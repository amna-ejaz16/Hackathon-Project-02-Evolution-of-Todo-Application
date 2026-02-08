"""
Task management function tools for OpenAI Agent.

These tools wrap existing task CRUD operations as @function_tool decorated
functions, providing the AI agent with bounded, testable actions.
User context is bound via the factory function closure.
"""

from typing import List
from sqlmodel import Session, select
from agents import function_tool
import logging

from ..models.task import Task

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

    @function_tool
    def list_tasks() -> str:
        """
        List all tasks for the current user.

        Returns a formatted string with task details or a friendly message if no tasks exist.
        This is a placeholder that will be expanded in T026 to support filtering by status,
        priority, and category.

        Returns:
            Formatted string listing tasks or "You don't have any tasks yet" if empty
        """
        try:
            # Query tasks filtered by user_id (critical for data isolation)
            query = select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
            tasks = session.exec(query).all()

            if not tasks:
                return "You don't have any tasks yet. Would you like to create one?"

            # Format tasks as a numbered list with key details
            result_lines = [f"You have {len(tasks)} task(s):"]
            for idx, task in enumerate(tasks, start=1):
                status = "✓ Complete" if task.completed else "○ Pending"
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")

                task_line = f"{idx}. {status} {priority_emoji} {task.title}"

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

            logger.info(f"Agent listed {len(tasks)} tasks for user {user_id}")
            return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error in list_tasks tool for user {user_id}: {type(e).__name__}: {e}")
            return f"I encountered an error while fetching your tasks: {str(e)[:100]}"

    # Return list of tools (will be expanded with add_task, update_task, etc. in later phases)
    return [list_tasks]
