"""
Task CRUD endpoints.
T034-T041: Task operations with authentication and user-scoped filtering.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated, Optional
from datetime import datetime
import logging

from ..core.database import get_session
from ..api.deps import get_current_user, CurrentUser
from ..models.task import Task, TaskCreate, TaskUpdate, TaskRead, TaskList, VALID_PRIORITIES

logger = logging.getLogger(__name__)

router = APIRouter()


# T034: GET /tasks - List user's tasks, filtered by user_id
@router.get("/", response_model=TaskList)
async def list_tasks(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    # T041: Query parameters for filtering and sorting
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[str] = Query(None, description="Filter by priority (low/medium/high)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: Optional[str] = Query("created_at", description="Sort field"),
    order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
):
    """
    List all tasks for the authenticated user.
    Results are filtered by user_id from JWT token.

    Query Parameters:
    - completed: Filter by completion status (true/false)
    - priority: Filter by priority level (low/medium/high)
    - category: Filter by category name
    - sort: Sort by field (created_at, updated_at, due_date, priority, title)
    - order: Sort order (asc/desc, default: desc)
    """
    try:
        # Build query with user_id filter (critical for data isolation)
        query = select(Task).where(Task.user_id == current_user.user_id)

        # Apply optional filters
        if completed is not None:
            query = query.where(Task.completed == completed)
        if priority is not None:
            # Normalize priority filter to lowercase
            normalized_priority = priority.lower().strip()
            if normalized_priority in VALID_PRIORITIES:
                query = query.where(Task.priority == normalized_priority)
        if category is not None:
            query = query.where(Task.category == category)

        # Apply sorting
        sort_column = getattr(Task, sort, Task.created_at)
        if order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        tasks = session.exec(query).all()

        logger.info(f"User {current_user.user_id} listed {len(tasks)} tasks")

        return TaskList(
            tasks=[TaskRead.model_validate(task) for task in tasks],
            total=len(tasks),
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error in list_tasks: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {type(e).__name__}: {str(e)[:200]}",
        )


# T035: POST /tasks - Create task with user_id from JWT
@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Create a new task for the authenticated user.
    Task is automatically associated with user_id from JWT.
    """
    try:
        # Normalize priority to lowercase (default to 'medium' if invalid)
        normalized_priority = task_data.get_normalized_priority()
        logger.info(f"Creating task with priority: {task_data.priority} -> {normalized_priority}")

        # Create task with user_id from authenticated user
        task = Task(
            user_id=current_user.user_id,
            title=task_data.title,
            description=task_data.description,
            priority=normalized_priority,
            category=task_data.category,
            due_date=task_data.due_date,
        )

        session.add(task)
        session.commit()
        session.refresh(task)

        logger.info(f"User {current_user.user_id} created task {task.id}")

        return TaskRead.model_validate(task)
    except SQLAlchemyError as e:
        logger.error(f"Database error in create_task: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {type(e).__name__}: {str(e)[:200]}",
        )


# T036: GET /tasks/{task_id} - Single task with ownership check
@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Get a specific task by ID.
    Returns 404 if task doesn't exist OR doesn't belong to user (security).
    """
    # Query with both task_id AND user_id (ownership check)
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    ).first()

    if not task:
        # Return 404 for both "not found" and "not owned" (prevents info leakage)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return TaskRead.model_validate(task)


# T037: PATCH /tasks/{task_id} - Update with ownership check
@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Update a task's properties.
    Only the task owner can update. Returns 404 for non-owned tasks.
    """
    # Query with ownership check
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Update only provided fields
    update_data = task_data.model_dump(exclude_unset=True)

    # Normalize priority if provided
    if "priority" in update_data and update_data["priority"] is not None:
        normalized_priority = task_data.get_normalized_priority()
        update_data["priority"] = normalized_priority
        logger.info(f"Updating priority: {task_data.priority} -> {normalized_priority}")

    for key, value in update_data.items():
        setattr(task, key, value)

    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    logger.info(f"User {current_user.user_id} updated task {task.id}")

    return TaskRead.model_validate(task)


# T038: DELETE /tasks/{task_id} - Delete with ownership check
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Delete a task.
    Only the task owner can delete. Returns 404 for non-owned tasks.
    """
    # Query with ownership check
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    session.delete(task)
    session.commit()

    logger.info(f"User {current_user.user_id} deleted task {task_id}")

    return None


# T039: POST /tasks/{task_id}/complete - Mark task as complete
@router.post("/{task_id}/complete", response_model=TaskRead)
async def complete_task(
    task_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Mark a task as completed.
    Convenience endpoint for toggling completion status.
    """
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task.completed = True
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    logger.info(f"User {current_user.user_id} completed task {task.id}")

    return TaskRead.model_validate(task)


# T040: DELETE /tasks/{task_id}/complete - Mark task as incomplete
@router.delete("/{task_id}/complete", response_model=TaskRead)
async def uncomplete_task(
    task_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Mark a task as incomplete.
    Convenience endpoint for toggling completion status.
    """
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task.completed = False
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    logger.info(f"User {current_user.user_id} uncompleted task {task.id}")

    return TaskRead.model_validate(task)
