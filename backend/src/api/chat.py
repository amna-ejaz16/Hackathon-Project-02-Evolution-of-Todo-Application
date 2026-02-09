"""
Chat endpoints for AI-powered task management assistant.
T016-T017: Chat message processing and conversation history retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import Annotated, Optional
import logging

from ..core.database import get_session
from ..api.deps import get_current_user, CurrentUser
from ..models.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    MessageRead,
    Conversation,
    Message,
)
from ..services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()


# T016: POST /api/chat - Send message to AI assistant
@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Send a message to the AI task management assistant.

    The assistant can help with:
    - Listing tasks (all, pending, completed, by priority/category)
    - Creating new tasks with details
    - Completing or uncompleting tasks
    - Updating task details
    - Deleting tasks

    Request:
    - message: User input (1-2000 characters)

    Response:
    - response: Assistant's reply
    - conversation_id: ID of the conversation thread
    - action: Type of action performed (e.g., "tasks_listed", "task_created")
    - task_id: ID of affected task (if applicable)

    Error Cases:
    - 401: Invalid or missing JWT token
    - 422: Validation error (empty message or > 2000 chars)
    - 503: AI service temporarily unavailable
    """
    try:
        logger.info(
            f"User {current_user.user_id} sent message: {request.message[:100]}..."
        )

        # Process message through AI agent (async)
        response = await ChatService.process_message(
            user_message=request.message,
            user_id=current_user.user_id,
            session=session,
        )

        logger.info(
            f"Chat response generated for user {current_user.user_id} "
            f"(conversation {response.conversation_id}, action: {response.action})"
        )

        return response

    except Exception as e:
        # Log the error with full details
        logger.error(
            f"Error processing chat message for user {current_user.user_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True,
        )

        # Check if it's an OpenAI/agent-related error
        error_message = str(e).lower()
        if any(
            keyword in error_message
            for keyword in ["openai", "api", "rate limit", "timeout", "connection"]
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable. Please try again later.",
            )

        # For other errors, return generic 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message. Please try again.",
        )


# T017: GET /api/chat/history - Retrieve conversation history
@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Number of recent messages to retrieve (1-200, default: 50)",
    ),
):
    """
    Get the conversation history for the authenticated user.

    Returns the most recent messages from the user's active conversation,
    ordered chronologically (oldest first).

    Query Parameters:
    - limit: Number of messages to retrieve (default: 50, max: 200)

    Response:
    - messages: List of messages with role, content, metadata, timestamps
    - conversation_id: ID of the conversation (null if no conversation exists)
    - total: Total number of messages in the conversation

    Error Cases:
    - 401: Invalid or missing JWT token
    """
    try:
        # Get the user's conversation (if it exists)
        conversation = session.exec(
            select(Conversation).where(Conversation.user_id == current_user.user_id)
        ).first()

        # If no conversation exists, return empty history
        if not conversation:
            logger.info(f"No conversation found for user {current_user.user_id}")
            return ChatHistoryResponse(
                messages=[],
                conversation_id=None,
                total=0,
            )

        # Get messages with limit
        messages_query = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        messages = session.exec(messages_query).all()

        # Reverse to chronological order (oldest first)
        messages = list(reversed(messages))

        # Get total count
        total_count_query = select(Message).where(
            Message.conversation_id == conversation.id
        )
        total = len(session.exec(total_count_query).all())

        logger.info(
            f"Retrieved {len(messages)} messages (of {total} total) "
            f"for user {current_user.user_id} (conversation {conversation.id})"
        )

        # Convert to response schema
        message_reads = [
            MessageRead(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                metadata_dict=msg.get_metadata(),  # Deserialize JSON to dict
                created_at=msg.created_at,
            )
            for msg in messages
        ]

        return ChatHistoryResponse(
            messages=message_reads,
            conversation_id=conversation.id,
            total=total,
        )

    except Exception as e:
        logger.error(
            f"Error retrieving chat history for user {current_user.user_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history. Please try again.",
        )
