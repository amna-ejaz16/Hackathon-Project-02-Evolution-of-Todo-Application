"""
Chat service for AI-powered task management assistant.

Handles conversation management, message persistence, and agent execution
using OpenAI Agents SDK with task management tools.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func
from agents import Agent, Runner
import logging
import json

from ..models.chat import Conversation, Message, ChatRequest, ChatResponse
from ..models.task import Task
from .task_tools import create_task_tools

logger = logging.getLogger(__name__)


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

DELETING TASKS (T031):
When a user wants to delete a task:
- First use list_tasks to find matching tasks by title keywords
- If exactly one match is found, confirm before proceeding: "Are you sure you want to delete '[task title]'?"
- Wait for explicit confirmation (yes/confirm/delete) before calling delete_task
- If multiple matches, list them and ask which one to delete
- If no match, inform the user and offer to list their tasks

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
    def process_message(
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

            # Step 3: Fetch context (last 20 messages for AI)
            context_messages = ChatService.get_context_messages(conversation_id, session, limit=20)
            logger.info(f"[CONVERSATION LIFECYCLE] Fetched {len(context_messages)} context messages for conversation_id={conversation_id}, user_id={user_id}")

            # Step 4: Create task tools bound to this user
            tools = create_task_tools(user_id=user_id, session=session)
            logger.info(f"[AGENT EXECUTION] Created {len(tools)} task tools for user_id={user_id}")

            # Step 5: Create agent with tools and instructions
            agent = Agent(
                name="TaskManagerAssistant",
                instructions=ChatService.AGENT_INSTRUCTIONS,
                tools=tools,
                # Note: model defaults to "gpt-4o" in openai-agents SDK
                # Override with model="gpt-4o-mini" for cost savings if needed
            )

            logger.info(f"[AGENT EXECUTION] Created agent with instructions_length={len(ChatService.AGENT_INSTRUCTIONS)}, tools_count={len(tools)}, user_id={user_id}")

            # Step 6: Run agent with context
            # The Runner.run() method handles the conversation context and tool execution
            runner = Runner(agent=agent)

            # Build full conversation context including the new user message
            full_context = context_messages + [{"role": "user", "content": user_message}]

            logger.info(f"[AGENT EXECUTION] Running agent with context_message_count={len(full_context)}, user_id={user_id}, conversation_id={conversation_id}")

            # Execute agent
            result = runner.run(messages=full_context)

            logger.info(f"[AGENT EXECUTION] Agent execution completed, user_id={user_id}, conversation_id={conversation_id}")

            # Step 7: Extract response and metadata
            # The OpenAI Agents SDK Runner.run() returns a Response object
            # Access the final message content from the result
            assistant_response = "I'm sorry, I couldn't process that request."

            if hasattr(result, 'messages') and result.messages:
                # Get the last assistant message
                for msg in reversed(result.messages):
                    if msg.role == "assistant" and msg.content:
                        assistant_response = msg.content
                        logger.info(f"[AGENT EXECUTION] Extracted assistant response, length={len(assistant_response)}, user_id={user_id}")
                        break
            elif isinstance(result, dict):
                # Fallback for dict-like response
                assistant_response = result.get("response", assistant_response)
                logger.warning(f"[AGENT EXECUTION] Agent result was dict-like (unexpected format), user_id={user_id}")
            else:
                logger.warning(f"[AGENT EXECUTION] Could not extract assistant response from result, user_id={user_id}, result_type={type(result)}")

            # T025: Parse tool calls from agent result to determine action type
            action = "conversation"  # Default action
            task_id = None
            tool_calls_metadata = []

            # Extract tool calls from result messages
            if hasattr(result, 'messages'):
                for msg in result.messages:
                    if msg.role == "assistant" and hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.function.name if hasattr(tool_call.function, 'name') else ""
                            tool_args_str = tool_call.function.arguments if hasattr(tool_call.function, 'arguments') else ""

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
