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
    AGENT_INSTRUCTIONS = """You are a task management assistant that helps users manage their todo tasks.

You can help users:
- List their tasks (all tasks, pending, completed, by priority, by category)
- Create new tasks with details (title, description, priority, category, due date)
- Complete or uncomplete tasks
- Update task details (title, description, priority, category, due date)
- Delete tasks

When a user wants to create a task:
- Extract the title, description, priority (low/medium/high), category, and due date from their message
- If the title is unclear or missing, ask for clarification
- Apply reasonable defaults: medium priority, no category, no due date
- Always confirm what you created with full details

When a user asks to see tasks:
- Use the list_tasks tool with appropriate filters
- Format the response clearly with task status, priority, and due dates
- If no tasks match, suggest creating one

For completing, updating, or deleting tasks:
- First identify the task by title using list_tasks
- If multiple matches, ask the user to specify which one
- If no match, inform the user and offer to list their tasks
- For delete operations, always confirm the action

IMPORTANT CONSTRAINTS:
- You can ONLY perform task-related operations
- You cannot access external data or perform non-task actions
- Always be helpful and concise
- If you're unsure, ask clarifying questions

Be friendly, helpful, and conversational while staying focused on task management."""

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

        # Set metadata using the property setter (handles JSON serialization)
        if metadata:
            message.metadata = metadata

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
            # Step 1: Get or create conversation
            conversation = ChatService.get_or_create_conversation(user_id, session)
            conversation_id = conversation.id

            # Step 2: Store user message
            ChatService.store_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                metadata=None,
                session=session
            )

            # Step 3: Fetch context (last 20 messages for AI)
            context_messages = ChatService.get_context_messages(conversation_id, session, limit=20)

            # Step 4: Create task tools bound to this user
            tools = create_task_tools(user_id=user_id, session=session)

            # Step 5: Create agent with tools and instructions
            agent = Agent(
                name="TaskManagerAssistant",
                instructions=ChatService.AGENT_INSTRUCTIONS,
                tools=tools,
                # Note: model defaults to "gpt-4o" in openai-agents SDK
                # Override with model="gpt-4o-mini" for cost savings if needed
            )

            logger.info(f"Created agent with {len(tools)} tools for user {user_id}")

            # Step 6: Run agent with context
            # The Runner.run() method handles the conversation context and tool execution
            runner = Runner(agent=agent)

            # Build full conversation context including the new user message
            full_context = context_messages + [{"role": "user", "content": user_message}]

            # Execute agent
            result = runner.run(messages=full_context)

            logger.info(f"Agent execution completed for user {user_id}")

            # Step 7: Extract response and metadata
            # The result contains the assistant's response and any tool calls
            assistant_response = result.get("response", "I'm sorry, I couldn't process that request.")

            # Extract metadata (tool calls, action type)
            metadata = {
                "tool_calls": result.get("tool_calls", []),
                "action": "conversation",  # Default action
            }

            # Determine action type from tool calls (will be enhanced in T025)
            action = None
            task_id = None

            if metadata["tool_calls"]:
                # Extract action from first tool call (simplified for T015)
                first_tool = metadata["tool_calls"][0] if metadata["tool_calls"] else None
                if first_tool:
                    tool_name = first_tool.get("name", "")
                    if tool_name == "list_tasks":
                        action = "tasks_listed"
                    # Additional tool mappings will be added in US3-US6

            # Step 8: Store assistant message
            ChatService.store_message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response,
                metadata=metadata,
                session=session
            )

            # Step 9: Return response
            return ChatResponse(
                response=assistant_response,
                conversation_id=conversation_id,
                action=action,
                task_id=task_id
            )

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {type(e).__name__}: {e}")

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
                    ChatService.store_message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=error_response.response,
                        metadata={"error": str(e)},
                        session=session
                    )
                except Exception as store_error:
                    logger.error(f"Failed to store error message: {store_error}")

            raise
