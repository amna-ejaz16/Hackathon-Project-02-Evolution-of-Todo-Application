# Research: Phase I - In-Memory Console Todo App

**Date**: 2026-01-02
**Phase**: 0 (Research & Decision Log)
**Status**: Complete

## Research Topics

This document captures research findings and decisions for Phase I implementation.

---

## 1. Python 3.13+ Best Practices for Console Applications

### Input Validation Patterns

**Finding**: Python 3.13+ continues to support robust input validation through try-except blocks and string methods.

**Best Practices**:
- Use `input().strip()` to handle whitespace
- Validate non-empty inputs: `if not title.strip(): raise ValueError()`
- Use try-except for type conversions: `int(choice)` wrapped in try-except
- Provide clear error messages immediately after invalid input

**Example Pattern**:
```python
def get_valid_choice(prompt: str, valid_options: list) -> str:
    while True:
        choice = input(prompt).strip()
        if choice in valid_options:
            return choice
        print(f"Invalid choice. Please select from {valid_options}")
```

**Decision**: Implement validation at ConsoleInterface layer with clear error messages and retry loops.

---

### Menu-Driven Interface Design

**Finding**: Console menu best practices emphasize clarity, numbered options, and visual separation.

**Best Practices**:
- Use clear section headers with decorative borders (`===`, `---`)
- Number options starting from 1 (not 0) for user-friendliness
- Provide descriptive option labels (not just "Option 1")
- Include an explicit "Exit" option
- Clear screen between operations (optional, use `os.system('clear')` or `os.system('cls')`)

**Example Pattern**:
```
=== Todo Application ===
1. View all tasks
2. Add new task
3. Update task
4. Delete task
5. Mark task as complete/incomplete
6. Exit

Choose an option (1-6): _
```

**Decision**: Use numbered menu with clear labels. Do NOT clear screen (preserve history for debugging). Display menu after every operation.

---

### Error Handling Strategies

**Finding**: Console apps should handle errors gracefully without crashing.

**Best Practices**:
- Catch exceptions at UI layer, not business logic layer
- Display user-friendly error messages
- Return to main menu after errors
- Log errors for debugging (use print for console apps)

**Example Pattern**:
```python
try:
    task_manager.delete_task(task_id)
    print("✓ Task deleted successfully")
except ValueError as e:
    print(f"✗ Error: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
# Continue to main menu
```

**Decision**: ConsoleInterface catches exceptions from TaskManager and displays friendly messages. Application never crashes; always returns to menu.

---

## 2. In-Memory Data Structure Selection

### List vs Dictionary for Task Storage

**Options Evaluated**:

1. **List of Task objects**: `tasks: List[Task]`
   - Pro: Maintains insertion order (creation order)
   - Pro: Simple iteration for display
   - Pro: Familiar pattern
   - Con: O(n) lookups by ID

2. **Dictionary (task_id → Task)**: `tasks: Dict[int, Task]`
   - Pro: O(1) lookups by ID
   - Pro: Easy to check existence
   - Con: Requires separate tracking of insertion order (Python 3.7+ dicts are ordered, but not ideal for this use case)

3. **List of dictionaries**: `tasks: List[dict]`
   - Pro: No class definition needed
   - Con: No type safety
   - Con: Harder to maintain

**Decision**: **List of Task objects** (Option 1)

**Rationale**:
- Simplicity trumps performance for Phase I (up to 1000 tasks, O(n) is acceptable)
- Maintains creation order naturally
- Type safety with dataclass
- Easy to evolve to database in Phase II (Task → SQLModel schema)

---

### Task Entity Design: Dataclass vs Class vs Dict

**Options Evaluated**:

1. **Dataclass** (Python 3.7+):
   ```python
   from dataclasses import dataclass
   from datetime import datetime

   @dataclass
   class Task:
       id: int
       title: str
       description: str = ""
       completed: bool = False
       created_at: datetime = None
   ```
   - Pro: Minimal boilerplate, automatic `__init__`, `__repr__`, `__eq__`
   - Pro: Type annotations built-in
   - Pro: Pythonic and modern
   - Con: Slightly less flexible than plain class

