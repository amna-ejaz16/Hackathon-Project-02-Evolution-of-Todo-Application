"""Task model for the Todo application."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    """Represents a single todo item."""
    id: int
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate task after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Task title cannot be empty")
