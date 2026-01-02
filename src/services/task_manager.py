"""TaskManager service for managing todo tasks."""
from typing import List
from models.task import Task


class TaskManager:
    """Manages task CRUD operations in memory."""

    def __init__(self):
        """Initialize TaskManager with empty task list."""
        self.tasks: List[Task] = []
        self.next_id: int = 1

    def add_task(self, title: str, description: str = "") -> Task:
        """
        Create a new task and add it to the list.

        Args:
            title: Task title (required, non-empty)
            description: Task description (optional)

        Returns:
            The newly created Task object

        Raises:
            ValueError: If title is empty or whitespace-only
        """
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")

        task = Task(
            id=self.next_id,
            title=title.strip(),
            description=description.strip() if description else ""
        )
        self.tasks.append(task)
        self.next_id += 1
        return task

    def get_all_tasks(self) -> List[Task]:
        """
        Retrieve all tasks in creation order.

        Returns:
            List of all tasks (may be empty)
        """
        return self.tasks.copy()

    def get_task(self, task_id: int) -> Task | None:
        """
        Retrieve a task by its ID.

        Args:
            task_id: Unique identifier of the task

        Returns:
            Task object if found, None otherwise
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def toggle_complete(self, task_id: int) -> bool:
        """
        Toggle the completion status of a task.

        Args:
            task_id: Unique identifier of the task

        Returns:
            True if task was found and toggled, False otherwise
        """
        task = self.get_task(task_id)
        if task:
            task.completed = not task.completed
            return True
        return False

    def update_task(self, task_id: int, title: str | None = None, description: str | None = None) -> bool:
        """
        Update title and/or description of an existing task.

        Args:
            task_id: Unique identifier of the task
            title: New title (if provided, must be non-empty)
            description: New description (if provided)

        Returns:
            True if task was found and updated, False otherwise

        Raises:
            ValueError: If provided title is empty or whitespace-only
        """
        task = self.get_task(task_id)
        if not task:
            return False

        if title is not None:
            if not title or not title.strip():
                raise ValueError("Task title cannot be empty")
            task.title = title.strip()

        if description is not None:
            task.description = description.strip()

        return True

    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task from the list.

        Args:
            task_id: Unique identifier of the task

        Returns:
            True if task was found and deleted, False otherwise
        """
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            return True
        return False
