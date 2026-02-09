"""
MCP Service Layer - Base infrastructure for Model Context Protocol server.

This module provides the foundational architecture for exposing task management
operations as MCP tools. It defines:
- Pydantic validation models for all tool inputs
- Base MCP tool class with error handling
- Error response formatting for MCP protocol
- Tool execution patterns with user context binding

Architecture:
- Stateless tool design (all context in request parameters)
- User-scoped operations (user_id from JWT token)
- Validation using Pydantic models (type safety + coercion)
- Consistent error handling across all tools
- Reuses existing SQLModel Task model and database session

Integration with MCP SDK:
- Tools are exposed via Official MCP SDK server
- Each tool receives context dict with user_id (injected by auth middleware)
- Tools return structured responses (success/error) compatible with MCP protocol
- Validation errors are caught and formatted as MCP error responses
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select
import logging

from ..models.task import Task, VALID_PRIORITIES
from ..middleware.mcp_auth import MCPAuthError

logger = logging.getLogger(__name__)


# --- Pydantic Validation Models ---

class TaskCreateInput(BaseModel):
    """
    Input validation schema for add_task MCP tool.

    Enforces:
    - Title: 1-200 characters (required)
    - Priority: one of low/medium/high (normalized to lowercase)
    - Due date: ISO format YYYY-MM-DD
    - Category: optional string
    """

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: str = Field(default="medium", description="Task priority: low, medium, or high")
    category: Optional[str] = Field(None, max_length=50, description="Task category or tag")
    due_date: Optional[str] = Field(None, description="Due date in ISO format (YYYY-MM-DD)")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Normalize priority to lowercase and validate."""
        if v is None:
            return "medium"
        normalized = v.lower().strip()
        if normalized not in VALID_PRIORITIES:
            logger.warning(f"Invalid priority '{v}', defaulting to 'medium'")
            return "medium"
        return normalized

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate due_date is in ISO format."""
        if v is None:
            return None
        try:
            # Parse to ensure valid date format
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid due_date format '{v}'. Expected YYYY-MM-DD")


class TaskUpdateInput(BaseModel):
    """
    Input validation schema for update_task MCP tool.

    All fields are optional (partial update).
    task_id is required separately in the function signature.
    """

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    priority: Optional[str] = Field(None)
    category: Optional[str] = Field(None, max_length=50)
    due_date: Optional[str] = Field(None)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority if provided."""
        if v is None:
            return None
        normalized = v.lower().strip()
        if normalized not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{v}'. Must be one of: low, medium, high")
        return normalized

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate due_date if provided."""
        if v is None:
            return None
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid due_date format '{v}'. Expected YYYY-MM-DD")


class TaskListInput(BaseModel):
    """
    Input validation schema for list_tasks MCP tool.

    Supports filtering by:
    - status: all, pending, completed
    - priority: low, medium, high
    - category: exact match
    """

    status: str = Field(default="all", description="Filter by status: all, pending, completed")
    priority: Optional[str] = Field(None, description="Filter by priority: low, medium, high")
    category: Optional[str] = Field(None, description="Filter by category")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Normalize status."""
        normalized = v.lower().strip()
        if normalized not in {"all", "pending", "completed"}:
            logger.warning(f"Invalid status '{v}', defaulting to 'all'")
            return "all"
        return normalized

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority if provided."""
        if v is None:
            return None
        normalized = v.lower().strip()
        if normalized not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{v}'. Must be one of: low, medium, high")
        return normalized


class TaskIdInput(BaseModel):
    """
    Input validation schema for task operations that require only a task_id.

    Used by: complete_task, uncomplete_task, delete_task
    """

    task_id: int = Field(..., gt=0, description="ID of the task to operate on")


# --- MCP Error Handling ---

class MCPError(Exception):
    """
    Custom exception for MCP tool errors.

    Provides structured error information compatible with MCP protocol.

    Attributes:
        code: Error code (e.g., "NOT_FOUND", "VALIDATION_ERROR", "UNAUTHORIZED")
        message: Human-readable error message
        details: Optional dict with additional error context
    """

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for MCP protocol response."""
        result = {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }
        if self.details:
            result["error"]["details"] = self.details
        return result


# --- MCP Tool Base Class ---

