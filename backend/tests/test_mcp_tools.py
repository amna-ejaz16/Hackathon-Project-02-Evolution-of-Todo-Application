"""
Unit tests for MCP tool implementations.

Tests all 5 MCP tools:
- add_task: Task creation with validation
- list_tasks: Querying with filters
- complete_task: Marking tasks complete
- delete_task: Task deletion
- update_task: Partial task updates

Validates:
- Input validation (Pydantic)
- User scoping (no cross-user access)
- Error handling (MCPError)
- Response formatting
"""

import pytest
from datetime import date
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

from src.models.task import Task
from src.services.mcp_service import (
    MCPTaskTools,
    MCPError,
    TaskCreateInput,
    TaskListInput,
    TaskUpdateInput,
    TaskIdInput,
)


# --- Test Fixtures ---

@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="user_id")
def user_id_fixture():
    """Test user ID."""
    return "user_test_123"


@pytest.fixture(name="other_user_id")
def other_user_id_fixture():
    """Different user ID for cross-user tests."""
    return "user_other_456"


@pytest.fixture(name="mcp_tools")
def mcp_tools_fixture(session: Session):
    """Create MCPTaskTools instance."""
    return MCPTaskTools(session=session)


@pytest.fixture(name="sample_task")
def sample_task_fixture(session: Session, user_id: str):
    """Create a sample task for testing."""
    task = Task(
        user_id=user_id,
        title="Sample Task",
        description="Test description",
        priority="medium",
        category="Work",
        due_date=date(2026, 3, 1),
        completed=False,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


# --- add_task Tests ---

@pytest.mark.asyncio
async def test_add_task_success(mcp_tools: MCPTaskTools, user_id: str):
    """Test successful task creation."""
    context = {"user_id": user_id}

    result = await mcp_tools.add_task(
        context=context,
        title="New Task",
        description="Task description",
        priority="high",
        category="Personal",
        due_date="2026-03-15",
    )

    assert result["success"] is True
    assert "data" in result
    task_data = result["data"]
    assert task_data["title"] == "New Task"
    assert task_data["priority"] == "high"
    assert task_data["category"] == "Personal"
    assert task_data["due_date"] == "2026-03-15"
    assert task_data["completed"] is False
    assert "id" in task_data


@pytest.mark.asyncio
async def test_add_task_minimal(mcp_tools: MCPTaskTools, user_id: str):
    """Test task creation with only required field (title)."""
    context = {"user_id": user_id}

    result = await mcp_tools.add_task(
        context=context,
        title="Minimal Task",
    )

    assert result["success"] is True
    task_data = result["data"]
    assert task_data["title"] == "Minimal Task"
    assert task_data["priority"] == "medium"  # Default
    assert task_data["description"] is None
    assert task_data["category"] is None
    assert task_data["due_date"] is None


@pytest.mark.asyncio
async def test_add_task_invalid_priority(mcp_tools: MCPTaskTools, user_id: str):
    """Test add_task with invalid priority (should default to medium)."""
    context = {"user_id": user_id}

    result = await mcp_tools.add_task(
        context=context,
        title="Task with Invalid Priority",
        priority="super-urgent",  # Invalid
    )

    # Should succeed but normalize to 'medium'
    assert result["success"] is True
    task_data = result["data"]
    assert task_data["priority"] == "medium"


@pytest.mark.asyncio
async def test_add_task_invalid_date_format(mcp_tools: MCPTaskTools, user_id: str):
    """Test add_task with invalid date format."""
    context = {"user_id": user_id}

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.add_task(
            context=context,
            title="Task with Bad Date",
            due_date="2026/03/15",  # Wrong format
        )

    assert exc_info.value.code == "VALIDATION_ERROR"
    assert "due_date" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_add_task_missing_user_context(mcp_tools: MCPTaskTools):
    """Test add_task without user_id in context."""
    context = {}  # No user_id

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.add_task(
            context=context,
            title="Task",
        )

    assert exc_info.value.code == "UNAUTHORIZED"


# --- list_tasks Tests ---

@pytest.mark.asyncio
async def test_list_tasks_all(
    mcp_tools: MCPTaskTools,
    session: Session,
    user_id: str,
):
    """Test listing all tasks for a user."""
    # Create multiple tasks
    tasks_data = [
        {"title": "Task 1", "priority": "high", "completed": False},
        {"title": "Task 2", "priority": "medium", "completed": True},
        {"title": "Task 3", "priority": "low", "completed": False},
    ]

    for data in tasks_data:
        task = Task(user_id=user_id, **data)
        session.add(task)
    session.commit()

    context = {"user_id": user_id}
    result = await mcp_tools.list_tasks(context=context, status="all")

    assert result["success"] is True
    assert result["data"]["total"] == 3
    assert len(result["data"]["tasks"]) == 3


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(
    mcp_tools: MCPTaskTools,
    session: Session,
    user_id: str,
):
    """Test filtering tasks by status (pending/completed)."""
    # Create tasks with different statuses
    session.add(Task(user_id=user_id, title="Pending Task", completed=False))
    session.add(Task(user_id=user_id, title="Completed Task", completed=True))
    session.commit()

    context = {"user_id": user_id}

    # Test pending filter
    result = await mcp_tools.list_tasks(context=context, status="pending")
    assert result["data"]["total"] == 1
    assert result["data"]["tasks"][0]["completed"] is False

    # Test completed filter
    result = await mcp_tools.list_tasks(context=context, status="completed")
    assert result["data"]["total"] == 1
    assert result["data"]["tasks"][0]["completed"] is True


@pytest.mark.asyncio
async def test_list_tasks_filter_by_priority(
    mcp_tools: MCPTaskTools,
    session: Session,
    user_id: str,
):
    """Test filtering tasks by priority."""
    session.add(Task(user_id=user_id, title="High Task", priority="high"))
    session.add(Task(user_id=user_id, title="Low Task", priority="low"))
    session.commit()

    context = {"user_id": user_id}
    result = await mcp_tools.list_tasks(context=context, priority="high")

    assert result["data"]["total"] == 1
    assert result["data"]["tasks"][0]["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks_filter_by_category(
    mcp_tools: MCPTaskTools,
    session: Session,
    user_id: str,
):
    """Test filtering tasks by category."""
    session.add(Task(user_id=user_id, title="Work Task", category="Work"))
    session.add(Task(user_id=user_id, title="Home Task", category="Home"))
    session.commit()

    context = {"user_id": user_id}
    result = await mcp_tools.list_tasks(context=context, category="Work")

    assert result["data"]["total"] == 1
    assert result["data"]["tasks"][0]["category"] == "Work"


@pytest.mark.asyncio
async def test_list_tasks_user_scoping(
    mcp_tools: MCPTaskTools,
    session: Session,
    user_id: str,
    other_user_id: str,
):
    """Test that users can only see their own tasks."""
    # Create tasks for different users
    session.add(Task(user_id=user_id, title="User1 Task"))
    session.add(Task(user_id=other_user_id, title="User2 Task"))
    session.commit()

    # Query as user1
    context = {"user_id": user_id}
    result = await mcp_tools.list_tasks(context=context, status="all")

    # Should only see own task
    assert result["data"]["total"] == 1
    assert result["data"]["tasks"][0]["title"] == "User1 Task"


@pytest.mark.asyncio
async def test_list_tasks_empty_result(mcp_tools: MCPTaskTools, user_id: str):
    """Test listing tasks when user has no tasks."""
    context = {"user_id": user_id}
    result = await mcp_tools.list_tasks(context=context, status="all")

    assert result["success"] is True
    assert result["data"]["total"] == 0
    assert result["data"]["tasks"] == []


# --- complete_task Tests ---

@pytest.mark.asyncio
async def test_complete_task_success(
    mcp_tools: MCPTaskTools,
    sample_task: Task,
    user_id: str,
):
    """Test marking a task as completed."""
    context = {"user_id": user_id}
    result = await mcp_tools.complete_task(context=context, task_id=sample_task.id)

    assert result["success"] is True
    assert result["data"]["completed"] is True
    assert result["data"]["id"] == sample_task.id


@pytest.mark.asyncio
async def test_complete_task_not_found(mcp_tools: MCPTaskTools, user_id: str):
    """Test completing a task that doesn't exist."""
    context = {"user_id": user_id}

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.complete_task(context=context, task_id=99999)

    assert exc_info.value.code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_complete_task_wrong_user(
    mcp_tools: MCPTaskTools,
    sample_task: Task,
    other_user_id: str,
):
    """Test that users cannot complete other users' tasks."""
    context = {"user_id": other_user_id}  # Different user

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.complete_task(context=context, task_id=sample_task.id)

    assert exc_info.value.code == "NOT_FOUND"


# --- delete_task Tests ---

@pytest.mark.asyncio
async def test_delete_task_success(
    mcp_tools: MCPTaskTools,
    session: Session,
    sample_task: Task,
    user_id: str,
):
    """Test deleting a task."""
    context = {"user_id": user_id}
    task_id = sample_task.id

    result = await mcp_tools.delete_task(context=context, task_id=task_id)

    assert result["success"] is True
    assert result["data"]["deleted_task_id"] == task_id

    # Verify task is actually deleted
    from sqlmodel import select
    deleted_task = session.exec(select(Task).where(Task.id == task_id)).first()
    assert deleted_task is None


@pytest.mark.asyncio
async def test_delete_task_not_found(mcp_tools: MCPTaskTools, user_id: str):
    """Test deleting a task that doesn't exist."""
    context = {"user_id": user_id}

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.delete_task(context=context, task_id=99999)

    assert exc_info.value.code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_task_wrong_user(
    mcp_tools: MCPTaskTools,
    sample_task: Task,
    other_user_id: str,
):
    """Test that users cannot delete other users' tasks."""
    context = {"user_id": other_user_id}  # Different user

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.delete_task(context=context, task_id=sample_task.id)

    assert exc_info.value.code == "NOT_FOUND"


# --- update_task Tests ---

@pytest.mark.asyncio
async def test_update_task_title(
    mcp_tools: MCPTaskTools,
    sample_task: Task,
    user_id: str,
):
    """Test updating only the task title."""
    context = {"user_id": user_id}

    result = await mcp_tools.update_task(
        context=context,
        task_id=sample_task.id,
        title="Updated Title",
    )

    assert result["success"] is True
    assert result["data"]["title"] == "Updated Title"
    # Other fields should remain unchanged
    assert result["data"]["priority"] == sample_task.priority


@pytest.mark.asyncio
async def test_update_task_multiple_fields(
    mcp_tools: MCPTaskTools,
    sample_task: Task,
    user_id: str,
):
    """Test updating multiple task fields at once."""
    context = {"user_id": user_id}

    result = await mcp_tools.update_task(
        context=context,
        task_id=sample_task.id,
        title="New Title",
        priority="high",
        category="Updated Category",
        due_date="2026-04-01",
    )

    assert result["success"] is True
    data = result["data"]
    assert data["title"] == "New Title"
    assert data["priority"] == "high"
    assert data["category"] == "Updated Category"
    assert data["due_date"] == "2026-04-01"


@pytest.mark.asyncio
async def test_update_task_no_fields(
    mcp_tools: MCPTaskTools,
    sample_task: Task,
    user_id: str,
):
    """Test update with no fields provided (should fail)."""
    context = {"user_id": user_id}

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.update_task(
            context=context,
            task_id=sample_task.id,
            # No fields provided
        )

    assert exc_info.value.code == "VALIDATION_ERROR"
    assert "no fields" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_update_task_invalid_priority(
    mcp_tools: MCPTaskTools,
    sample_task: Task,
    user_id: str,
):
    """Test updating with invalid priority."""
    context = {"user_id": user_id}

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.update_task(
            context=context,
            task_id=sample_task.id,
            priority="super-high",  # Invalid
        )

    assert exc_info.value.code == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_update_task_not_found(mcp_tools: MCPTaskTools, user_id: str):
    """Test updating a task that doesn't exist."""
    context = {"user_id": user_id}

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.update_task(
            context=context,
            task_id=99999,
            title="New Title",
        )

    assert exc_info.value.code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_task_wrong_user(
    mcp_tools: MCPTaskTools,
    sample_task: Task,
    other_user_id: str,
):
    """Test that users cannot update other users' tasks."""
    context = {"user_id": other_user_id}  # Different user

    with pytest.raises(MCPError) as exc_info:
        await mcp_tools.update_task(
            context=context,
            task_id=sample_task.id,
            title="Hacked Title",
        )

    assert exc_info.value.code == "NOT_FOUND"


# --- Validation Tests ---

def test_task_create_input_validation():
    """Test TaskCreateInput Pydantic validation."""
    # Valid input
    valid_input = TaskCreateInput(
        title="Test Task",
        priority="high",
        due_date="2026-03-01",
    )
    assert valid_input.title == "Test Task"
    assert valid_input.priority == "high"

    # Invalid due_date format
    with pytest.raises(ValueError):
        TaskCreateInput(title="Test", due_date="invalid-date")

    # Invalid priority (should normalize to medium)
    input_with_invalid_priority = TaskCreateInput(
        title="Test",
        priority="SUPER_HIGH"
    )
    assert input_with_invalid_priority.priority == "medium"


def test_task_list_input_validation():
    """Test TaskListInput Pydantic validation."""
    # Valid input
    valid_input = TaskListInput(status="pending", priority="high")
    assert valid_input.status == "pending"
    assert valid_input.priority == "high"

    # Invalid status (should normalize to "all")
    invalid_status_input = TaskListInput(status="invalid_status")
    assert invalid_status_input.status == "all"

    # Invalid priority
    with pytest.raises(ValueError):
        TaskListInput(priority="super_high")


def test_task_id_input_validation():
    """Test TaskIdInput Pydantic validation."""
    # Valid input
    valid_input = TaskIdInput(task_id=123)
    assert valid_input.task_id == 123

    # Invalid (zero or negative)
    with pytest.raises(ValueError):
        TaskIdInput(task_id=0)

    with pytest.raises(ValueError):
        TaskIdInput(task_id=-5)
