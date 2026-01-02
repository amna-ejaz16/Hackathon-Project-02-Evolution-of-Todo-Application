# Contract: Application Runner (main.py)

**Module**: `src/main.py`
**Date**: 2026-01-02
**Purpose**: Define the entry point and main application loop

## Overview

The Application Runner is the entry point for the Todo console application. It initializes dependencies (TaskManager, ConsoleInterface), runs the main event loop, and orchestrates user workflows based on menu choices.

---

## Module Structure

```python
from services.task_manager import TaskManager
from cli.console_interface import ConsoleInterface

def main() -> None:
    """Main application entry point and event loop."""
    # Implementation

if __name__ == "__main__":
    main()
```

---

## Main Function

### main

**Signature**:
```python
def main() -> None:
```

**Purpose**: Initialize the application and run the main event loop.

**Parameters**: None

**Returns**: None

**Behavior**:

1. **Initialization Phase**:
   ```python
   task_manager = TaskManager()
   console_interface = ConsoleInterface(task_manager)
   ```
   - Create TaskManager instance
   - Create ConsoleInterface instance with TaskManager dependency

2. **Welcome Message**:
   ```python
   print("\n" + "="*50)
   print("Welcome to the Todo Application (Phase I)")
   print("All data is stored in memory (not persistent)")
   print("="*50 + "\n")
   ```
   - Display welcome message
   - Inform user about in-memory storage limitation

3. **Main Event Loop**:
   ```python
   while True:
       console_interface.display_menu()
       choice = console_interface.get_user_choice()

       if choice == "1":
           console_interface.run_view_tasks_workflow()
       elif choice == "2":
           console_interface.run_add_task_workflow()
       elif choice == "3":
           console_interface.run_update_task_workflow()
       elif choice == "4":
           console_interface.run_delete_task_workflow()
       elif choice == "5":
           console_interface.run_toggle_complete_workflow()
       elif choice == "6":
           print("\nThank you for using the Todo Application!")
           break

       print()  # Blank line for readability
   ```
   - Display menu
   - Get user choice
   - Route to appropriate workflow based on choice
   - Exit loop when user selects "6"

4. **Exit**:
   - Display goodbye message
   - Exit application (return from main)

---

## Control Flow Diagram

```
┌─────────────────────────────────────────────────┐
│ Start: main()                                   │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ Initialize: TaskManager, ConsoleInterface      │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ Display: Welcome message                        │
└─────────────────────────────────────────────────┘
                     │
                     ▼
           ┌─────────────────┐
           │  Display Menu   │
           └─────────────────┘
                     │
                     ▼
           ┌─────────────────┐
           │ Get User Choice │
           └─────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
   Choice == "1"            Choice == "2"
   View Tasks               Add Task
        │                         │
        ▼                         ▼
   run_view_tasks_workflow   run_add_task_workflow
        │                         │
        └─────────┬───────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
   Choice == "3"       Choice == "4"
   Update Task         Delete Task
        │                   │
        ▼                   ▼
   run_update_task_workflow  run_delete_task_workflow
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
   Choice == "5"       Choice == "6"
   Toggle Complete     Exit
        │                   │
        ▼                   ▼
   run_toggle_complete   Display goodbye
   _workflow             Exit loop
        │                   │
        └─────────┬─────────┘
                  │
                  ▼ (if not exit)
           Loop back to Display Menu
```

---

## Example Execution Flow

### Successful Add → View → Exit

```
Welcome to the Todo Application (Phase I)
All data is stored in memory (not persistent)

=== Todo Application ===
1. View all tasks
2. Add new task
3. Update task
4. Delete task
5. Mark task as complete/incomplete
6. Exit

Choose an option (1-6): 2
Enter task title: Buy groceries
Enter task description (optional, press Enter to skip): Get milk and bread
✓ Task added successfully!

=== Todo Application ===
1. View all tasks
2. Add new task
3. Update task
4. Delete task
5. Mark task as complete/incomplete
6. Exit

Choose an option (1-6): 1
Your Tasks:
[1] ☐ Buy groceries
    Description: Get milk and bread

=== Todo Application ===
1. View all tasks
2. Add new task
3. Update task
4. Delete task
5. Mark task as complete/incomplete
6. Exit

Choose an option (1-6): 6

Thank you for using the Todo Application!
```

