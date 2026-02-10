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

# Confirmation detection patterns for pending action handler
AFFIRMATIVE_PATTERNS = {
    "yes", "confirm", "ok", "sure", "yeah", "yep",
    "proceed", "delete it", "go ahead", "do it"
}

NEGATIVE_PATTERNS = {
    "no", "cancel", "stop", "don't", "nope",
    "nevermind", "never mind", "abort"
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
Two-turn pattern for task deletion:

TURN 1 - User says "delete [task description]":
- Use list_tasks tool to find matching tasks by searching for keywords from the user's message
- If exactly ONE task matches:
  * Show the task name and ID: "I found the task '[task title]' (ID: {id}). Are you sure you want to delete it?"
  * STOP - do NOT call delete_task on this turn
  * WAIT for user confirmation in their next message
- If MULTIPLE tasks match:
  * List all matching tasks with their IDs (numbered 1, 2, 3, etc.)
  * Ask which one to delete
  * WAIT for user to specify
- If NO tasks match:
  * Tell user no matching tasks found
  * Offer to show all tasks

TURN 2 - User responds with affirmative (e.g., "yes", "confirm", "ok"):
- LOOK at your previous message in the conversation history to find the task ID
- The task ID will be in format "(ID: {number})" from your confirmation message
- EXTRACT that task ID number
- CALL the delete_task tool with the extracted task_id as parameter
- Report result: "✓ Deleted task '[task title]' (ID: {id})"

If user responds with "no" or "cancel":
- STOP (do NOT call delete_task)
- Respond: "No problem. I did not delete the task."

CRITICAL: The task ID MUST be extracted from your previous confirmation message before calling delete_task

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
        Handle pending action confirmation/cancellation.

        Checks if the last assistant message has a pending_action and if the
        current user message is a confirmation or cancellation.

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
        # Get last assistant message with metadata
        last_assistant_msg = session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .limit(1)
        ).first()

        if not last_assistant_msg:
            return None

        metadata = last_assistant_msg.get_metadata()
        if not metadata or "pending_action" not in metadata:
            return None

        pending = metadata["pending_action"]

        # Check for confirmation
        if is_confirmation(user_message):
            logger.info(f"[PENDING ACTION] User confirmed {pending['type']} for task_id={pending['task_id']}")

            # Execute pending action
            if pending["type"] == "delete_task":
                # Import here to avoid circular dependency
                tools_list = create_task_tools(user_id=user_id, session=session)

                # Find delete_task tool
                delete_tool = next((t for t in tools_list if t.__name__ == "delete_task"), None)

                if delete_tool:
                    # Execute deletion
                    result = delete_tool(task_id=pending["task_id"])

                    # Store user confirmation message
                    ChatService.store_message(
                        conversation_id=conversation_id,
                        role="user",
                        content=user_message,
                        metadata=None,
                        session=session
                    )

                    # Store assistant confirmation response
                    assistant_response = f"✓ {result}"
                    ChatService.store_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=assistant_response,
                        metadata={
                            "tool_calls": [{"name": "delete_task", "arguments": {"task_id": pending["task_id"]}}],
                            "action": "task_deleted",
                            "task_id": pending["task_id"]
                        },
                        session=session
                    )

                    logger.info(f"[PENDING ACTION] Executed delete_task for task_id={pending['task_id']}")

                    return ChatResponse(
                        response=assistant_response,
                        conversation_id=conversation_id,
                        action="task_deleted",
                        task_id=pending["task_id"]
                    )

        # Check for cancellation
        elif is_cancellation(user_message):
            logger.info(f"[PENDING ACTION] User cancelled {pending['type']} for task_id={pending['task_id']}")

            # Store user cancellation message
            ChatService.store_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                metadata=None,
                session=session
            )

            # Store assistant acknowledgment
            assistant_response = f"No problem. I did not delete the task '{pending['task_title']}'."
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

        session.add(message)
        session.commit()
        session.refresh(message)

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

            # Step 2.5: Check for pending action confirmation (NEW)
            pending_response = ChatService.handle_pending_action(
                user_message=user_message,
                conversation_id=conversation_id,
                user_id=user_id,
                session=session
            )

            if pending_response:
                logger.info(f"[PENDING ACTION] Handled pending action, skipping agent execution")
                return pending_response

            # Step 3: Fetch context (last 20 messages for AI)
            context_messages = ChatService.get_context_messages(conversation_id, session, limit=20)
            logger.info(f"[CONVERSATION LIFECYCLE] Fetched {len(context_messages)} context messages for conversation_id={conversation_id}, user_id={user_id}")

            # Step 4: Create task tools bound to this user
            tools = create_task_tools(user_id=user_id, session=session)
            logger.info(f"[AGENT EXECUTION] Created {len(tools)} task tools for user_id={user_id}")

            # Step 5: Create agent with tools and instructions
            # CRITICAL: Disable all MCP operations to prevent "Unable to add filesystem: <illegal path>" errors
            # This error occurs when MCP tries to initialize filesystem sandbox with invalid paths in serverless environments
            # We use ONLY @function_tool decorated tools, no MCP servers needed

            logger.info(f"[AGENT EXECUTION] Creating agent with {len(tools)} tools for user_id={user_id}")

            agent = Agent(
                name="TaskManagerAssistant",
                instructions=ChatService.AGENT_INSTRUCTIONS,
                tools=tools,
                model="gpt-4o-mini",  # Use mini for cost efficiency and faster responses
                mcp_servers=[],  # CRITICAL: Empty list - no MCP servers
            )

            logger.info(f"[AGENT EXECUTION] Agent created successfully. Instructions: {len(ChatService.AGENT_INSTRUCTIONS)} chars, Tools: {len(tools)}")

            # Step 6: Run agent with context
            # Runner.run() is ASYNC and requires await
            runner = Runner()

            # Build full conversation context including the new user message
            full_context = context_messages + [{"role": "user", "content": user_message}]

            logger.info(f"[AGENT EXECUTION] Running agent. Context messages: {len(full_context)}, Current message: {user_message[:100]}...")

            # Suppress all stderr output during agent execution to suppress MCP warnings
            # This is safe because we're already logging important events
            old_stderr = sys.stderr
            old_stdout = sys.stdout
            sys.stderr = StringIO()
            sys.stdout = StringIO()

            result = None
            try:
                # Execute agent with just the current user message
                # The agent will have access to task tools but NO filesystem access
                result = await runner.run(
                    starting_agent=agent,
                    input=user_message,
                )
                logger.info(f"[AGENT EXECUTION] Agent completed successfully")
            except ValueError as e:
                # Handle "Unable to add filesystem: <illegal path>" errors
                error_str = str(e).lower()
                if "filesystem" in error_str or "illegal path" in error_str:
                    logger.warning(f"[AGENT EXECUTION] MCP filesystem error (expected, harmless): {e}")
                    # Despite the MCP error, the agent may have still produced a response
                    # Try to extract whatever response we got, or fall back to default
                else:
                    logger.error(f"[AGENT EXECUTION] ValueError: {e}", exc_info=True)
                    raise
            except Exception as e:
                logger.error(f"[AGENT EXECUTION] Agent error: {type(e).__name__}: {e}", exc_info=True)
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
                                    text_parts.append(content_block.text)
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

            # NEW: Detect if agent is asking for delete confirmation
            pending_action = None
            if "Are you sure you want to delete" in assistant_response or \
               "Do you want to delete" in assistant_response:
                # Extract task ID from confirmation message
                match = re.search(r'\(ID:\s*(\d+)\)', assistant_response)
                if match:
                    task_id_str = match.group(1)
                    # Try to find task title in message
                    title_match = re.search(r"'([^']+)'", assistant_response)
                    task_title = title_match.group(1) if title_match else "this task"

                    pending_action = {
                        "type": "delete_task",
                        "task_id": int(task_id_str),
                        "task_title": task_title,
                        "awaiting_confirmation": True,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    logger.info(f"[PENDING ACTION] Detected confirmation request for task_id={pending_action['task_id']}")

            # T025: Parse tool calls from agent result to determine action type
            action = "conversation"  # Default action
            task_id = None
            tool_calls_metadata = []

            # Extract tool calls from result new_items
            if result and hasattr(result, 'new_items') and result.new_items:
                for item in result.new_items:
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

                        # Parse arguments to extract task_id if present
                        tool_args = {}
                        try:
                            tool_args = json.loads(tool_args_str) if tool_args_str else {}
                        except json.JSONDecodeError:
                            logger.warning(f"[TOOL CALL TRACKING] Failed to parse tool arguments for tool={tool_name}, user_id={user_id}, args_str={tool_args_str[:100]}")

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
                metadata["pending_action"] = pending_action

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
            logger.error(
                f"[ERROR] Exception during message processing: user_id={user_id}, "
                f"conversation_id={conversation.id if 'conversation' in locals() else 'unknown'}, "
                f"error_type={type(e).__name__}, error_message={str(e)}",
                exc_info=True
            )

            # Return error response to user
            error_response = ChatResponse(
                response="I'm sorry, I encountered an error processing your request. Please try again.",
                conversation_id=conversation.id if 'conversation' in locals() else 0,
                action=None,
                task_id=None
            )

            # Try to store error message if conversation exists
            if 'conversation' in locals():
                try:
                    error_msg = ChatService.store_message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=error_response.response,
                        metadata={"error": str(e)},
                        session=session
                    )
                    logger.info(f"[MESSAGE STORAGE] Stored error message message_id={error_msg.id}, conversation_id={conversation.id}, user_id={user_id}")
                except Exception as store_error:
                    logger.error(f"[ERROR] Failed to store error message: user_id={user_id}, conversation_id={conversation.id}, error={store_error}", exc_info=True)

            raise
