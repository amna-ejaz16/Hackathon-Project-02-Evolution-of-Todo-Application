# Contract: ConsoleInterface

**Module**: `src/cli/console_interface.py`
**Date**: 2026-01-02
**Purpose**: Define the interface for console user interaction

## Overview

The ConsoleInterface class handles all user interaction via console I/O. It displays menus, prompts for input, validates user input, displays task lists, and shows messages. It delegates business logic to TaskManager.

---

## Class Definition

```python
from typing import List
from services.task_manager import TaskManager
from models.task import Task

class ConsoleInterface:
    """Handles console user interaction for the Todo app."""

    def __init__(self, task_manager: TaskManager):
        """Initialize ConsoleInterface with TaskManager dependency."""
        self.task_manager = task_manager
```

---

## Methods

### display_menu

**Signature**:
```python
def display_menu(self) -> None:
```

**Purpose**: Display the main menu with all available options.

**Parameters**: None

**Returns**: None

**Output** (to console):
```
=== Todo Application ===
1. View all tasks
2. Add new task
3. Update task
4. Delete task
5. Mark task as complete/incomplete
6. Exit

Choose an option (1-6):
```

**Behavior**:
1. Print menu header with decorative border
2. Print numbered options (1-6)
3. Print prompt for user choice
4. No input reading (handled by `get_user_choice`)

**Maps to**: FR-009

---

### get_user_choice

**Signature**:
```python
def get_user_choice(self) -> str:
```

**Purpose**: Read and validate user's menu choice.

**Parameters**: None

**Returns**:
- `str`: Valid menu choice ("1", "2", "3", "4", "5", or "6")

**Behavior**:
1. Read input with `input().strip()`
2. Validate choice is in ["1", "2", "3", "4", "5", "6"]
3. If invalid, display error message and retry (loop)
4. Return valid choice

**Example**:
```python
choice = interface.get_user_choice()
# User enters "7" → displays error, retries
# User enters "1" → returns "1"
```

**Maps to**: FR-009, FR-010

---

### display_tasks

**Signature**:
```python
def display_tasks(self, tasks: List[Task]) -> None:
```

**Purpose**: Display a formatted list of tasks.

**Parameters**:
- `tasks` (List[Task]): List of tasks to display

**Returns**: None

**Output** (to console):

**When tasks list is empty**:
```
No tasks found. Your todo list is empty.
```

**When tasks exist**:
```
Your Tasks:
[1] ☐ Buy groceries
    Description: Get milk and bread
[2] ☑ Prepare presentation
    Description: Slides for Monday meeting
[3] ☐ Call dentist
    Description: (none)
```

**Format Rules**:
- `[id]` prefix for each task
- `☐` for pending tasks (completed=False)
- `☑` for completed tasks (completed=True)
- Display description on next line (indented)
- Show "(none)" if description is empty

**Behavior**:
1. Check if tasks list is empty → display "No tasks" message
2. Otherwise, print "Your Tasks:" header
3. Iterate tasks and print formatted output
4. Include visual distinction for completed vs pending

**Maps to**: FR-003, FR-013, FR-015

---

### prompt_task_details

**Signature**:
```python
def prompt_task_details(self) -> dict:
```

**Purpose**: Prompt user for task title and description (for add/update operations).

**Parameters**: None

**Returns**:
- `dict`: `{"title": str, "description": str}`

**Behavior**:
1. Prompt for title: `"Enter task title: "`
2. Read and strip input
3. Validate title non-empty (if empty, display error and retry)
4. Prompt for description: `"Enter task description (optional, press Enter to skip): "`
5. Read and strip input (allow empty)
6. Return dict with title and description

**Example**:
```python
details = interface.prompt_task_details()
# User enters title: "Buy groceries"
# User enters description: "Get milk and bread"
# Returns: {"title": "Buy groceries", "description": "Get milk and bread"}
```

**Maps to**: FR-001, FR-002, FR-011

---

### prompt_task_id

**Signature**:
```python
def prompt_task_id(self) -> int:
```

**Purpose**: Prompt user for a task ID (for update/delete/toggle operations).

**Parameters**: None

**Returns**:
- `int`: Valid task ID entered by user

**Behavior**:
1. Prompt: `"Enter task ID: "`
2. Read and strip input
3. Validate input is a positive integer
4. If invalid, display error and retry (loop)
5. Return task ID as int

**Example**:
```python
task_id = interface.prompt_task_id()
# User enters "abc" → displays error, retries
# User enters "1" → returns 1
```

**Maps to**: FR-012

---

### display_message

**Signature**:
```python
def display_message(self, message: str, message_type: str = "info") -> None:
```

**Purpose**: Display a formatted message to the user.

**Parameters**:
- `message` (str): Message text to display
- `message_type` (str): Type of message ("success", "error", "info")

**Returns**: None

