"""User SQLModel for Better Auth compatibility.

This model is READ-ONLY - Better Auth manages user creation on the frontend.
The backend only reads user data for reference/joining.

IMPORTANT: table=False because Better Auth creates and manages the 'user' table.
We define this model only for type hints and potential read queries.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel):
    """User model matching Better Auth's table schema.

    NOTE: table=False - this model does NOT create a database table.
    Better Auth manages the 'user' table on the frontend.

    This model can be used for:
    - Type hints
    - Reading user data if needed (raw SQL or text queries)
    """

    # Better Auth uses TEXT-based IDs, not UUIDs
    id: str
    name: str
    email: str
    emailVerified: bool = False
    image: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class UserRead(SQLModel):
    """User response schema (read-only)."""

    id: str
    name: str
    email: str
    emailVerified: bool
    image: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