class MCPToolBase:
    """
    Base class for MCP tools with common patterns.

    Provides:
    - User context validation
    - Database session management
    - Error handling and logging
    - Response formatting

    Subclasses implement specific tool logic (add_task, list_tasks, etc.)
    """

    def __init__(self, session: Session):
        """
        Initialize MCP tool with database session.

        Args:
            session: SQLModel database session for queries
        """
        self.session = session

    def _validate_user_context(self, context: Dict[str, Any]) -> str:
        """
        Extract and validate user_id from MCP context.

        Args:
            context: MCP request context (contains user_id after auth middleware)

        Returns:
            User ID string

        Raises:
            MCPError: If user_id is missing from context
        """
        user_id = context.get("user_id")
        if not user_id:
            logger.error("[MCP_TOOL] Missing user_id in context (auth middleware failure?)")
            raise MCPError(
                code="UNAUTHORIZED",
                message="User authentication required",
                details={"context_keys": list(context.keys())}
            )
        return user_id

    def _get_user_task(self, task_id: int, user_id: str) -> Task:
        """
        Fetch a task by ID with ownership validation.

        Args:
            task_id: Task ID to fetch
            user_id: User ID for ownership check

        Returns:
            Task object if found and owned by user

        Raises:
            MCPError: If task not found or not owned by user
        """
        task = self.session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()

        if not task:
            logger.warning(f"[MCP_TOOL] Task {task_id} not found for user {user_id}")
            raise MCPError(
                code="NOT_FOUND",
                message=f"Task {task_id} not found or you don't have access to it",
                details={"task_id": task_id}
            )

        return task

    def _format_success_response(self, data: Any, message: Optional[str] = None) -> Dict[str, Any]:
        """
        Format a successful MCP tool response.

        Args:
            data: Response data (can be dict, list, string, etc.)
            message: Optional success message

        Returns:
            MCP-compatible success response dict
        """
        response = {"success": True, "data": data}
        if message:
            response["message"] = message
        return response

    def _format_error_response(self, error: Exception) -> Dict[str, Any]:
        """
        Format an error as MCP tool response.

        Args:
            error: Exception to format

        Returns:
            MCP-compatible error response dict
        """
        if isinstance(error, MCPError):
            return error.to_dict()
        elif isinstance(error, MCPAuthError):
            return MCPError(
                code="UNAUTHORIZED",
                message=error.message,
                details={"http_code": error.code}
            ).to_dict()
        else:
            # Unexpected error
            logger.error(f"[MCP_TOOL] Unexpected error: {type(error).__name__}: {error}", exc_info=True)
            return MCPError(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                details={"error_type": type(error).__name__}
            ).to_dict()


# --- MCP Tool Implementations ---

