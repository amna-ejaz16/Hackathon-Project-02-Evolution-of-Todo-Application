"""
Chat service for AI-powered task management assistant.

Handles conversation management, message persistence, and agent execution
using OpenAI Agents SDK with task management tools.

IMPORTANT: MCP filesystem operations are DISABLED to prevent:
- "Unable to add filesystem: <illegal path>" errors in serverless environments
- Filesystem sandbox security checks that reject null/invalid paths
- We use only @function_tool decorated tools (no MCP servers)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func
from agents import Agent, Runner, MessageOutputItem, ToolCallItem, ToolCallOutputItem
import logging
import json
import sys
import os
import re
from io import StringIO

from ..models.chat import Conversation, Message, ChatRequest, ChatResponse
from ..models.task import Task
from .task_tools import create_task_tools

logger = logging.getLogger(__name__)

# Suppress MCP filesystem warnings and errors globally
os.environ['MCP_DISABLE_FILESYSTEM'] = '1'
os.environ['MCP_NO_SERVER'] = '1'

# Suppress warnings from external libraries that might try to use MCP
import warnings
warnings.filterwarnings('ignore', message='.*Unable to add filesystem.*')

# Suppress other MCP-related warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='.*MCP.*')
warnings.filterwarnings('ignore', message='.*filesystem.*')

# Confirmation detection patterns for pending action handler
AFFIRMATIVE_PATTERNS = {
    "yes", "yeah", "yep", "yup",
    "ok", "okay", "alright", "sure", "sounds good",
    "confirm", "confirmed",
    "proceed", "go", "go ahead", "go for it",
    "delete it", "delete", "do it", "do that",
    "correct", "right", "let's do it"
}

NEGATIVE_PATTERNS = {
    "no", "nope", "nah",
    "cancel", "stop", "abort",
    "don't", "dont",
    "nevermind", "never mind",
    "not", "keep it", "leave it", "skip"
}


def is_confirmation(message: str) -> bool:
    """Check if message is an affirmative confirmation."""
    normalized = message.lower().strip().strip('.,!?')
    return normalized in AFFIRMATIVE_PATTERNS


def is_cancellation(message: str) -> bool:
    """Check if message is a negative cancellation."""
    normalized = message.lower().strip().strip('.,!?')
    return normalized in NEGATIVE_PATTERNS


class ChatService:
    """
    Service layer for AI chatbot functionality.

    Responsibilities:
    - Conversation lifecycle (get/create)
    - Message persistence with auto-pruning (200 message cap)
    - Context window management (last 20 messages for AI)
    - Agent execution with task tools
    - Response extraction and metadata capture
    """

    # Agent system instructions (FR-018: constrain to task management only)
    # Combined instructions for T024, T027, T031, T033
    AGENT_INSTRUCTIONS = """You are a task management assistant that helps users manage their todo tasks.

CAPABILITIES:
You can help users create, list, complete, uncomplete, update, and delete tasks.

TASK CREATION (T024):
When a user wants to create a task:
- Extract the title, description, priority (low/medium/high), category, and due date from their message
- If the title is unclear or missing, ask for clarification before proceeding
- Apply reasonable defaults: medium priority, no category, no due date
- Always confirm what you created with full details (title, priority, category, due date)
- Example: "I've created a new task 'Buy groceries' with high priority, due Friday. Is there anything else you'd like to do?"

LISTING TASKS (T027):
When a user asks to see tasks:
- Use the list_tasks tool with appropriate filters (status, priority, category)
- Format the response as a clear, numbered list showing:
  * Task status (complete/pending)
  * Priority level with emoji indicators
  * Task title
  * Due date if set
  * Category if set
- If no tasks match the filters, suggest creating one
- Examples of user queries: "show all tasks", "list pending high priority tasks", "what's due today"

COMPLETING/UNCOMPLETING TASKS (T031):
When a user wants to complete or uncomplete a task:
- First use list_tasks to find matching tasks by searching title keywords
- If exactly one match is found, proceed with the operation (complete_task or uncomplete_task)
- If multiple matches are found, list them with their IDs and ask the user to specify which one
- If no match is found, inform the user and offer to list all their tasks
- Example: "I found multiple tasks matching 'report': 1. Write monthly report, 2. Submit expense report. Which one would you like to complete?"

DELETING TASKS (T031 - Multi-turn confirmation):
Two-turn pattern for task deletion with context preservation:

TURN 1 - User says "delete [task description]":
- Use list_tasks tool to find matching tasks by searching for keywords from the user's message
- PRESERVE the task context: remember the task ID and title you found
- If exactly ONE task matches:
  * Show the task name and ID: "I found the task '[task title]' (ID: {id}). Are you sure you want to delete it?"
  * STOP - do NOT call delete_task on this turn
  * WAIT for user confirmation in their next message
  * IMPORTANT: Your confirmation message must always include the task ID in format "(ID: {number})"
- If MULTIPLE tasks match:
  * List all matching tasks with their IDs (numbered 1, 2, 3, etc.)
  * Ask which one to delete
  * WAIT for user to specify
- If NO tasks match:
  * Tell user no matching tasks found
  * Offer to show all tasks

TURN 2 - User responds with affirmative (e.g., "yes", "confirm", "ok"):
- CONTEXT PRESERVATION: Look at your IMMEDIATELY PREVIOUS message in the conversation history
- The task ID will be in format "(ID: {number})" from your confirmation message
- EXTRACT that task ID number using regex or string search
- VERIFY the task ID is a valid positive integer before calling delete_task
- CALL the delete_task tool with the extracted task_id as parameter
- CONFIRM deletion: "✓ Deleted task '[task title]' (ID: {id})"

If user responds with "no" or "cancel":
- CONTEXT PRESERVATION: Acknowledge the specific task from your previous message
- STOP (do NOT call delete_task)
- Respond: "No problem. I did not delete the task '[task title]' (ID: {id})."

