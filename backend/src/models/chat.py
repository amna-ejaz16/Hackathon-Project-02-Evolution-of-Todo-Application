"""Chat models for AI chatbot conversation persistence."""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
import json


class Conversation(SQLModel, table=True):
    """Represents a chat thread between a user and the AI assistant.

    One active conversation per user (enforced at application level).
    user_id is TEXT to match Better Auth's user.id format.
    """

    __tablename__ = "conversation"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    title: str = Field(default="Task Assistant")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    """A single chat message within a conversation.

    role: 'user' or 'assistant'
    metadata_json: JSON string storing tool_calls, action type, reasoning traces.
    """

    __tablename__ = "message"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str = Field()  # 'user' or 'assistant'
    content: str = Field()
    metadata_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversation: Optional[Conversation] = Relationship(back_populates="messages")

    def get_metadata(self) -> Optional[dict]:
        """Parse metadata JSON string to dict.

        Returns:
            dict: Parsed metadata or None if not set
        """
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except json.JSONDecodeError:
                return None
        return None

    def set_metadata(self, value: Optional[dict]) -> None:
        """Serialize metadata dict to JSON string.

        Args:
            value: Dict to serialize or None to clear
        """
        if value is not None:
            self.metadata_json = json.dumps(value)
        else:
            self.metadata_json = None


# --- Pydantic Schemas (API contracts) ---


class ChatRequest(SQLModel):
    """Request body for POST /api/chat."""

    message: str = Field(min_length=1, max_length=2000)


class MessageRead(SQLModel):
    """Response schema for a single message."""

    id: int
    role: str
    content: str
    metadata_dict: Optional[dict] = None
    created_at: datetime


class ChatResponse(SQLModel):
    """Response body for POST /api/chat."""

    response: str
    conversation_id: int
    action: Optional[str] = None
    task_id: Optional[int] = None


class ChatHistoryResponse(SQLModel):
    """Response body for GET /api/chat/history."""

    messages: List[MessageRead]
    conversation_id: Optional[int] = None
    total: int