---

## Error Handling

### Global Exception Handling

```python
def main() -> None:
    """Main application entry point and event loop."""
    try:
        # Application logic
        ...
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        print("Application will now exit.")
```

**Behavior**:
- Catch `KeyboardInterrupt` (Ctrl+C) and exit gracefully
- Catch unexpected exceptions and display error before exit
- Ensure application never crashes without user feedback

---

## Dependency Injection

The main function uses constructor injection for dependencies:

```python
# main.py creates TaskManager
task_manager = TaskManager()

# main.py injects TaskManager into ConsoleInterface
console_interface = ConsoleInterface(task_manager)
```

This enables:
- **Testability**: Can inject mock TaskManager for testing
- **Separation of Concerns**: main.py orchestrates, doesn't implement logic
- **Flexibility**: Easy to swap implementations in future phases

---

## Testing Requirements

### Integration Tests (`tests/integration/test_full_workflow.py`)

1. **test_add_and_view_task**: Simulate add task → view tasks workflow
2. **test_add_update_view**: Simulate add → update → view workflow
3. **test_add_toggle_view**: Simulate add → toggle complete → view workflow
4. **test_add_delete_view**: Simulate add → delete → view workflow
5. **test_full_lifecycle**: Simulate create → view → update → toggle → delete
6. **test_exit_choice**: Verify exit choice terminates loop gracefully

**Testing Approach**:
- Use `monkeypatch` to mock `input()` with predefined sequence
- Use `capsys` to capture and verify output
- Simulate full user sessions

**Example**:
```python
def test_add_and_view_task(monkeypatch, capsys):
    # Mock user input sequence: 2 (add) → "Buy groceries" → "" → 1 (view) → 6 (exit)
    inputs = iter(["2", "Buy groceries", "", "1", "6"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    # Run main
    main()

    # Verify output
    captured = capsys.readouterr()
    assert "Task added successfully" in captured.out
    assert "[1] ☐ Buy groceries" in captured.out
    assert "Thank you for using the Todo Application" in captured.out
```

---

## Performance Considerations

### Startup Time
- **Expected**: < 100ms (no heavy initialization)
- **Measurement**: Time from `python src/main.py` to first menu display

### Response Time per Operation
- **Expected**: < 50ms for all operations (in-memory only)
- **Worst Case**: O(n) for task lookups, acceptable for up to 1000 tasks

---

## Future Evolution to Phase II

### Phase I (Console App)
```python
# main.py
def main():
    task_manager = TaskManager()  # In-memory
    console_interface = ConsoleInterface(task_manager)
    # Run event loop
```

### Phase II (Web App)
```python
# main.py (FastAPI)
from fastapi import FastAPI
from services.task_service import TaskService
from db import get_session

app = FastAPI()

@app.get("/tasks")
def get_tasks(session: Session = Depends(get_session)):
    service = TaskService(session)
    return service.get_all_tasks()
```

**Migration Notes**:
- main.py is fully replaced (console → web server)
- TaskManager logic → TaskService (database-backed)
- ConsoleInterface → Next.js frontend
- Core business logic (add, update, delete, toggle) remains similar

---

## Validation Against Success Criteria

| Success Criterion | How main.py Ensures It |
|-------------------|------------------------|
| SC-004: All 5 operations accessible from menu | Event loop routes all 6 menu choices |
| SC-006: Clear feedback for every action | Workflows display messages via ConsoleInterface |
| SC-007: Full task lifecycle works | Event loop allows sequential operations |
| SC-008: Graceful edge case handling | try-except around main loop |

---

## Dependencies

- `services.task_manager.TaskManager`: Business logic
- `cli.console_interface.ConsoleInterface`: User interaction
- `builtins.print`: For welcome/goodbye messages

---

**Contract Status**: ✅ Complete