CRITICAL RULES FOR CONTEXT PRESERVATION:
1. The task ID MUST be extracted from your previous confirmation message before calling delete_task
2. Never assume or guess the task ID - always extract it from the conversation history
3. Your confirmation message MUST include the task ID in format "(ID: {number})" so you can extract it later
4. If you cannot find the task ID in your previous message, ask the user to clarify which task they want to delete

UPDATING TASKS (T033):
When a user wants to update a task:
- First find the task using list_tasks by searching title keywords
- If found, call update_task with ONLY the fields that need changing (title, description, priority, category, due_date)
- Do not pass fields that should remain unchanged
- Confirm what was updated with the new values
- If multiple matches, ask user to specify which task
- Example: "I've updated 'Buy groceries' to high priority with due date Friday, Feb 14."

IMPORTANT CONSTRAINTS:
- You can ONLY perform task-related operations (create, list, complete, uncomplete, update, delete)
- You cannot access external data, browse the web, or perform non-task actions
- Always be helpful, concise, and conversational
- If you're unsure about what the user wants, ask clarifying questions
- Always reference tasks by their title and ID when confirming actions

Be friendly and natural while staying focused on task management."""

    @staticmethod
    def get_or_create_conversation(user_id: str, session: Session) -> Conversation:
        """
        Get the active conversation for a user, or create one if none exists.

        Per FR-026, each user has a single active conversation thread.

        Args:
            user_id: User ID from JWT token
            session: Database session

        Returns:
            Conversation object (existing or newly created)
        """
        # Check for existing conversation
        conversation = session.exec(
            select(Conversation).where(Conversation.user_id == user_id)
        ).first()

        if conversation:
            # Update the last activity timestamp
            conversation.updated_at = datetime.utcnow()
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            logger.info(f"Retrieved existing conversation {conversation.id} for user {user_id}")
            return conversation

        # Create new conversation
        conversation = Conversation(user_id=user_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        logger.info(f"Created new conversation {conversation.id} for user {user_id}")
        return conversation

    @staticmethod
    def get_context_messages(conversation_id: int, session: Session, limit: int = 20) -> List[Dict[str, str]]:
        """
        Fetch the last N messages from a conversation for AI context.

        Per FR-026, only the last 20 messages are used for agent context
        to maintain coherent multi-turn dialogue without overwhelming the model.

        Args:
            conversation_id: Conversation ID
            session: Database session
            limit: Maximum number of messages to retrieve (default: 20)

        Returns:
            List of message dicts with 'role' and 'content' keys, ordered chronologically
        """
        messages = session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        ).all()

        # Reverse to chronological order (oldest first)
        messages = list(reversed(messages))

        # Convert to agent-compatible format
        context = [{"role": msg.role, "content": msg.content} for msg in messages]

        logger.info(f"Retrieved {len(context)} context messages for conversation {conversation_id}")
        return context

    @staticmethod
    def handle_pending_action(
        user_message: str,
        conversation_id: int,
        user_id: str,
        session: Session
    ) -> Optional[ChatResponse]:
        """
        Handle pending action confirmation/cancellation - State Machine Pattern.

        Checks if the last assistant message has a pending_action and if the
        current user message is a confirmation or cancellation.

        State Machine Flow:
        1. Get last assistant message
        2. Check for pending_action in metadata
        3. Check user confirmation/cancellation
        4. Execute action or return cancellation message
        5. Return response or None to proceed to agent

        If confirmed: Executes the pending action directly and returns response
        If cancelled: Clears pending action and returns cancellation message
        If neither: Returns None (proceed to agent normally)

        Args:
            user_message: Current user input
            conversation_id: Conversation ID
            user_id: User ID from JWT
            session: Database session

        Returns:
            ChatResponse if pending action was handled, None otherwise
        """
        try:
            logger.warning(f"🔵 [PENDING ACTION STATE MACHINE] ENTERING handler for conversation_id={conversation_id}, user_id={user_id}")
            logger.warning(f"🔵 [PENDING ACTION STATE MACHINE] User message: '{user_message}'")

            # STEP 1: Get last assistant message with metadata
            logger.info(f"[PENDING ACTION STATE MACHINE] Step 1: Querying for last assistant message...")
            last_assistant_msg = session.exec(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .where(Message.role == "assistant")
                .order_by(Message.created_at.desc())
                .limit(1)
            ).first()

            logger.warning(f"🔵 [PENDING ACTION STATE MACHINE] Query result: last_assistant_msg={last_assistant_msg is not None}")

            if not last_assistant_msg:
                logger.warning(f"[PENDING ACTION STATE MACHINE] ⚠️ No last assistant message found, user_id={user_id}, conversation_id={conversation_id}")
                return None

            content_preview = last_assistant_msg.content[:100] if last_assistant_msg.content else "(empty)"
            logger.info(f"[PENDING ACTION STATE MACHINE] Retrieved last assistant message id={last_assistant_msg.id}, content_preview={content_preview}, has_metadata_json={bool(last_assistant_msg.metadata_json)}")

            # STEP 2: Extract metadata and check for pending action
            metadata = last_assistant_msg.get_metadata()
            if not metadata:
                logger.warning(f"[PENDING ACTION STATE MACHINE] ❌ No metadata on last assistant message (metadata_json={last_assistant_msg.metadata_json}), user_id={user_id}, conversation_id={conversation_id}")
                return None

            logger.info(f"[PENDING ACTION STATE MACHINE] Metadata retrieved: keys={list(metadata.keys())}, user_id={user_id}")

            if "pending_action" not in metadata:
                logger.warning(f"⚠️ [PENDING ACTION STATE MACHINE] NO PENDING_ACTION in metadata, trying FALLBACK extraction...")

                # FALLBACK: Extract task ID directly from the assistant message
                # If metadata wasn't stored, try to find ID in the message itself
                fallback_id_patterns = [
                    r'\(ID:\s*(\d+)\)',                  # (ID: 42)
                    r'ID[:\s]+(\d+)',                     # ID: 42
                    r'task\s+#?(\d+)',                    # task 42
                ]

                fallback_id = None
                for pattern in fallback_id_patterns:
                    match = re.search(pattern, last_assistant_msg.content, re.IGNORECASE)
                    if match:
                        fallback_id = int(match.group(1))
                        logger.warning(f"✅ [PENDING ACTION STATE MACHINE] FALLBACK SUCCESS: Extracted task_id={fallback_id} from message")
                        break

                if not fallback_id:
                    logger.error(f"🔴 [PENDING ACTION STATE MACHINE] CRITICAL: NO PENDING_ACTION in metadata AND no ID in message!")
                    logger.error(f"    Message content: '{last_assistant_msg.content[:200]}'")
                    return None

                # Create a minimal pending_action from extracted ID
                pending = {
                    "type": "delete_task",
                    "task_id": fallback_id,
                    "task_title": "task",
                    "awaiting_confirmation": True
                }
                logger.warning(f"✅ [PENDING ACTION STATE MACHINE] Using FALLBACK pending_action: {pending}")
            else:
                pending = metadata.get("pending_action")

            logger.warning(f"✅ [PENDING ACTION STATE MACHINE] FOUND pending_action in metadata!")

            pending = metadata.get("pending_action")
            if not pending or not isinstance(pending, dict):
                logger.warning(f"[PENDING ACTION STATE MACHINE] Invalid pending action structure: type={type(pending).__name__}, user_id={user_id}")
                return None

            logger.info(f"[PENDING ACTION STATE MACHINE] Found pending action in metadata: {pending}, user_id={user_id}")

            # Validate pending action has required fields
            pending_type = pending.get("type")
            pending_task_id = pending.get("task_id")
            pending_task_title = pending.get("task_title", f"task {pending_task_id}")

            if pending_type != "delete_task":
                logger.warning(f"[PENDING ACTION STATE MACHINE] Unknown pending action type: {pending_type}, user_id={user_id}")
                return None

            # STEP 3: Check user confirmation or cancellation
            logger.warning(f"🔵 [PENDING ACTION STATE MACHINE] Step 3: Checking user confirmation. Message: '{user_message}'")

            # Debug: Check confirmation function
            is_confirm = is_confirmation(user_message)
            is_cancel = is_cancellation(user_message)
            logger.warning(f"🔵 [PENDING ACTION STATE MACHINE] Confirmation check:")
            logger.warning(f"     is_confirmation('{user_message}')={is_confirm}")
            logger.warning(f"     is_cancellation('{user_message}')={is_cancel}")
            logger.warning(f"     AFFIRMATIVE_PATTERNS={AFFIRMATIVE_PATTERNS}")
            logger.warning(f"     Normalized message='{user_message.lower().strip().strip('.,!?')}'")

            if not is_confirm and not is_cancel:
                logger.warning(f"🔴 [PENDING ACTION STATE MACHINE] Message not recognized as confirmation or cancellation")
                return None

            # Check for confirmation
            if is_confirm:
                logger.info(f"[PENDING ACTION STATE MACHINE] ✅ USER CONFIRMED {pending_type} for task_id={pending_task_id}, title='{pending_task_title}', user_id={user_id}")

                # Execute pending action (only delete_task supported)
                if pending_type == "delete_task":
                    # Validate task_id comprehensively
                    if not isinstance(pending_task_id, int):
                        logger.error(f"[PENDING ACTION] Invalid task_id type: {type(pending_task_id).__name__} (expected int)")
                        return ChatResponse(
                            response="Error: Invalid task ID format. Please try again.",
                            conversation_id=conversation_id,
                            action="conversation",
                            task_id=None
                        )

                    if pending_task_id <= 0:
                        logger.error(f"[PENDING ACTION] Invalid task_id value: {pending_task_id} (expected > 0)")
                        return ChatResponse(
                            response="Error: Invalid task ID value. Please try again.",
                            conversation_id=conversation_id,
                            action="conversation",
                            task_id=None
                        )

                    # Import here to avoid circular dependency
                    tools_list = create_task_tools(user_id=user_id, session=session)

                    # Find delete_task tool
                    delete_tool = next((t for t in tools_list if t.__name__ == "delete_task"), None)

                    if not delete_tool:
                        logger.error(f"[PENDING ACTION] delete_task tool not found")
                        return ChatResponse(
                            response="Error: Task deletion tool unavailable. Please try again.",
                            conversation_id=conversation_id,
                            action="conversation",
                            task_id=None
                        )

                    try:
                        # Execute deletion
                        result = delete_tool(task_id=pending_task_id)
                        logger.info(f"[PENDING ACTION] Delete tool result: {result}")

                        # Safely check if deletion was successful
                        result_str = str(result) if result else ""
                        is_success = "Deleted task" in result_str

                        if is_success:
                            # Store assistant confirmation response with success metadata
                            task_title = pending.get("task_title", f"task {pending_task_id}")
                            assistant_response = f"✓ {result_str}"
                            ChatService.store_message(
                                conversation_id=conversation_id,
                                role="assistant",
                                content=assistant_response,
                                metadata={
                                    "tool_calls": [{"name": "delete_task", "arguments": {"task_id": pending_task_id}}],
                                    "action": "task_deleted",
                                    "task_id": pending_task_id
                                },
                                session=session
                            )
                            logger.info(f"[PENDING ACTION] Successfully deleted task_id={pending_task_id}, title='{task_title}'")

                            return ChatResponse(
                                response=assistant_response,
                                conversation_id=conversation_id,
                                action="task_deleted",
                                task_id=pending_task_id
                            )
                        else:
                            # Deletion failed - store error response without task_deleted action
                            assistant_response = f"❌ {result_str}" if result_str else "❌ Could not delete task. Please try again."
                            ChatService.store_message(
                                conversation_id=conversation_id,
                                role="assistant",
                                content=assistant_response,
                                metadata={
                                    "error": result_str,
                                    "action": "conversation"
                                },
                                session=session
                            )
                            logger.warning(f"[PENDING ACTION] Failed to delete task_id={pending_task_id}: {result_str}")

                            return ChatResponse(
                                response=assistant_response,
                                conversation_id=conversation_id,
                                action="conversation",
                                task_id=None
                            )
                    except Exception as e:
                        logger.error(f"[PENDING ACTION] Exception during delete execution: {type(e).__name__}: {e}", exc_info=True)
                        error_msg = f"Error deleting task: {str(e)[:100]}"
                        ChatService.store_message(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=error_msg,
                            metadata={
                                "error": str(e),
                                "action": "conversation"
                            },
                            session=session
                        )
                        return ChatResponse(
                            response=error_msg,
                            conversation_id=conversation_id,
                            action="conversation",
                            task_id=None
                        )

            # Check for cancellation
            elif is_cancel:
                logger.info(f"[PENDING ACTION] ✅ USER CANCELLED {pending_type} for task_id={pending_task_id}")

                # NOTE: User message already stored in process_message() at step 2, don't store twice

                # Store assistant acknowledgment response
                task_title = pending.get("task_title", "this task")
                assistant_response = f"No problem. I did not delete the task '{task_title}'."
                ChatService.store_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_response,
                    metadata={"action": "conversation"},
                    session=session
                )

                return ChatResponse(
                    response=assistant_response,
                    conversation_id=conversation_id,
                    action="conversation",
                    task_id=None
                )

            # Not a confirmation or cancellation - proceed to agent
            logger.warning(f"🔴 [PENDING ACTION STATE MACHINE] Returning None (not a confirmation/cancellation)")
            return None

        except Exception as e:
            # Fail gracefully if pending action handling has unexpected errors
            logger.error(f"🔴 [PENDING ACTION] Unexpected error in handle_pending_action: {type(e).__name__}: {e}", exc_info=True)
            logger.error(f"🔴 [PENDING ACTION] Stack trace: {e}")
            # Don't return a response - let it proceed to agent
            return None

    @staticmethod
    def store_message(
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]],
        session: Session
    ) -> Message:
        """
        Store a message in the database and enforce the 200-message cap.

        Per FR-027, conversations are capped at 200 messages with automatic pruning
        of oldest messages when the limit is exceeded.

        Args:
            conversation_id: Conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata dict (tool calls, action type, reasoning)
            session: Database session

        Returns:
            Created Message object
        """
        # Create and store message
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )

        # Set metadata using the method (handles JSON serialization)
        if metadata:
            message.set_metadata(metadata)
            logger.debug(f"[MESSAGE STORAGE] Set metadata on message: keys={list(metadata.keys())}")
            if "pending_action" in metadata:
                logger.info(f"[MESSAGE STORAGE] 🔴 PENDING_ACTION STORED: {metadata['pending_action']}")

        session.add(message)
        session.commit()
        session.refresh(message)

        # CRITICAL: Verify metadata was actually persisted to database
        stored_metadata = message.get_metadata()
        if metadata and stored_metadata is None:
            logger.error(f"[MESSAGE STORAGE] ❌ CRITICAL: Metadata was lost during storage! Expected: {list(metadata.keys())}")
        elif metadata and "pending_action" in metadata:
            if "pending_action" not in stored_metadata:
                logger.error(f"[MESSAGE STORAGE] ❌ CRITICAL: pending_action lost during serialization!")
            else:
                logger.info(f"[MESSAGE STORAGE] ✅ pending_action verified in database: {stored_metadata['pending_action']}")

        logger.info(f"Stored {role} message {message.id} in conversation {conversation_id}")

        # Enforce 200-message cap (FR-027)
        message_count = session.exec(
            select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        ).one()

        if message_count > 200:
            # Calculate how many messages to delete
            delete_count = message_count - 200

            # Get IDs of oldest messages to delete
            old_messages = session.exec(
                select(Message.id)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .limit(delete_count)
            ).all()

            # Delete old messages
            for msg_id in old_messages:
                old_message = session.get(Message, msg_id)
                if old_message:
                    session.delete(old_message)

            session.commit()
            logger.info(f"Pruned {delete_count} old messages from conversation {conversation_id} (cap: 200)")

        return message

    @staticmethod
    async def process_message(
        user_message: str,
        user_id: str,
        session: Session
    ) -> ChatResponse:
        """
        Process a user message through the AI agent and return a response.

        This is the main orchestration method that handles the full flow:
        1. Get or create conversation
        2. Store user message
        3. Fetch conversation context (last 20 messages)
        4. Create agent with task tools
        5. Run agent with context
        6. Extract response and metadata
        7. Store assistant message
        8. Return ChatResponse

        Args:
            user_message: User's input message
            user_id: User ID from JWT token
            session: Database session

        Returns:
            ChatResponse with assistant's reply and metadata

        Raises:
            Exception: If agent execution fails or OpenAI API errors occur
        """
        try:
            logger.info(f"[CONVERSATION LIFECYCLE] Processing message for user_id={user_id}, message_length={len(user_message)}")

            # Step 1: Get or create conversation
            conversation = ChatService.get_or_create_conversation(user_id, session)
            conversation_id = conversation.id
            logger.info(f"[CONVERSATION LIFECYCLE] Using conversation_id={conversation_id} for user_id={user_id}")

            # Step 2: Store user message
            user_msg = ChatService.store_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                metadata=None,
                session=session
            )
            logger.info(f"[MESSAGE STORAGE] Stored user message message_id={user_msg.id}, conversation_id={conversation_id}, content_length={len(user_message)}")

            # Step 2.5: Check for pending action confirmation (CRITICAL)
            # This must happen BEFORE agent initialization to avoid MCP errors blocking pending actions
            logger.info(f"[EXECUTION FLOW] Checking for pending action at step 2.5")
            pending_response = ChatService.handle_pending_action(
                user_message=user_message,
                conversation_id=conversation_id,
                user_id=user_id,
                session=session
            )

            if pending_response:
                logger.warning(f"✅ [PENDING ACTION] SUCCESS! Handled pending action, SKIPPING agent execution")
                logger.warning(f"✅ [PENDING ACTION] Returning: {pending_response.action}")
                return pending_response

            logger.warning(f"🔴 [EXECUTION FLOW] handle_pending_action returned None, proceeding to AGENT EXECUTION")

            # Step 3: Fetch context (last 20 messages for AI)
            context_messages = ChatService.get_context_messages(conversation_id, session, limit=20)
            logger.info(f"[CONVERSATION LIFECYCLE] Fetched {len(context_messages)} context messages for conversation_id={conversation_id}, user_id={user_id}")

            # Step 4: Create task tools bound to this user
            # These tools are created BEFORE agent initialization so they're available for both
            # agent execution AND backup pending action handling
            tools = create_task_tools(user_id=user_id, session=session)
            logger.info(f"[AGENT EXECUTION] Created {len(tools)} task tools for user_id={user_id}")

            # Log available tools for debugging
            tool_names = [getattr(t, '__name__', str(t)) for t in tools]
            logger.debug(f"[AGENT EXECUTION] Available tools: {tool_names}")

            # Step 5-6: Create agent and runner INSIDE try/except to catch MCP initialization errors
            # MCP filesystem errors occur during Agent() construction, not during Runner.run()
            # We must catch these errors here, not later during execution

            agent = None
            runner = None
            result = None
            old_stderr = sys.stderr
            old_stdout = sys.stdout

            try:
                # Suppress all stderr/stdout during agent creation
                # This is safe because MCP warnings are not actionable in serverless environment
                # MCP tries to initialize filesystem even with mcp_servers=[] so we capture those errors
                sys.stderr = StringIO()
                sys.stdout = StringIO()

                logger.info(f"[AGENT EXECUTION] Creating agent with {len(tools)} tools for user_id={user_id}")

                # Step 5: Create agent with tools and instructions
                # CRITICAL: mcp_servers=[] prevents MCP server initialization
                # Note: Agent() may still try to validate filesystem, which we suppress above
                try:
                    agent = Agent(
                        name="TaskManagerAssistant",
                        instructions=ChatService.AGENT_INSTRUCTIONS,
                        tools=tools,
                        model="gpt-4o-mini",  # Use mini for cost efficiency and faster responses
                        mcp_servers=[],  # CRITICAL: Empty list - no MCP servers
                    )
                    logger.info(f"[AGENT EXECUTION] ✅ Agent created successfully. Tools: {len(tools)}")

                except Exception as agent_init_error:
                    # Catch agent initialization errors even with stderr/stdout suppression
                    error_str = str(agent_init_error).lower()
                    error_type = type(agent_init_error).__name__

                    # Check for MCP-related errors
                    is_mcp_error = any(keyword in error_str for keyword in ["filesystem", "illegal path", "mcp", "add filesystem", "path"])

                    if is_mcp_error:
                        logger.warning(f"[AGENT EXECUTION] ⚠️ MCP filesystem error (suppressed): {error_type}: {agent_init_error}")
                        logger.info(f"[AGENT EXECUTION] ℹ️ This is expected in serverless environments. Continuing with agent execution.")
                        agent = None  # Mark as failed but continue
                    else:
                        logger.error(f"[AGENT EXECUTION] ❌ Non-MCP agent initialization error: {error_type}: {agent_init_error}")
                        raise

                # Step 6: Create runner for agent execution
                runner = Runner()
                logger.info(f"[AGENT EXECUTION] Runner initialized successfully")

                # Restore stderr/stdout after successful initialization
                sys.stderr = old_stderr
                sys.stdout = old_stdout

            except (ValueError, OSError, RuntimeError) as e:
                # Catch MCP initialization errors (filesystem, paths, etc.)
                error_str = str(e).lower()

                # Log MCP-related errors as warnings (they're expected in serverless)
                if any(keyword in error_str for keyword in ["filesystem", "illegal path", "mcp", "add filesystem"]):
                    logger.warning(f"[AGENT EXECUTION] MCP initialization error (expected in serverless): {type(e).__name__}: {e}")
                    # Restore stderr/stdout
                    sys.stderr = old_stderr
                    sys.stdout = old_stdout

                    error_response = "I'm having trouble connecting to the task management system. Please try again in a moment."
                    ChatService.store_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=error_response,
                        metadata={"error": "mcp_initialization", "type": str(type(e).__name__)},
                        session=session
                    )

                    logger.info(f"[AGENT EXECUTION] Returning graceful error response to user after MCP failure")
                    return ChatResponse(
                        response=error_response,
                        conversation_id=conversation_id,
                        action="conversation",
                        task_id=None
                    )
                else:
                    # Other errors should be logged and re-raised
                    logger.error(f"[AGENT EXECUTION] Agent initialization error: {type(e).__name__}: {e}", exc_info=True)
                    sys.stderr = old_stderr
                    sys.stdout = old_stdout
                    raise
            except Exception as e:
                # Catch any other unexpected errors during initialization
                logger.error(f"[AGENT EXECUTION] Unexpected error during agent initialization: {type(e).__name__}: {e}", exc_info=True)
                sys.stderr = old_stderr
                sys.stdout = old_stdout
                raise
            finally:
                # ALWAYS restore stdout and stderr at the end of initialization block
                sys.stderr = old_stderr
                sys.stdout = old_stdout

            # Validate agent was successfully initialized before proceeding
            if agent is None or runner is None:
                logger.error(f"[AGENT EXECUTION] Agent initialization failed (agent=None or runner=None)")
                error_response = "I'm having trouble initializing the task assistant. Please try again in a moment."
                ChatService.store_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=error_response,
                    metadata={"error": "agent_initialization_failed"},
                    session=session
                )
                return ChatResponse(
                    response=error_response,
                    conversation_id=conversation_id,
                    action="conversation",
                    task_id=None
                )

            # At this point, agent and runner are successfully initialized
            # Now run the agent with error handling for execution phase
            try:
                logger.info(f"[AGENT EXECUTION] Running agent. Current message: {user_message[:100]}...")

                # Build full conversation context for reference (not directly passed to agent)
                # Note: OpenAI Agents SDK runner.run() does NOT accept messages parameter
                # Context is available through tools and agent instructions
                full_context = context_messages + [{"role": "user", "content": user_message}]
                logger.info(f"[AGENT EXECUTION] Available context: {len(full_context)} messages in conversation history")

                # Execute agent with task tools
                # Agent follows instructions which guide behavior for deletion confirmations
                # Deletion is handled by:
                # 1. handle_pending_action() intercepts on turn 2 (preferred, fast path)
                # 2. Agent instructions guide multi-turn deletion if needed (fallback)
                result = await runner.run(
                    starting_agent=agent,
                    input=user_message,
                )
                logger.info(f"[AGENT EXECUTION] Agent completed successfully")

            except Exception as e:
                logger.error(f"[AGENT EXECUTION] Agent execution error: {type(e).__name__}: {e}", exc_info=True)
                raise
            finally:
                # ALWAYS restore stdout and stderr
                sys.stderr = old_stderr
                sys.stdout = old_stdout

            logger.info(f"[AGENT EXECUTION] Agent execution completed, user_id={user_id}, conversation_id={conversation_id}")

            # Step 7: Extract response and metadata
            # The OpenAI Agents SDK Runner.run() returns a RunResult object with new_items containing MessageOutputItem objects
            # Each MessageOutputItem has raw_item (ResponseOutputMessage) with content field
            assistant_response = "I'm sorry, I couldn't process that request."

            try:
                if result and hasattr(result, 'new_items') and result.new_items:
                    # Get the last assistant message from new_items
                    for item in reversed(result.new_items):
                        if isinstance(item, MessageOutputItem):
                            # Extract content from ResponseOutputMessage
                            if hasattr(item.raw_item, 'content') and item.raw_item.content:
                                # item.raw_item.content is a list of content blocks
                                # Extract text from ResponseOutputText blocks
                                text_parts = []
                                for content_block in item.raw_item.content:
                                    if hasattr(content_block, 'text'):
                                        text_str = str(content_block.text) if content_block.text else ""
                                        if text_str:
                                            text_parts.append(text_str)
                                if text_parts:
                                    assistant_response = "\n".join(text_parts)
                                    logger.info(f"[AGENT EXECUTION] Extracted assistant response from new_items, length={len(assistant_response)}, user_id={user_id}")
                                    break
                elif isinstance(result, dict):
                    # Fallback for dict-like response
                    assistant_response = result.get("response", assistant_response)
                    logger.warning(f"[AGENT EXECUTION] Agent result was dict-like (unexpected format), user_id={user_id}")
                else:
                    logger.warning(f"[AGENT EXECUTION] Could not extract assistant response from result, user_id={user_id}, result_type={type(result)}, has_new_items={hasattr(result, 'new_items')}")
            except Exception as e:
                logger.error(f"[AGENT EXECUTION] Error extracting assistant response: {type(e).__name__}: {e}", exc_info=True)
                assistant_response = "I'm sorry, I encountered an error processing your request. Please try again."

            # NEW: Detect if agent is asking for delete confirmation
            # Enhanced detection patterns for various confirmation phrases - MUCH more flexible
            pending_action = None
            delete_confirmation_patterns = [
                r"are\s+you\s+sure.*delete",           # "are you sure ... delete"
                r"do\s+you.*(?:want|like).*delete",    # "do you want to delete" / "do you like me to delete"
                r"should\s+[iw]e.*delete",             # "should i/we delete"
                r"confirm.*delete",                    # "confirm delete"
                r"delete.*(?:confirm|ok|okay)",        # "delete and confirm"
                r"want\s+(?:to\s+)?delete",           # "want to delete" or "want delete"
                r"(?:go\s+ahead|proceed).*delete",     # "go ahead/proceed with delete"
                r"(?:really|actually)\s+delete",       # "really delete"
                r"(?:shall|may)\s+[iw]e.*delete",      # "shall we delete" / "may I delete"
                r"(?:alright|ok|okay).*delete",        # "ok to delete"
            ]

            # Check if response contains any delete confirmation pattern
            # Use DOTALL flag to make . match newlines (important for multi-line responses)
            has_delete_phrase = any(re.search(pattern, assistant_response, re.IGNORECASE | re.DOTALL)
                                   for pattern in delete_confirmation_patterns)

            # FALLBACK: If no pattern matched, check for structural markers
            # If message has (ID: number) and contains "delete" and ends with ? or !
            if not has_delete_phrase:
                has_id = re.search(r'\(ID:\s*\d+\)', assistant_response)
                has_delete_word = re.search(r'\bdelete\b', assistant_response, re.IGNORECASE)
                has_question = assistant_response.rstrip().endswith(('?', '!'))
                has_delete_phrase = bool(has_id and has_delete_word and has_question)
                if has_delete_phrase:
                    logger.info(f"[PENDING ACTION DETECTION] Using fallback pattern (ID + delete + ?/!)")

            logger.info(f"[PENDING ACTION DETECTION] Response length: {len(assistant_response)}")
            logger.info(f"[PENDING ACTION DETECTION] Response preview: '{assistant_response[:150]}...'")
            logger.info(f"[PENDING ACTION DETECTION] Delete phrase detected: {has_delete_phrase}")

            # DEBUG: Show which patterns were checked
            if not has_delete_phrase:
                for i, pattern in enumerate(delete_confirmation_patterns):
                    match = re.search(pattern, assistant_response, re.IGNORECASE | re.DOTALL)
                    logger.debug(f"[PENDING ACTION DETECTION] Pattern {i}: {pattern[:50]}... → {bool(match)}")

            if has_delete_phrase:
                # Extract task ID from confirmation message - try multiple patterns with improved coverage
                id_patterns = [
                    r'\(ID:\s*(\d+)\)',                  # (ID: 42) or (ID:42)
                    r'(?:ID|id)[:\s]+(\d+)(?:[\s.!?)]|$)',  # ID: 42 or ID 42 (with proper boundary)
                    r'task\s+(?:ID\s+)?#?(\d+)',         # task ID 42 or task #42
                    r'(?:task|Task)\s+[^(]*#(\d+)',      # task xyz #42
                    r'\[(?:task|id|ID):\s*(\d+)\]',      # [task: 42]
                    r'(?:^|\s)#(\d+)(?:\s|$)',           # standalone #42
                    r'task\s+(?:with\s+)?id\s+(\d+)',    # task with id 42
                ]

                match = None
                for pattern in id_patterns:
                    match = re.search(pattern, assistant_response, re.IGNORECASE)
                    if match:
                        logger.info(f"[PENDING ACTION] Task ID matched with pattern: {pattern}")
                        break

                if match:
                    task_id_str = match.group(1)
                    logger.info(f"[PENDING ACTION] Extracted task_id_str: {task_id_str}")

                    # Try to find task title in message - much more flexible matching
                    # Handles both ASCII and Unicode quotes flexibly
                    title_patterns = [
                        r"['\"]([^'\"]+)['\"]",                       # 'task title' or "task title"
                        r'(?:called|named|titled|is)\s+([^()\n]+?)(?:\s*\(|$)',  # called/named/titled/is [title] (
                        r'task\s+(?:(?:called|named)\s+)?([^()\n]+?)(?:\s*(?:with|ID|\(|#)|$)',  # task [title] with/ID/(/#
                        r'found\s+(?:the\s+)?(?:task|item)\s+(?:called|named)?\s*([^()\n]+?)(?:\s*\(|$)',  # found task [title] (
                        r'(?:the|your)\s+task\s+["\']?([^()\n"\']+)["\']?(?:\s*\(|$)',  # the task "title" or the task title (
                    ]

                    task_title = "this task"
                    for title_pattern in title_patterns:
                        title_match = re.search(title_pattern, assistant_response, re.IGNORECASE)
                        if title_match:
                            candidate_title = title_match.group(1).strip().strip('.,!?')
                            # Only accept if it's a reasonable length and doesn't contain too many special delimiters
                            if candidate_title and 2 <= len(candidate_title) <= 100 and candidate_title != "Delete":
                                task_title = candidate_title
                                logger.info(f"[PENDING ACTION] Task title matched: '{task_title}'")
                                break

                    try:
                        task_id_int = int(task_id_str)
                        if task_id_int <= 0:
                            raise ValueError(f"Invalid task_id: {task_id_int} (must be > 0)")
                        pending_action = {
                            "type": "delete_task",
                            "task_id": task_id_int,
                            "task_title": task_title,
                            "awaiting_confirmation": True,
                            "created_at": datetime.utcnow().isoformat()
                        }
                        logger.info(f"[PENDING ACTION] ✅ Detected deletion confirmation request: task_id={task_id_int}, title='{task_title}'")
                    except (ValueError, TypeError) as e:
                        logger.error(f"[PENDING ACTION] ⚠️ Failed to parse task_id '{task_id_str}': {e}")
                        pending_action = None
                else:
                    logger.warning(f"[PENDING ACTION] ⚠️ Delete phrase detected but no task ID found in response. This will require user to clarify.")

            # T025: Parse tool calls from agent result to determine action type
            action = "conversation"  # Default action
            task_id = None
            tool_calls_metadata = []

            # Extract tool calls from result new_items
            if result and hasattr(result, 'new_items') and result.new_items:
                for item in result.new_items:
                    try:
                        # Handle ToolCallItem (the tool call itself)
                        # Production-safe extraction for OpenAI Responses API ResponseFunctionToolCall
                        if isinstance(item, ToolCallItem):
                            tool_name = ""
                            tool_args_str = ""

                            # NEW API: ResponseFunctionToolCall has .name and .arguments as direct attributes
                            # Defensive extraction to handle both old and new API formats
                            if hasattr(item.raw_item, 'name'):
                                # New Responses API: Direct attribute access
                                tool_name = getattr(item.raw_item, 'name', '')
                                tool_args_str = getattr(item.raw_item, 'arguments', '')
                            elif hasattr(item.raw_item, 'function') and hasattr(item.raw_item.function, 'name'):
                                # Old ChatCompletion API: Nested structure (fallback, may be removed later)
                                tool_name = item.raw_item.function.name
                                tool_args_str = item.raw_item.function.arguments
                            else:
                                # Unknown format: log and skip
                                logger.warning(
                                    f"[TOOL CALL TRACKING] Unknown tool call format for item type {type(item.raw_item).__name__}, "
                                    f"user_id={user_id}, conversation_id={conversation_id}"
                                )
                                continue

                            # Safely convert to string if needed
                            tool_name = str(tool_name) if tool_name else ""
                            tool_args_str = str(tool_args_str) if tool_args_str else ""

                            # Parse arguments to extract task_id if present
                            tool_args = {}
                            try:
                                tool_args = json.loads(tool_args_str) if tool_args_str else {}
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.warning(f"[TOOL CALL TRACKING] Failed to parse tool arguments for tool={tool_name}, user_id={user_id}, error={type(e).__name__}")

                            # Log tool call details
                            logger.info(f"[TOOL CALL TRACKING] AI tool call: tool={tool_name}, arguments={tool_args}, user_id={user_id}, conversation_id={conversation_id}")

                            # Store tool call for metadata
                            tool_calls_metadata.append({
                                "name": tool_name,
                                "arguments": tool_args
                            })

                            # T025: Map tool calls to action types based on contract/chat-api.yaml
                            # Priority given to task modification actions over list operations
                            if tool_name == "add_task" and action == "conversation":
                                action = "task_created"
                                logger.info(f"[ACTION DETECTION] Detected action=task_created, title={tool_args.get('title')}, priority={tool_args.get('priority')}, user_id={user_id}")
                                # Extract task_id from the returned task object if available
                                # Note: The tool returns a string, but we'd need to parse it
                                # For now, we'll rely on the frontend refetching the task list
                            elif tool_name == "update_task" and action not in ["task_created", "task_deleted"]:
                                action = "task_updated"
                                task_id = tool_args.get("task_id")
                                logger.info(f"[ACTION DETECTION] Detected action=task_updated, task_id={task_id}, fields={list(tool_args.keys())}, user_id={user_id}")
                            elif tool_name == "complete_task" and action not in ["task_created", "task_updated", "task_deleted"]:
                                action = "task_completed"
                                task_id = tool_args.get("task_id")
                                logger.info(f"[ACTION DETECTION] Detected action=task_completed, task_id={task_id}, user_id={user_id}")
                            elif tool_name == "uncomplete_task" and action not in ["task_created", "task_updated", "task_deleted"]:
                                action = "task_uncompleted"
                                task_id = tool_args.get("task_id")
                                logger.info(f"[ACTION DETECTION] Detected action=task_uncompleted, task_id={task_id}, user_id={user_id}")
                            elif tool_name == "delete_task" and action not in ["task_created", "task_updated"]:
                                action = "task_deleted"
                                task_id = tool_args.get("task_id")
                                logger.info(f"[ACTION DETECTION] Detected action=task_deleted, task_id={task_id}, user_id={user_id}")
                            elif tool_name == "list_tasks" and action == "conversation":
                                action = "tasks_listed"
                                filters = {k: v for k, v in tool_args.items() if v is not None}
                                logger.info(f"[ACTION DETECTION] Detected action=tasks_listed, filters={filters}, user_id={user_id}")
                    except Exception as e:
                        logger.error(f"[TOOL CALL TRACKING] Error processing tool call item: {type(e).__name__}: {e}", exc_info=True)
                        continue

            # Log summary of action detection
            if tool_calls_metadata:
                logger.info(f"[ACTION DETECTION] Final action determination: action={action}, task_id={task_id}, tools_executed={len(tool_calls_metadata)}, user_id={user_id}, conversation_id={conversation_id}")
            else:
                logger.info(f"[ACTION DETECTION] No tool calls detected, action={action}, user_id={user_id}, conversation_id={conversation_id}")

            # Build metadata for storage
            metadata = {
                "tool_calls": tool_calls_metadata,
                "action": action,
            }

            if task_id:
                metadata["task_id"] = task_id

            # NEW: Add pending action if detected
            if pending_action:
                logger.info(f"[PENDING ACTION STORAGE] ✅ Adding pending_action to metadata: {pending_action}")
                metadata["pending_action"] = pending_action
            else:
                logger.info(f"[PENDING ACTION STORAGE] ⚠️ No pending_action to store (pending_action is None)")

            logger.info(f"[METADATA] Final metadata to store: {list(metadata.keys())} - pending_action={'pending_action' in metadata}")

            # Step 8: Store assistant message
            assistant_msg = ChatService.store_message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response,
                metadata=metadata,
                session=session
            )
            logger.info(f"[MESSAGE STORAGE] Stored assistant message message_id={assistant_msg.id}, conversation_id={conversation_id}, content_length={len(assistant_response)}, action={action}, task_id={task_id}")

            # Step 9: Return response
            logger.info(f"[CONVERSATION LIFECYCLE] Completed message processing for user_id={user_id}, conversation_id={conversation_id}, action={action}, task_id={task_id}")
            return ChatResponse(
                response=assistant_response,
                conversation_id=conversation_id,
                action=action,
                task_id=task_id
            )

        except Exception as e:
            # Log error with full stack trace
            error_type = type(e).__name__
            error_message = str(e)
            conversation_id_safe = conversation.id if 'conversation' in locals() else 0

            logger.error(
                f"[ERROR] Exception during message processing: user_id={user_id}, "
                f"conversation_id={conversation_id_safe}, "
                f"error_type={error_type}, error_message={error_message[:200]}",
                exc_info=True
            )

            # Prepare error response
            user_facing_message = "I'm sorry, I encountered an error processing your request. Please try again."

            error_response = ChatResponse(
                response=user_facing_message,
                conversation_id=conversation_id_safe,
                action=None,
                task_id=None
            )

            # Try to store error message if conversation exists
            if 'conversation' in locals() and conversation and conversation.id:
                try:
                    error_metadata = {
                        "error": error_message[:500],  # Limit error message length
                        "error_type": error_type
                    }

                    error_msg = ChatService.store_message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=user_facing_message,
                        metadata=error_metadata,
                        session=session
                    )
                    logger.info(f"[MESSAGE STORAGE] Stored error message message_id={error_msg.id}, conversation_id={conversation.id}, user_id={user_id}")
                except Exception as store_error:
                    logger.error(f"[ERROR] Failed to store error message: user_id={user_id}, conversation_id={conversation.id}, error={type(store_error).__name__}: {str(store_error)[:100]}", exc_info=True)

            # Always raise to maintain error handling contract
            raise
