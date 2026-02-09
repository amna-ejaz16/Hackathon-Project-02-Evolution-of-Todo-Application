"""
Task management function tools for OpenAI Agent.

These tools wrap existing task CRUD operations as @function_tool decorated
functions, providing the AI agent with bounded, testable actions.
User context is bound via the factory function closure.
"""

from typing import List, Optional
from sqlmodel import Session, select
from agents import function_tool
from datetime import datetime, date
import logging

from ..models.task import Task, VALID_PRIORITIES

logger = logging.getLogger(__name__)


def create_task_tools(user_id: str, session: Session) -> List:
    """
    Factory function that creates task management tools bound to a specific user.

    Args:
        user_id: User ID from JWT token (user context for all operations)
        session: SQLModel database session for queries

    Returns:
        List of @function_tool decorated functions with user_id bound via closure

    Example:
        tools = create_task_tools(user_id="user_abc123", session=db_session)
        agent = Agent(tools=tools, ...)
    """

    # T023: add_task function tool
    @function_tool
    def add_task(
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> str:
        """
        Create a new task for the user.

        Args:
            title: Task title (required, 1-200 characters)
            description: Optional task description
            priority: Task priority (low/medium/high), defaults to medium
            category: Optional category/tag (e.g., Work, Home, Personal)
            due_date: Optional due date in ISO format (YYYY-MM-DD)

        Returns:
            Formatted confirmation string with task details
        """
        try:
            # Normalize priority to lowercase (default to 'medium' if invalid)
            normalized_priority = priority.lower().strip() if priority else "medium"
            if normalized_priority not in VALID_PRIORITIES:
                normalized_priority = "medium"

            # Parse due_date if provided
            parsed_due_date = None
            if due_date:
                try:
                    parsed_due_date = date.fromisoformat(due_date)
                except ValueError:
                    logger.warning(f"Invalid due_date format '{due_date}', ignoring")

            # Create task with user_id from closure
            task = Task(
                user_id=user_id,
                title=title,
                description=description,
                priority=normalized_priority,
                category=category,
                due_date=parsed_due_date,
            )

            session.add(task)
            session.commit()
            session.refresh(task)

            logger.info(f"Agent created task {task.id} for user {user_id}")

            # Build confirmation message
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(normalized_priority, "⚪")
            result = f"Created task '{title}' (ID: {task.id}) with priority {priority_emoji} {normalized_priority}"

            if category:
                result += f", category: {category}"
            if parsed_due_date:
                result += f", due: {parsed_due_date}"

            return result

        except Exception as e:
            logger.error(f"Error in add_task tool for user {user_id}: {type(e).__name__}: {e}")
            return f"I encountered an error while creating the task: {str(e)[:100]}"

    # T026: Expand list_tasks with filtering
    @function_tool
    def list_tasks(
        status: Optional[str] = "all",
        priority: Optional[str] = None,
        category: Optional[str] = None,
    ) -> str:
        """
        List tasks for the current user with optional filtering.

        Args:
            status: Filter by status - "all" (default), "pending", or "completed"
            priority: Filter by priority - "low", "medium", or "high" (optional)
            category: Filter by category name (optional)

        Returns:
            Formatted string listing tasks or "You don't have any tasks yet" if empty
        """
        try:
            # Build query with user_id filter (critical for data isolation)
            query = select(Task).where(Task.user_id == user_id)

            # Apply status filter
            if status and status.lower() == "pending":
                query = query.where(Task.completed == False)
            elif status and status.lower() == "completed":
                query = query.where(Task.completed == True)
            # "all" or None means no status filter

            # Apply priority filter
            if priority:
                normalized_priority = priority.lower().strip()
                if normalized_priority in VALID_PRIORITIES:
                    query = query.where(Task.priority == normalized_priority)

            # Apply category filter
            if category:
                query = query.where(Task.category == category)

            # Order by created_at descending
            query = query.order_by(Task.created_at.desc())

            tasks = session.exec(query).all()

            if not tasks:
                # Customize message based on filters
                if status == "pending" or priority or category:
                    return "No tasks match your filters. Try adjusting the criteria."
                return "You don't have any tasks yet. Would you like to create one?"

            # Format tasks as a numbered list with key details
            filter_desc = []
            if status and status != "all":
                filter_desc.append(f"status={status}")
            if priority:
                filter_desc.append(f"priority={priority}")
            if category:
                filter_desc.append(f"category={category}")

            header = f"You have {len(tasks)} task(s)"
            if filter_desc:
                header += f" ({', '.join(filter_desc)})"
            header += ":"

            result_lines = [header]
            for idx, task in enumerate(tasks, start=1):
                status_icon = "✓ Complete" if task.completed else "○ Pending"
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")

                task_line = f"{idx}. [{task.id}] {status_icon} {priority_emoji} {task.title}"

                # Add optional details
                details = []
                if task.category:
                    details.append(f"Category: {task.category}")
                if task.due_date:
                    details.append(f"Due: {task.due_date}")
                if task.description:
                    details.append(f"Note: {task.description[:50]}...")

                if details:
                    task_line += f" ({', '.join(details)})"

                result_lines.append(task_line)

            logger.info(f"Agent listed {len(tasks)} tasks for user {user_id} (filters: {filter_desc})")
            return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error in list_tasks tool for user {user_id}: {type(e).__name__}: {e}")
            return f"I encountered an error while fetching your tasks: {str(e)[:100]}"

    # T028: complete_task function tool
    @function_tool
    def complete_task(task_id: int) -> str:
        """
        Mark a task as completed.

        Args:
            task_id: ID of the task to mark as complete

        Returns:
            Confirmation string with task title
        """
        try:
            # Query with ownership check
            task = session.exec(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            ).first()

            if not task:
                return f"Task {task_id} not found. Please check the task ID and try again."

            task.completed = True
            task.updated_at = datetime.utcnow()

            session.add(task)
            session.commit()
            session.refresh(task)

            logger.info(f"Agent completed task {task.id} for user {user_id}")

            return f"✓ Marked task '{task.title}' (ID: {task.id}) as completed"

        except Exception as e:
            logger.error(f"Error in complete_task tool for user {user_id}: {type(e).__name__}: {e}")
            return f"I encountered an error while completing the task: {str(e)[:100]}"

    # T029: uncomplete_task function tool
    @function_tool
    def uncomplete_task(task_id: int) -> str:
        """
        Mark a task as incomplete (not completed).

        Args:
            task_id: ID of the task to mark as incomplete

        Returns:
            Confirmation string with task title
        """
        try:
            # Query with ownership check
            task = session.exec(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            ).first()

            if not task:
                return f"Task {task_id} not found. Please check the task ID and try again."

            task.completed = False
            task.updated_at = datetime.utcnow()

            session.add(task)
            session.commit()
            session.refresh(task)

            logger.info(f"Agent uncompleted task {task.id} for user {user_id}")

            return f"○ Marked task '{task.title}' (ID: {task.id}) as incomplete"

        except Exception as e:
            logger.error(f"Error in uncomplete_task tool for user {user_id}: {type(e).__name__}: {e}")
            return f"I encountered an error while marking the task as incomplete: {str(e)[:100]}"

    # T030: delete_task function tool
    @function_tool
    def delete_task(task_id: int) -> str:
        """
        Delete a task permanently.

        Args:
            task_id: ID of the task to delete

        Returns:
            Confirmation string with task title
        """
        try:
            # Query with ownership check
            task = session.exec(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            ).first()

            if not task:
                return f"Task {task_id} not found. Please check the task ID and try again."

            task_title = task.title  # Store title before deletion

            session.delete(task)
            session.commit()

            logger.info(f"Agent deleted task {task_id} for user {user_id}")

            return f"Deleted task '{task_title}' (ID: {task_id})"

        except Exception as e:
            logger.error(f"Error in delete_task tool for user {user_id}: {type(e).__name__}: {e}")
            return f"I encountered an error while deleting the task: {str(e)[:100]}"

    # T032: update_task function tool
    @function_tool
    def update_task(
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> str:
        """
        Update a task's properties (partial update).

        Args:
            task_id: ID of the task to update (required)
            title: New task title (optional)
            description: New description (optional)
            priority: New priority (low/medium/high) (optional)
            category: New category (optional)
            due_date: New due date in ISO format (YYYY-MM-DD) (optional)

        Returns:
            Confirmation string with what was changed
        """
        try:
            # Query with ownership check
            task = session.exec(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            ).first()

            if not task:
                return f"Task {task_id} not found. Please check the task ID and try again."

            # Track changes for response message
            changes = []

            # Update only provided fields
            if title is not None:
                task.title = title
                changes.append(f"title to '{title}'")

            if description is not None:
                task.description = description
                changes.append(f"description")

            if priority is not None:
                normalized_priority = priority.lower().strip()
                if normalized_priority in VALID_PRIORITIES:
                    task.priority = normalized_priority
                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(normalized_priority, "⚪")
                    changes.append(f"priority to {priority_emoji} {normalized_priority}")
                else:
                    logger.warning(f"Invalid priority '{priority}', ignoring")

            if category is not None:
                task.category = category
                changes.append(f"category to '{category}'")

            if due_date is not None:
                try:
                    parsed_due_date = date.fromisoformat(due_date)
                    task.due_date = parsed_due_date
                    changes.append(f"due date to {parsed_due_date}")
                except ValueError:
                    logger.warning(f"Invalid due_date format '{due_date}', ignoring")

            if not changes:
                return f"No changes made to task '{task.title}' (ID: {task.id}). Please provide at least one field to update."

            task.updated_at = datetime.utcnow()

            session.add(task)
            session.commit()
            session.refresh(task)

            logger.info(f"Agent updated task {task.id} for user {user_id}: {', '.join(changes)}")

            return f"Updated task '{task.title}' (ID: {task.id}): {', '.join(changes)}"

        except Exception as e:
            logger.error(f"Error in update_task tool for user {user_id}: {type(e).__name__}: {e}")
            return f"I encountered an error while updating the task: {str(e)[:100]}"

    # Return list of all tools
    return [
        add_task,
        list_tasks,
        complete_task,
        uncomplete_task,
        delete_task,
        update_task,
    ]
