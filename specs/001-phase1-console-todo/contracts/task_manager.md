# Contract: TaskManager

**Module**: `src/services/task_manager.py`
**Date**: 2026-01-02
**Purpose**: Define the interface for task management business logic

## Overview

The TaskManager class provides CRUD (Create, Read, Update, Delete) operations for Task entities. It maintains in-memory state and enforces business rules from the specification.

---

## Class Definition

```python
from typing import List
from models.task import Task

class TaskManager:
    """Manages task CRUD operations in memory."""

    def __init__(self):
        """Initialize TaskManager with empty task list."""
        self.tasks: List[Task] = []
        self.next_id: int = 1
```

---

## Methods

### add_task

**Signature**:
```python
def add_task(self, title: str, description: str = "") -> Task:
```

**Purpose**: Create a new task and add it to the in-memory list.

**Parameters**:
- `title` (str): Task title (required, non-empty)
- `description` (str): Task description (optional, defaults to "")

**Returns**:
- `Task`: The newly created task object

**Raises**:
- `ValueError`: If title is empty or contains only whitespace

**Behavior**:
1. Validate `title` is non-empty (strip whitespace)
2. Create new Task with `id=next_id`, provided title/description, `completed=False`, `created_at=now()`
3. Append Task to `tasks` list
4. Increment `next_id`
5. Return Task object

**Example**:
```python
tm = TaskManager()
task = tm.add_task("Buy groceries", "Get milk and bread")
# task.id == 1
# task.completed == False
```

**Maps to**: FR-001, FR-002, FR-011, FR-012

---

### get_task

**Signature**:
```python
def get_task(self, task_id: int) -> Task | None:
```

**Purpose**: Retrieve a task by its ID.

**Parameters**:
- `task_id` (int): Unique identifier of the task

**Returns**:
- `Task`: Task object if found
- `None`: If no task with the given ID exists

**Raises**: None

**Behavior**:
1. Iterate through `tasks` list
2. Return task if `task.id == task_id`
3. Return `None` if not found

**Example**:
```python
task = tm.get_task(1)
if task:
    print(task.title)
else:
    print("Task not found")
```

**Maps to**: FR-003, FR-012

---

### get_all_tasks

**Signature**:
```python
def get_all_tasks(self) -> List[Task]:
```

**Purpose**: Retrieve all tasks in creation order.

**Parameters**: None

**Returns**:
- `List[Task]`: List of all tasks (may be empty)

**Raises**: None

**Behavior**:
1. Return copy of `tasks` list (to prevent external mutation)

**Example**:
```python
all_tasks = tm.get_all_tasks()
for task in all_tasks:
    print(f"[{task.id}] {task.title}")
```

**Maps to**: FR-003, FR-015

---

### update_task

**Signature**:
```python
def update_task(self, task_id: int, title: str | None = None, description: str | None = None) -> bool:
```

**Purpose**: Update title and/or description of an existing task.

**Parameters**:
- `task_id` (int): Unique identifier of the task
- `title` (str | None): New title (if provided, must be non-empty)
- `description` (str | None): New description (if provided)

**Returns**:
- `True`: If task was found and updated
- `False`: If task was not found

**Raises**:
- `ValueError`: If provided title is empty or whitespace-only

**Behavior**:
1. Find task with `task.id == task_id`
2. If not found, return `False`
3. If `title` provided, validate non-empty and update `task.title`
4. If `description` provided, update `task.description`
5. Return `True`

**Example**:
```python
success = tm.update_task(1, title="Buy groceries and pharmacy items")
if success:
    print("Task updated")
else:
    print("Task not found")
```

**Maps to**: FR-005, FR-006, FR-011

---

### delete_task

**Signature**:
```python
def delete_task(self, task_id: int) -> bool:
```

**Purpose**: Remove a task from the list.

**Parameters**:
- `task_id` (int): Unique identifier of the task

**Returns**:
- `True`: If task was found and deleted
- `False`: If task was not found

**Raises**: None

**Behavior**:
1. Find task with `task.id == task_id`
2. If found, remove from `tasks` list and return `True`
3. If not found, return `False`
4. **Note**: `next_id` is NOT decremented (IDs are never reused)

**Example**:
```python
success = tm.delete_task(1)
if success:
    print("Task deleted")
else:
    print("Task not found")
```

**Maps to**: FR-007

---

### toggle_complete

**Signature**:
```python
def toggle_complete(self, task_id: int) -> bool:
```

**Purpose**: Toggle the completion status of a task (pending ↔ completed).

**Parameters**:
- `task_id` (int): Unique identifier of the task

**Returns**:
- `True`: If task was found and toggled
- `False`: If task was not found

**Raises**: None

**Behavior**:
1. Find task with `task.id == task_id`
2. If found, set `task.completed = not task.completed` and return `True`
3. If not found, return `False`

**Example**:
```python
success = tm.toggle_complete(1)
if success:
    print("Task status toggled")
else:
    print("Task not found")
```

**Maps to**: FR-004, FR-013

---

## State Management

### Invariants

1. **ID Uniqueness**: All tasks in `tasks` list have unique `id` values
2. **ID Monotonicity**: `next_id` only increments (never decrements)
3. **Order Preservation**: Tasks maintain insertion order in `tasks` list

### State Transitions

```
Initial State: tasks=[], next_id=1

add_task("Task A") → tasks=[Task(id=1)], next_id=2
add_task("Task B") → tasks=[Task(id=1), Task(id=2)], next_id=3
delete_task(1) → tasks=[Task(id=2)], next_id=3 (unchanged)
add_task("Task C") → tasks=[Task(id=2), Task(id=3)], next_id=4
```

---

## Error Handling

| Error Condition | Method | Behavior |
|----------------|--------|----------|
| Empty title | `add_task`, `update_task` | Raise `ValueError` |
| Task not found | `get_task` | Return `None` |
| Task not found | `update_task`, `delete_task`, `toggle_complete` | Return `False` |

---

## Testing Requirements

### Unit Tests (`tests/unit/test_task_manager.py`)

1. **test_add_task_with_valid_input**: Verify task is added with correct attributes
2. **test_add_task_with_empty_title**: Verify ValueError is raised
3. **test_get_task_existing**: Verify correct task is returned
4. **test_get_task_nonexistent**: Verify None is returned
5. **test_get_all_tasks_empty**: Verify empty list when no tasks
6. **test_get_all_tasks_multiple**: Verify all tasks returned in order
7. **test_update_task_title**: Verify title is updated
8. **test_update_task_description**: Verify description is updated
9. **test_update_task_nonexistent**: Verify False is returned
10. **test_delete_task_existing**: Verify task is removed
11. **test_delete_task_nonexistent**: Verify False is returned
12. **test_toggle_complete_pending_to_complete**: Verify status changes
13. **test_toggle_complete_complete_to_pending**: Verify status toggles back
14. **test_id_uniqueness**: Verify all task IDs are unique
15. **test_id_not_reused_after_deletion**: Verify deleted IDs are not reassigned

---

## Dependencies

- `models.task.Task`: Task entity
- `datetime`: For Task creation timestamps
- `typing.List`: For type annotations

---

**Contract Status**: ✅ Complete