class MCPTaskTools(MCPToolBase):
    """
    MCP tool implementations for task management operations.

    This class provides all 5 core task tools exposed via MCP protocol:
    - add_task: Create new tasks
    - list_tasks: Query tasks with filters
    - complete_task: Mark tasks complete
    - delete_task: Remove tasks
    - update_task: Modify task properties

    All operations are user-scoped and logged for auditing.
    """

    async def add_task(
        self,
        context: Dict[str, Any],
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new task (MCP tool: add_task).

        Args:
            context: MCP context with user_id (injected by auth)
            title: Task title (required, 1-200 chars)
            description: Optional task description
            priority: Priority level (low/medium/high), default medium
            category: Optional category/tag
            due_date: Optional due date in ISO format (YYYY-MM-DD)

        Returns:
            Success response with created task data

        Raises:
            MCPError: On validation or database errors
        """
        try:
            # Extract and validate user context
            user_id = self._validate_user_context(context)

            # Validate input using Pydantic model
            input_data = TaskCreateInput(
                title=title,
                description=description,
                priority=priority,
                category=category,
                due_date=due_date,
            )

            # Parse due_date to date object if provided
            parsed_due_date = None
            if input_data.due_date:
                parsed_due_date = date.fromisoformat(input_data.due_date)

            # Create task in database
            task = Task(
                user_id=user_id,
                title=input_data.title,
                description=input_data.description,
                priority=input_data.priority,
                category=input_data.category,
                due_date=parsed_due_date,
            )

            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)

            logger.info(f"[MCP_TOOL] add_task: Created task {task.id} for user {user_id}")

            # Format response
            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "category": task.category,
                "due_date": str(task.due_date) if task.due_date else None,
                "completed": task.completed,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }

            return self._format_success_response(
                data=task_data,
                message=f"Task '{title}' created successfully"
            )

        except ValueError as e:
            # Pydantic validation error
            logger.warning(f"[MCP_TOOL] add_task validation error: {e}")
            raise MCPError(
                code="VALIDATION_ERROR",
                message=str(e),
                details={"field": "input_validation"}
            )
        except Exception as e:
            logger.error(f"[MCP_TOOL] add_task error: {type(e).__name__}: {e}", exc_info=True)
            raise MCPError(
                code="INTERNAL_ERROR",
                message="Failed to create task",
                details={"error_type": type(e).__name__}
            )

    async def list_tasks(
        self,
        context: Dict[str, Any],
        status: str = "all",
        priority: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List tasks with optional filtering (MCP tool: list_tasks).

        Args:
            context: MCP context with user_id
            status: Filter by status (all/pending/completed), default all
            priority: Filter by priority (low/medium/high), optional
            category: Filter by category, optional
            page: Page number for pagination, default 1
            page_size: Results per page, default 20

        Returns:
            Success response with list of tasks and pagination info

        Raises:
            MCPError: On validation or database errors
        """
        try:
            # Extract and validate user context
            user_id = self._validate_user_context(context)

            # Validate input
            input_data = TaskListInput(
                status=status,
                priority=priority,
                category=category,
            )

            # Build query with user scoping
            query = select(Task).where(Task.user_id == user_id)

            # Apply status filter
            if input_data.status == "pending":
                query = query.where(Task.completed == False)
            elif input_data.status == "completed":
                query = query.where(Task.completed == True)
            # "all" means no filter

            # Apply priority filter
            if input_data.priority:
                query = query.where(Task.priority == input_data.priority)

            # Apply category filter
            if input_data.category:
                query = query.where(Task.category == input_data.category)

            # Order by created_at descending
            query = query.order_by(Task.created_at.desc())

            # Execute query (pagination can be added later if needed)
            tasks = self.session.exec(query).all()

            # Format task data
            tasks_data = []
            for task in tasks:
                tasks_data.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,
                    "category": task.category,
                    "due_date": str(task.due_date) if task.due_date else None,
                    "completed": task.completed,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                })

            logger.info(f"[MCP_TOOL] list_tasks: Found {len(tasks)} tasks for user {user_id}")

            return self._format_success_response(
                data={
                    "tasks": tasks_data,
                    "total": len(tasks),
                    "filters": {
                        "status": input_data.status,
                        "priority": input_data.priority,
                        "category": input_data.category,
                    }
                },
                message=f"Found {len(tasks)} tasks"
            )

        except ValueError as e:
            logger.warning(f"[MCP_TOOL] list_tasks validation error: {e}")
            raise MCPError(
                code="VALIDATION_ERROR",
                message=str(e),
                details={"field": "input_validation"}
            )
        except Exception as e:
            logger.error(f"[MCP_TOOL] list_tasks error: {type(e).__name__}: {e}", exc_info=True)
            raise MCPError(
                code="INTERNAL_ERROR",
                message="Failed to list tasks",
                details={"error_type": type(e).__name__}
            )

    async def complete_task(
        self,
        context: Dict[str, Any],
        task_id: int,
    ) -> Dict[str, Any]:
        """
        Mark a task as completed (MCP tool: complete_task).

        Args:
            context: MCP context with user_id
            task_id: ID of task to mark complete

        Returns:
            Success response with updated task data

        Raises:
            MCPError: If task not found or database error
        """
        try:
            # Extract and validate user context
            user_id = self._validate_user_context(context)

            # Validate input
            input_data = TaskIdInput(task_id=task_id)

            # Get task with ownership check
            task = self._get_user_task(input_data.task_id, user_id)

            # Mark as complete
            task.completed = True
            task.updated_at = datetime.utcnow()

            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)

            logger.info(f"[MCP_TOOL] complete_task: Marked task {task.id} complete for user {user_id}")

            # Format response
            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "category": task.category,
                "due_date": str(task.due_date) if task.due_date else None,
                "completed": task.completed,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }

            return self._format_success_response(
                data=task_data,
                message=f"Task '{task.title}' marked as completed"
            )

        except MCPError:
            # Re-raise MCP errors (like NOT_FOUND)
            raise
        except ValueError as e:
            logger.warning(f"[MCP_TOOL] complete_task validation error: {e}")
            raise MCPError(
                code="VALIDATION_ERROR",
                message=str(e),
                details={"field": "task_id"}
            )
        except Exception as e:
            logger.error(f"[MCP_TOOL] complete_task error: {type(e).__name__}: {e}", exc_info=True)
            raise MCPError(
                code="INTERNAL_ERROR",
                message="Failed to complete task",
                details={"error_type": type(e).__name__}
            )

    async def delete_task(
        self,
        context: Dict[str, Any],
        task_id: int,
    ) -> Dict[str, Any]:
        """
        Delete a task permanently (MCP tool: delete_task).

        Args:
            context: MCP context with user_id
            task_id: ID of task to delete

        Returns:
            Success response with deletion confirmation

        Raises:
            MCPError: If task not found or database error
        """
        try:
            # Extract and validate user context
            user_id = self._validate_user_context(context)

            # Validate input
            input_data = TaskIdInput(task_id=task_id)

            # Get task with ownership check
            task = self._get_user_task(input_data.task_id, user_id)

            # Store title before deletion
            task_title = task.title
            task_id_val = task.id

            # Delete task
            self.session.delete(task)
            self.session.commit()

            logger.info(f"[MCP_TOOL] delete_task: Deleted task {task_id_val} for user {user_id}")

            return self._format_success_response(
                data={
                    "deleted_task_id": task_id_val,
                    "deleted_task_title": task_title,
                },
                message=f"Task '{task_title}' deleted successfully"
            )

        except MCPError:
            # Re-raise MCP errors (like NOT_FOUND)
            raise
        except ValueError as e:
            logger.warning(f"[MCP_TOOL] delete_task validation error: {e}")
            raise MCPError(
                code="VALIDATION_ERROR",
                message=str(e),
                details={"field": "task_id"}
            )
        except Exception as e:
            logger.error(f"[MCP_TOOL] delete_task error: {type(e).__name__}: {e}", exc_info=True)
            raise MCPError(
                code="INTERNAL_ERROR",
                message="Failed to delete task",
                details={"error_type": type(e).__name__}
            )

    async def update_task(
        self,
        context: Dict[str, Any],
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update task properties (MCP tool: update_task).

        Args:
            context: MCP context with user_id
            task_id: ID of task to update (required)
            title: New title, optional
            description: New description, optional
            priority: New priority, optional
            category: New category, optional
            due_date: New due date (ISO format), optional

        Returns:
            Success response with updated task data

        Raises:
            MCPError: If task not found, validation error, or database error
        """
        try:
            # Extract and validate user context
            user_id = self._validate_user_context(context)

            # Validate task_id
            task_id_input = TaskIdInput(task_id=task_id)

            # Get task with ownership check
            task = self._get_user_task(task_id_input.task_id, user_id)

            # Validate update fields
            update_data = TaskUpdateInput(
                title=title,
                description=description,
                priority=priority,
                category=category,
                due_date=due_date,
            )

            # Track changes
            changes = []

            # Update only provided fields
            if update_data.title is not None:
                task.title = update_data.title
                changes.append("title")

            if update_data.description is not None:
                task.description = update_data.description
                changes.append("description")

            if update_data.priority is not None:
                task.priority = update_data.priority
                changes.append("priority")

            if update_data.category is not None:
                task.category = update_data.category
                changes.append("category")

            if update_data.due_date is not None:
                task.due_date = date.fromisoformat(update_data.due_date)
                changes.append("due_date")

            if not changes:
                raise MCPError(
                    code="VALIDATION_ERROR",
                    message="No fields provided for update",
                    details={"task_id": task_id}
                )

            task.updated_at = datetime.utcnow()

            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)

            logger.info(f"[MCP_TOOL] update_task: Updated task {task.id} fields [{', '.join(changes)}] for user {user_id}")

            # Format response
            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "category": task.category,
                "due_date": str(task.due_date) if task.due_date else None,
                "completed": task.completed,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }

            return self._format_success_response(
                data=task_data,
                message=f"Task '{task.title}' updated successfully ({', '.join(changes)})"
            )

        except MCPError:
            # Re-raise MCP errors
            raise
        except ValueError as e:
            logger.warning(f"[MCP_TOOL] update_task validation error: {e}")
            raise MCPError(
                code="VALIDATION_ERROR",
                message=str(e),
                details={"field": "input_validation"}
            )
        except Exception as e:
            logger.error(f"[MCP_TOOL] update_task error: {type(e).__name__}: {e}", exc_info=True)
            raise MCPError(
                code="INTERNAL_ERROR",
                message="Failed to update task",
                details={"error_type": type(e).__name__}
            )


# --- Utility Functions ---

def create_mcp_tools_manifest() -> Dict[str, Any]:
    """
    Generate MCP tools manifest for tool discovery.

    Returns a structured description of all available MCP tools
    with their input schemas, descriptions, and metadata.

    This is used by MCP clients to discover available capabilities.

    Returns:
        MCP tools manifest dict compatible with MCP protocol
    """
    return {
        "tools": [
            {
                "name": "add_task",
                "description": "Create a new task with title, description, priority, category, and due date",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 1, "maxLength": 200},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                        "category": {"type": "string", "maxLength": 50},
                        "due_date": {"type": "string", "format": "date", "description": "ISO format YYYY-MM-DD"}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "list_tasks",
                "description": "List tasks with optional filtering by status, priority, and category",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["all", "pending", "completed"], "default": "all"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                        "category": {"type": "string"},
                        "page": {"type": "integer", "minimum": 1, "default": 1},
                        "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}
                    }
                }
            },
            {
                "name": "complete_task",
                "description": "Mark a task as completed",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "minimum": 1}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "delete_task",
                "description": "Permanently delete a task",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "minimum": 1}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "update_task",
                "description": "Update task properties (partial update)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "minimum": 1},
                        "title": {"type": "string", "minLength": 1, "maxLength": 200},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                        "category": {"type": "string", "maxLength": 50},
                        "due_date": {"type": "string", "format": "date"}
                    },
                    "required": ["task_id"]
                }
            }
        ]
    }
