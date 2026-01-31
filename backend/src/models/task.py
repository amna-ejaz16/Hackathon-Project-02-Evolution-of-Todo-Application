"""Task SQLModel for todo items."""

from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String


# Valid priority values (lowercase only)
VALID_PRIORITIES = {"low", "medium", "high"}


class Priority(str, Enum):
    """Task priority levels.

    Values are lowercase to match database constraint.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def from_str(cls, value: str) -> "Priority":
        """Convert string to Priority, defaulting to MEDIUM if invalid."""
        if value is None:
            return cls.MEDIUM
        normalized = str(value).lower().strip()
        if normalized in VALID_PRIORITIES:
            return cls(normalized)
        return cls.MEDIUM


class TaskBase(SQLModel):
    """Base task fields shared by create/update schemas."""

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None)
    # Priority stored as string to match DB constraint (low/medium/high)
    priority: str = Field(default="medium")
    category: Optional[str] = Field(default=None, max_length=50)
    due_date: Optional[date] = Field(default=None)


class Task(TaskBase, table=True):
    """Task model with database table mapping.

    Note: user_id is TEXT to match Better Auth's user ID format.
    The foreign key constraint to 'user.id' is defined in the database
    schema (scripts/create-tasks-table.sql), not here, to avoid
    SQLModel conflicts with Better Auth's table.
    """

    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)  # FK constraint is in DB schema
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreate(SQLModel):
    """Schema for creating a new task."""

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None)
    priority: str = Field(default="medium")
    category: Optional[str] = Field(default=None, max_length=50)
    due_date: Optional[date] = Field(default=None)

    def get_normalized_priority(self) -> str:
        """Get priority normalized to lowercase, defaulting to 'medium' if invalid."""
        if self.priority is None:
            return "medium"
        normalized = str(self.priority).lower().strip()
        return normalized if normalized in VALID_PRIORITIES else "medium"


class TaskUpdate(SQLModel):
    """Schema for updating a task (all fields optional)."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None)
    completed: Optional[bool] = Field(default=None)
    priority: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None, max_length=50)
    due_date: Optional[date] = Field(default=None)

    def get_normalized_priority(self) -> Optional[str]:
        """Get priority normalized to lowercase, or None if not provided."""
        if self.priority is None:
            return None
        normalized = str(self.priority).lower().strip()
        return normalized if normalized in VALID_PRIORITIES else "medium"


class TaskRead(TaskBase):
    """Schema for task responses."""

    id: int
    user_id: str
    completed: bool
    created_at: datetime
    updated_at: datetime


class TaskList(SQLModel):
    """Schema for task list responses (GET /tasks)."""

    tasks: List[TaskRead]
    total: int
