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
    metadata: JSON string storing tool_calls, action type, reasoning traces.
    """

    __tablename__ = "message"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str = Field()  # 'user' or 'assistant'
    content: str = Field()
    metadata_json: Optional[str] = Field(default=None, sa_column_kwargs={"name": "metadata"})
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversation: Optional[Conversation] = Relationship(back_populates="messages")

    @property
    def metadata(self) -> Optional[dict]:
        """Parse metadata JSON string to dict."""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return None

    @metadata.setter
    def metadata(self, value: Optional[dict]):
        """Serialize metadata dict to JSON string."""
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
    metadata: Optional[dict] = None
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
