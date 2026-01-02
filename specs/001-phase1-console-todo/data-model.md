# Data Model: Phase I - In-Memory Console Todo App

**Date**: 2026-01-02
**Phase**: 1 (Design)
**Status**: Complete

## Overview

This document defines the data model for Phase I of the Todo application. The model is designed to be simple, type-safe, and evolvable to Phase II (database-backed web app).

---

## Task Entity

The core entity representing a single todo item.

### Attributes

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | `int` | Yes | Auto-generated | Unique identifier for the task (auto-incrementing) |
| `title` | `str` | Yes | N/A | Brief description of the task (non-empty) |
| `description` | `str` | No | `""` | Detailed description of the task (optional) |
| `completed` | `bool` | No | `False` | Completion status (True = complete, False = pending) |
| `created_at` | `datetime` | Yes | Auto-generated | Timestamp when the task was created |

### Validation Rules

From spec.md Functional Requirements:

- **FR-011**: Title MUST NOT be empty (validated by TaskManager.add_task)
- **FR-012**: ID MUST be unique (enforced by auto-incrementing counter)
- **FR-002**: Description is optional (defaults to empty string)

### Constraints

- **Uniqueness**: `id` must be unique across all tasks in the list
- **Immutability**: `id` and `created_at` should not change after creation
- **Mutability**: `title`, `description`, and `completed` can be updated

### State Transitions

```
                 add_task()
    [None] ─────────────────► [Pending Task]
                                    │
                                    │ toggle_complete()
                                    ▼
                              [Completed Task]
                                    │
                                    │ toggle_complete()
                                    ▼
                              [Pending Task]
                                    │
                                    │ delete_task()
                                    ▼
                                 [Deleted]
```

### Python Implementation

Using Python dataclass for type safety and minimal boilerplate:

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Task:
    """Represents a single todo item."""
    id: int
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate task after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Task title cannot be empty")
```

### Example Instances

**Valid Task**:
```python
Task(id=1, title="Buy groceries", description="Get milk and bread", completed=False, created_at=datetime.now())
```

**Minimal Task** (description optional):
```python
Task(id=2, title="Call dentist")
```

**Completed Task**:
```python
Task(id=3, title="Prepare presentation", description="Slides for Monday", completed=True, created_at=datetime.now())
```

---

## TaskManager State

The TaskManager service maintains the application state in memory.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `tasks` | `List[Task]` | In-memory list of all tasks (ordered by creation) |
| `next_id` | `int` | Counter for generating unique task IDs (starts at 1) |

### State Invariants

- **ID Uniqueness**: All tasks in `tasks` list must have unique `id` values
- **ID Monotonicity**: `next_id` always increments (never decrements), even after deletions
- **Order Preservation**: Tasks in `tasks` list maintain insertion order (creation order)

### Python Implementation

```python
class TaskManager:
    """Manages task CRUD operations in memory."""

    def __init__(self):
        """Initialize TaskManager with empty task list."""
        self.tasks: List[Task] = []
        self.next_id: int = 1

    # Methods defined in contracts/task_manager.md
```

### State Evolution Example

```python
# Initial state
tm = TaskManager()
# tasks = []
# next_id = 1

# After adding first task
task1 = tm.add_task("Buy groceries")
# tasks = [Task(id=1, title="Buy groceries", ...)]
# next_id = 2

# After adding second task
task2 = tm.add_task("Call dentist")
# tasks = [Task(id=1, ...), Task(id=2, ...)]
# next_id = 3

# After deleting first task
tm.delete_task(1)
# tasks = [Task(id=2, ...)]
# next_id = 3 (unchanged - IDs never reused)

# After adding third task
task3 = tm.add_task("Prepare presentation")
# tasks = [Task(id=2, ...), Task(id=3, ...)]
# next_id = 4
```

---

## Relationships

**Phase I (In-Memory)**:
- One-to-Many: TaskManager → Tasks (TaskManager contains many Tasks)
- No inter-task relationships (tasks are independent)

**Phase II Evolution (Database)**:
- Task entity will map to `tasks` table in PostgreSQL
- `id` will become primary key (auto-incrementing)
- TaskManager will become API service layer (FastAPI)
- May add User entity with one-to-many relationship to Tasks

---

## Data Flow

### Create Task Flow
```
User Input → ConsoleInterface.prompt_task_details()
    → TaskManager.add_task(title, description)
    → Create Task(id=next_id, ...)
    → Append to tasks list
    → Increment next_id
    → Return Task object
```

### Read Task Flow
```
User Input (task_id) → ConsoleInterface.prompt_task_id()
    → TaskManager.get_task(task_id)
    → Iterate tasks list
    → Return Task if found, else None
```

### Update Task Flow
```
User Input → ConsoleInterface.prompt_task_id() + prompt_task_details()
    → TaskManager.update_task(task_id, title, description)
    → Find task in list
    → Mutate task.title and/or task.description
    → Return True if found, else False
```

### Delete Task Flow
```
User Input (task_id) → ConsoleInterface.prompt_task_id()
    → TaskManager.delete_task(task_id)
    → Find and remove task from list
    → Return True if found, else False
```

### Toggle Complete Flow
```
User Input (task_id) → ConsoleInterface.prompt_task_id()
    → TaskManager.toggle_complete(task_id)
    → Find task in list
    → Mutate task.completed = not task.completed
    → Return True if found, else False
```

---

## Schema Evolution to Phase II

### Phase I (In-Memory)
```python
@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
```

### Phase II (Database with SQLModel)
```python
from sqlmodel import Field, SQLModel
from datetime import datetime

class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: str = ""
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    # New fields for Phase II:
    # user_id: int = Field(foreign_key="users.id")  # Multi-user support
```

**Migration Notes**:
- Dataclass → SQLModel is straightforward (similar syntax)
- `id: int` → `id: int | None = Field(primary_key=True)` (database handles auto-increment)
- Add `table=True` to enable database mapping
- Add indexes as needed (`Field(index=True)`)

---

## Validation Summary

| Rule | Enforced By | Error Handling |
|------|-------------|----------------|
| Title non-empty | TaskManager.add_task() | Raise ValueError |
| ID uniqueness | TaskManager (auto-increment) | Guaranteed by design |
| Description optional | Task dataclass | Default to "" |
| Valid task_id for operations | TaskManager methods | Return False or None |

---

**Data Model Status**: ✅ Complete - Ready for contract definition
