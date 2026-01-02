"""Console interface for user interaction."""
from typing import List
from services.task_manager import TaskManager
from models.task import Task


class ConsoleInterface:
    """Handles console user interaction for the Todo app."""

    def __init__(self, task_manager: TaskManager):
        """Initialize ConsoleInterface with TaskManager dependency."""
        self.task_manager = task_manager

    def display_menu(self) -> None:
        """Display the main menu with all available options."""
        print("\n" + "=" * 30)
        print("=== Todo Application ===")
        print("=" * 30)
        print("1. View all tasks")
        print("2. Add new task")
        print("3. Update task")
        print("4. Delete task")
        print("5. Mark task as complete/incomplete")
        print("6. Exit")
        print("=" * 30)

    def get_user_choice(self) -> str:
        """
        Read and validate user's menu choice.

        Returns:
            Valid menu choice ("1" through "6")
        """
        valid_choices = ["1", "2", "3", "4", "5", "6"]
        while True:
            choice = input("\nChoose an option (1-6): ").strip()
            if choice in valid_choices:
                return choice
            self.display_message("Invalid choice. Please enter a number between 1 and 6.", "error")

    def display_tasks(self, tasks: List[Task]) -> None:
        """
        Display a formatted list of tasks.

        Args:
            tasks: List of tasks to display
        """
        if not tasks:
            print("\nNo tasks found. Your todo list is empty.")
            return

        print("\nYour Tasks:")
        print("-" * 60)
        for task in tasks:
            status = "☑" if task.completed else "☐"
            print(f"[{task.id}] {status} {task.title}")
            desc = task.description if task.description else "(none)"
            print(f"    Description: {desc}")
        print("-" * 60)

    def prompt_task_details(self) -> dict:
        """
        Prompt user for task title and description.

        Returns:
            dict with 'title' and 'description' keys
        """
        while True:
            title = input("\nEnter task title: ").strip()
            if title:
                break
            self.display_message("Task title cannot be empty. Please try again.", "error")

        description = input("Enter task description (optional, press Enter to skip): ").strip()

        return {"title": title, "description": description}

    def display_message(self, message: str, message_type: str = "info") -> None:
        """
        Display a formatted message to the user.

        Args:
            message: Message text to display
            message_type: Type of message ("success", "error", "info")
        """
        symbols = {
            "success": "✓",
            "error": "✗",
            "info": "ℹ"
        }
        symbol = symbols.get(message_type, "ℹ")
        print(f"\n{symbol} {message}")

    def run_add_task_workflow(self) -> None:
        """Handle the complete workflow for adding a task."""
        try:
            details = self.prompt_task_details()
            task = self.task_manager.add_task(details["title"], details["description"])
            self.display_message(f"Task '{task.title}' added successfully!", "success")
        except ValueError as e:
            self.display_message(f"Error: {e}", "error")
        except Exception as e:
            self.display_message(f"Unexpected error: {e}", "error")

    def run_view_tasks_workflow(self) -> None:
        """Handle the complete workflow for viewing all tasks."""
        tasks = self.task_manager.get_all_tasks()
        self.display_tasks(tasks)

    def prompt_task_id(self) -> int:
        """
        Prompt user for a task ID.

        Returns:
            Valid task ID as integer
        """
        while True:
            try:
                task_id_str = input("\nEnter task ID: ").strip()
                task_id = int(task_id_str)
                if task_id > 0:
                    return task_id
                self.display_message("Task ID must be a positive number.", "error")
            except ValueError:
                self.display_message("Invalid input. Please enter a numeric task ID.", "error")

    def run_toggle_complete_workflow(self) -> None:
        """Handle the complete workflow for toggling task completion status."""
        tasks = self.task_manager.get_all_tasks()
        if not tasks:
            self.display_message("No tasks available to mark complete.", "info")
            return

        self.display_tasks(tasks)
        task_id = self.prompt_task_id()

        if self.task_manager.toggle_complete(task_id):
            self.display_message("Task status updated!", "success")
        else:
            self.display_message("Task not found. Please check the task ID and try again.", "error")

    def run_update_task_workflow(self) -> None:
        """Handle the complete workflow for updating a task."""
        tasks = self.task_manager.get_all_tasks()
        if not tasks:
            self.display_message("No tasks available to update.", "info")
            return

        self.display_tasks(tasks)
        task_id = self.prompt_task_id()

        # Check if task exists
        task = self.task_manager.get_task(task_id)
        if not task:
            self.display_message("Task not found. Please check the task ID and try again.", "error")
            return

        print(f"\nCurrent task: {task.title}")
        print(f"Current description: {task.description if task.description else '(none)'}")

        details = self.prompt_task_details()

        try:
            if self.task_manager.update_task(task_id, details["title"], details["description"]):
                self.display_message("Task updated successfully!", "success")
            else:
                self.display_message("Failed to update task.", "error")
        except ValueError as e:
            self.display_message(f"Error: {e}", "error")
        except Exception as e:
            self.display_message(f"Unexpected error: {e}", "error")

    def run_delete_task_workflow(self) -> None:
        """Handle the complete workflow for deleting a task."""
        tasks = self.task_manager.get_all_tasks()
        if not tasks:
            self.display_message("No tasks available to delete.", "info")
            return

        self.display_tasks(tasks)
        task_id = self.prompt_task_id()

        # Check if task exists
        task = self.task_manager.get_task(task_id)
        if not task:
            self.display_message("Task not found. Please check the task ID and try again.", "error")
            return

        # Confirmation prompt
        print(f"\nAre you sure you want to delete this task?")
        print(f"Task: {task.title}")
        confirmation = input("Type 'yes' to confirm deletion: ").strip().lower()

        if confirmation != "yes":
            self.display_message("Deletion cancelled.", "info")
            return

        if self.task_manager.delete_task(task_id):
            self.display_message("Task deleted successfully!", "success")
        else:
            self.display_message("Failed to delete task.", "error")