**Output** (to console):
- **success**: `✓ {message}` (green if terminal supports colors)
- **error**: `✗ {message}` (red if terminal supports colors)
- **info**: `ℹ {message}` (blue if terminal supports colors)

**Behavior**:
1. Prefix message with appropriate symbol
2. Print to console
3. Optional: Use ANSI color codes if supported

**Example**:
```python
interface.display_message("Task added successfully", "success")
# Output: ✓ Task added successfully

interface.display_message("Task not found", "error")
# Output: ✗ Task not found
```

**Maps to**: FR-006, FR-010

---

## Workflow Methods

These methods orchestrate complete user workflows by combining multiple operations.

### run_add_task_workflow

**Signature**:
```python
def run_add_task_workflow(self) -> None:
```

**Purpose**: Handle the complete workflow for adding a task.

**Behavior**:
1. Call `prompt_task_details()` to get title and description
2. Call `task_manager.add_task(title, description)`
3. Catch `ValueError` if title is empty
4. Display success or error message via `display_message()`

**Maps to**: User Story 1

---

### run_update_task_workflow

**Signature**:
```python
def run_update_task_workflow(self) -> None:
```

**Purpose**: Handle the complete workflow for updating a task.

**Behavior**:
1. Display all tasks via `display_tasks()`
2. Call `prompt_task_id()` to get task ID
3. Call `prompt_task_details()` to get new title and description
4. Call `task_manager.update_task(task_id, title, description)`
5. Display success or error message based on return value

**Maps to**: User Story 3

---

### run_delete_task_workflow

**Signature**:
```python
def run_delete_task_workflow(self) -> None:
```

**Purpose**: Handle the complete workflow for deleting a task.

**Behavior**:
1. Display all tasks via `display_tasks()`
2. Call `prompt_task_id()` to get task ID
3. Confirm deletion: `"Are you sure you want to delete this task? (y/n): "`
4. If confirmed, call `task_manager.delete_task(task_id)`
5. Display success or error message

**Maps to**: User Story 4

---

### run_toggle_complete_workflow

**Signature**:
```python
def run_toggle_complete_workflow(self) -> None:
```

**Purpose**: Handle the complete workflow for toggling task completion status.

**Behavior**:
1. Display all tasks via `display_tasks()`
2. Call `prompt_task_id()` to get task ID
3. Call `task_manager.toggle_complete(task_id)`
4. Display success or error message

**Maps to**: User Story 2

---

### run_view_tasks_workflow

**Signature**:
```python
def run_view_tasks_workflow(self) -> None:
```

**Purpose**: Handle the complete workflow for viewing all tasks.

**Behavior**:
1. Call `task_manager.get_all_tasks()`
2. Call `display_tasks(tasks)`

**Maps to**: User Story 1

---

## Input Validation

| Input | Validation | Error Handling |
|-------|------------|----------------|
| Menu choice | Must be "1"-"6" | Display error, retry |
| Task title | Non-empty after strip | Display error, retry |
| Task description | Any (allow empty) | N/A |
| Task ID | Positive integer | Display error, retry |
| Delete confirmation | "y" or "n" | Display error, retry |

---

## Error Messages

| Scenario | Message |
|----------|---------|
| Invalid menu choice | `"Invalid choice. Please enter a number between 1 and 6."` |
| Empty task title | `"Task title cannot be empty. Please try again."` |
| Invalid task ID format | `"Invalid input. Please enter a numeric task ID."` |
| Task not found | `"Task not found. Please check the task ID and try again."` |
| Task added | `"Task added successfully!"` |
| Task updated | `"Task updated successfully!"` |
| Task deleted | `"Task deleted successfully!"` |
| Task toggled | `"Task status updated!"` |

---

## Testing Requirements

### Unit Tests (`tests/unit/test_console_interface.py`)

1. **test_display_menu**: Verify menu is printed correctly (use capsys)
2. **test_get_user_choice_valid**: Verify valid choice is returned
3. **test_get_user_choice_invalid_then_valid**: Verify retry on invalid input
4. **test_display_tasks_empty**: Verify "No tasks" message displayed
5. **test_display_tasks_multiple**: Verify formatted task list displayed
6. **test_prompt_task_details_valid**: Verify dict returned with title/description
7. **test_prompt_task_details_empty_title_retry**: Verify retry on empty title
8. **test_prompt_task_id_valid**: Verify int returned
9. **test_prompt_task_id_invalid_retry**: Verify retry on non-numeric input
10. **test_display_message_success**: Verify success message format
11. **test_display_message_error**: Verify error message format

---

## Dependencies

- `services.task_manager.TaskManager`: For delegating business logic
- `models.task.Task`: For type annotations
- `typing.List`: For type annotations
- `builtins.input`: For reading user input
- `builtins.print`: For console output

---

**Contract Status**: ✅ Complete
