# Quickstart: Phase I - In-Memory Console Todo App

**Date**: 2026-01-02
**Audience**: End users and developers
**Purpose**: Instructions for running and using the Todo application

---

## Prerequisites

- **Python**: Version 3.13 or higher
- **Operating System**: Any OS with Python 3.13+ (Linux, Windows, macOS)
- **Terminal/Console**: Command-line interface

### Check Python Version

```bash
python --version
# Expected output: Python 3.13.x or higher
```

If Python 3.13+ is not installed:
- **Linux/macOS**: Use package manager (apt, brew, etc.) or download from [python.org](https://www.python.org/downloads/)
- **Windows**: Download installer from [python.org](https://www.python.org/downloads/)

---

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd The-Evolution-of-Todo-Application
```

### 2. Verify Project Structure

```bash
ls -R src/
# Expected output:
# src/:
# main.py  models/  services/  cli/
#
# src/models/:
# task.py
#
# src/services/:
# task_manager.py
#
# src/cli/:
# console_interface.py
```

### 3. No External Dependencies Required

Phase I uses only Python standard library. No `pip install` required.

---

## Running the Application

### Start the Application

```bash
python src/main.py
```

### Expected Output

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

Choose an option (1-6):
```

---

## Using the Application

### Main Menu Options

The application provides 6 menu options:

1. **View all tasks**: Display all tasks in your list
2. **Add new task**: Create a new todo item
3. **Update task**: Modify an existing task's title or description
4. **Delete task**: Remove a task from the list
5. **Mark task as complete/incomplete**: Toggle task completion status
6. **Exit**: Close the application

---

## Common Workflows

### Workflow 1: Add and View Tasks

1. **Start application**: `python src/main.py`
2. **Select option 2** (Add new task)
3. **Enter task title**: `Buy groceries`
4. **Enter description** (optional): `Get milk, bread, and eggs`
5. **See confirmation**: `✓ Task added successfully!`
6. **Select option 1** (View all tasks)
7. **See your task**:
   ```
   Your Tasks:
   [1] ☐ Buy groceries
       Description: Get milk, bread, and eggs
   ```

---

### Workflow 2: Mark Task as Complete

1. **Select option 1** (View all tasks) to see task IDs
2. **Select option 5** (Mark task as complete/incomplete)
3. **Enter task ID**: `1`
4. **See confirmation**: `✓ Task status updated!`
5. **Select option 1** (View all tasks) to verify:
   ```
   Your Tasks:
   [1] ☑ Buy groceries
       Description: Get milk, bread, and eggs
   ```
   (Note: `☑` indicates completed task)

---

### Workflow 3: Update Task Details

1. **Select option 1** (View all tasks) to see task IDs
2. **Select option 3** (Update task)
3. **Enter task ID**: `1`
4. **Enter new title**: `Buy groceries and pharmacy items`
5. **Enter new description**: `Get milk, bread, eggs, and aspirin`
6. **See confirmation**: `✓ Task updated successfully!`

---

### Workflow 4: Delete Task

1. **Select option 1** (View all tasks) to see task IDs
2. **Select option 4** (Delete task)
3. **Enter task ID**: `1`
4. **Confirm deletion**: `y`
5. **See confirmation**: `✓ Task deleted successfully!`

---

### Workflow 5: Exit Application

1. **Select option 6** (Exit)
2. **See goodbye message**: `Thank you for using the Todo Application!`
3. **Application terminates**

---

## Input Guidelines

### Valid Inputs

- **Menu choices**: Enter numbers `1` through `6`
- **Task titles**: Any non-empty text (whitespace-only titles are rejected)
- **Task descriptions**: Any text (including empty - just press Enter to skip)
- **Task IDs**: Positive integers corresponding to existing tasks
- **Confirmations**: `y` (yes) or `n` (no)

### Input Validation

The application validates all inputs and provides helpful error messages:

**Example: Invalid menu choice**
```
Choose an option (1-6): 9
✗ Invalid choice. Please enter a number between 1 and 6.
Choose an option (1-6): 1
```

**Example: Empty task title**
```
Enter task title:
✗ Task title cannot be empty. Please try again.
Enter task title: Buy groceries
```

**Example: Invalid task ID**
```
Enter task ID: abc
✗ Invalid input. Please enter a numeric task ID.
Enter task ID: 1
```

---

## Task Display Format

### Pending Task
```
[1] ☐ Buy groceries
    Description: Get milk and bread
```
- `[1]`: Task ID
- `☐`: Pending status (not completed)
- `Buy groceries`: Task title
- `Description: ...`: Task description (or "(none)" if empty)

### Completed Task
```
[2] ☑ Prepare presentation
    Description: Slides for Monday meeting
```
- `☑`: Completed status

---

## Important Notes

### Data Persistence

⚠️ **WARNING**: All data is stored in memory only. When you exit the application, **all tasks are lost**.

This is by design for Phase I. Persistent storage will be added in Phase II.

### Session Scope

- Tasks exist only while the application is running
- Restarting the application starts with an empty task list
- Task IDs start at 1 with each new session

### Task ID Behavior

- Task IDs are auto-incremented (1, 2, 3, ...)
- Deleted task IDs are **never reused** within a session
- Example:
  ```
  Add task → ID 1
  Add task → ID 2
  Delete task 1
  Add task → ID 3 (not ID 1)
  ```

---

## Troubleshooting

### Issue: "python: command not found"

**Solution**: Python is not installed or not in PATH. Install Python 3.13+ and add to PATH.

### Issue: "ModuleNotFoundError: No module named 'models'"

**Solution**: Ensure you're running the command from the repository root, not from `src/` directory:
```bash
# Wrong:
cd src && python main.py

# Correct:
python src/main.py
```

### Issue: Application crashes on input

**Solution**: This should not happen. If it does, please report as a bug. The application should handle all invalid inputs gracefully.

### Issue: Tasks not displaying

**Solution**: Verify you've added tasks first (option 2). If the list is empty, you'll see:
```
No tasks found. Your todo list is empty.
```

---

## Testing the Application

### Manual Testing Checklist

Use this checklist to verify all functionality works:

- [ ] **Add task**: Can create a task with title and description
- [ ] **Add task (title only)**: Can create a task with title, skipping description
- [ ] **View empty list**: Displays "No tasks" message when list is empty
- [ ] **View tasks**: Displays all tasks with IDs, titles, descriptions, and status
- [ ] **Mark complete**: Can mark a pending task as complete (☐ → ☑)
- [ ] **Mark incomplete**: Can toggle a completed task back to pending (☑ → ☐)
- [ ] **Update title**: Can update a task's title
- [ ] **Update description**: Can update a task's description
- [ ] **Delete task**: Can delete a task and it no longer appears in list
- [ ] **Invalid menu choice**: Displays error and retries
- [ ] **Empty task title**: Displays error and retries
- [ ] **Invalid task ID**: Displays error and retries
- [ ] **Nonexistent task ID**: Displays "Task not found" message
- [ ] **Exit**: Application terminates gracefully with goodbye message

---

## Running Automated Tests

### Install pytest (for testing only)

```bash
pip install pytest
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific module
pytest tests/unit/test_task_manager.py
```

### Expected Output

```
===================== test session starts ======================
collected 25 items

tests/unit/test_task.py .....                           [ 20%]
tests/unit/test_task_manager.py ..........              [ 60%]
tests/unit/test_console_interface.py .....              [ 80%]
tests/integration/test_full_workflow.py .....           [100%]

===================== 25 passed in 0.50s =======================
```

---

## Next Steps

After verifying Phase I works correctly:

1. **Review Code**: Explore `src/` directory to understand the architecture
2. **Read Contracts**: See `specs/001-phase1-console-todo/contracts/` for API documentation
3. **Phase II Preview**: Phase II will add web interface and database persistence
4. **Contribute**: See `specs/001-phase1-console-todo/tasks.md` for implementation tasks

---

## Support

For issues or questions:
- **Specification**: See `specs/001-phase1-console-todo/spec.md`
- **Architecture**: See `specs/001-phase1-console-todo/plan.md`
- **Contracts**: See `specs/001-phase1-console-todo/contracts/`

---

**Quickstart Status**: ✅ Complete - Ready for users