2. **Plain Class**:
   ```python
   class Task:
       def __init__(self, id, title, description="", completed=False):
           self.id = id
           self.title = title
           self.description = description
           self.completed = completed
           self.created_at = datetime.now()
   ```
   - Pro: More control over initialization
   - Con: More boilerplate code
   - Con: No automatic `__repr__`

3. **Dictionary**:
   ```python
   task = {"id": 1, "title": "Buy groceries", "description": "", "completed": False}
   ```
   - Pro: No class definition needed
   - Con: No type safety, error-prone

**Decision**: **Dataclass** (Option 1)

**Rationale**:
- Minimal boilerplate aligns with Constitution VIII (Simplicity)
- Type annotations improve code clarity and IDE support
- Built-in `__repr__` helps with debugging
- Modern Python best practice
- Easy to evolve to SQLModel in Phase II (both use similar syntax)

---

### ID Generation Strategies

**Options Evaluated**:

1. **Auto-incrementing integer counter**:
   ```python
   self.next_id = 1
   # On add_task:
   task_id = self.next_id
   self.next_id += 1
   ```
   - Pro: Simple, deterministic, user-friendly ("Task #3")
   - Pro: No external dependencies
   - Con: Not globally unique (fine for Phase I)

2. **UUID (Universally Unique Identifier)**:
   ```python
   import uuid
   task_id = str(uuid.uuid4())
   ```
   - Pro: Globally unique
   - Con: Long, hard for users to reference ("Task #a4f8-3c7d-...")
   - Con: Requires uuid library import

3. **Index-based (list index)**:
   ```python
   task_id = len(self.tasks)
   ```
   - Pro: Simplest
   - Con: IDs shift when tasks are deleted (fragile, confusing)

**Decision**: **Auto-incrementing integer counter** (Option 1)

**Rationale**:
- User-friendly: Easy to reference "Delete task #3"
- Deterministic: Same operations → same IDs (Constitution II)
- Simple: No external dependencies (Constitution VIII)
- Phase I appropriate: Global uniqueness not needed for in-memory, single-user app
- Evolvable: Can switch to database auto-increment in Phase II

---

## 3. Testing Strategy for Console Apps

### pytest Best Practices

**Finding**: pytest is the industry-standard testing framework for Python, with excellent support for console I/O testing.

**Best Practices**:
- Use fixtures for shared setup (e.g., `@pytest.fixture` for TaskManager instance)
- Use `capsys` fixture to capture stdout/stderr
- Use `monkeypatch` fixture to mock `input()`
- Organize tests by module (test_task.py, test_task_manager.py, etc.)
- Use descriptive test names: `test_add_task_with_valid_input()`

**Example**:
```python
def test_add_task_displays_success_message(capsys):
    # Given
    task_manager = TaskManager()
    interface = ConsoleInterface(task_manager)

    # When
    interface.add_task("Buy groceries", "Get milk and bread")

    # Then
    captured = capsys.readouterr()
    assert "Task added successfully" in captured.out
```

**Decision**: Use pytest with `capsys` and `monkeypatch` fixtures. Install pytest as dev dependency.

---

### Mocking Console I/O

**Finding**: pytest's `monkeypatch` fixture allows mocking `input()` for testing.

**Pattern**:
```python
def test_get_user_choice_returns_valid_choice(monkeypatch):
    # Mock input to return "1"
    monkeypatch.setattr('builtins.input', lambda _: "1")

    interface = ConsoleInterface(TaskManager())
    choice = interface.get_user_choice()

    assert choice == "1"
```

**Decision**: Use `monkeypatch.setattr('builtins.input', ...)` for mocking user input. Test validation logic with multiple mock inputs.

---

### Integration Test Patterns

**Finding**: Integration tests should validate full user workflows (end-to-end).

**Pattern**:
```python
def test_full_task_lifecycle():
    # Given: Fresh TaskManager
    tm = TaskManager()

    # When: Add task
    task = tm.add_task("Buy groceries", "Get milk")
    task_id = task.id

    # Then: Task exists
    assert tm.get_task(task_id) is not None

    # When: Mark complete
    tm.toggle_complete(task_id)

    # Then: Task is completed
    assert tm.get_task(task_id).completed is True

    # When: Delete task
    tm.delete_task(task_id)

    # Then: Task no longer exists
    assert tm.get_task(task_id) is None
```

**Decision**: Create `tests/integration/test_full_workflow.py` with end-to-end scenarios matching user stories from spec.md.

---

## 4. Code Organization Patterns

### Module Structure for Maintainability

**Finding**: Python projects should organize code by layer (models, services, cli) for clarity and separation of concerns.

**Pattern** (chosen for Phase I):
```
src/
├── models/
│   └── task.py          # Data models
├── services/
│   └── task_manager.py  # Business logic
├── cli/
│   └── console_interface.py  # User interface
└── main.py              # Entry point
```

**Alternatives**:
- Flat structure (`task.py`, `task_manager.py`, `console_interface.py`, `main.py` at root): Simpler but less scalable
- Feature-based (`features/tasks/`): Overkill for Phase I single feature

**Decision**: Use layer-based structure (models, services, cli) to enforce separation of concerns and prepare for Phase II evolution.

---

### Separation of Concerns Implementation

**Finding**: Clean architecture requires strict boundaries between layers.

**Principles**:
1. **Models** (`models/task.py`): Data structures only, no business logic
2. **Services** (`services/task_manager.py`): Business logic, no UI code
3. **CLI** (`cli/console_interface.py`): User interaction, no business logic
4. **Main** (`main.py`): Orchestration, minimal logic

**Dependencies**:
- Main → CLI, Services
- CLI → Services, Models
- Services → Models
- Models → (no dependencies)

**Decision**: Enforce dependency rules. Models are pure data. Services handle CRUD logic. CLI handles I/O. Main orchestrates.

---

### Preparing for Phase II Evolution

**Finding**: Phase I design should anticipate Phase II (web app with database).

**Evolution Path**:
- **Task model** (`models/task.py`) → SQLModel schema for database
- **TaskManager** (`services/task_manager.py`) → API service layer (FastAPI endpoints call TaskManager-like service)
- **ConsoleInterface** (`cli/console_interface.py`) → Replaced by Next.js frontend
- **main.py** → Replaced by FastAPI app

**Design Decisions to Enable Evolution**:
1. Use dataclass for Task (similar to SQLModel syntax)
2. Keep TaskManager stateless where possible (pass tasks list, don't store globally)
3. Define clear method contracts (add_task, get_task, etc.) that map to API endpoints
4. Avoid console-specific logic in TaskManager (keep it pure business logic)

**Decision**: Design Task entity and TaskManager to be reusable in Phase II. CLI is throwaway; models/services are evolvable.

---

## Summary of Key Decisions

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| Data Structure | List of Task objects | Simplicity, order preservation, type safety |
| Task Entity | Dataclass | Minimal boilerplate, Pythonic, evolvable to SQLModel |
| ID Generation | Auto-incrementing integer | User-friendly, deterministic, simple |
| Module Organization | Layer-based (models/services/cli) | Separation of concerns, testability, evolvability |
| Testing Framework | pytest with capsys/monkeypatch | Industry standard, excellent console I/O support |
| Input Validation | ConsoleInterface layer | Clear error messages, graceful recovery |
| Error Handling | Catch at UI layer, display friendly messages | Never crash, always return to menu |
| Phase II Prep | Reusable models/services, throwaway CLI | Enable smooth evolution to web app |

---

**Research Status**: ✅ Complete - Ready for Phase 1 design artifacts
