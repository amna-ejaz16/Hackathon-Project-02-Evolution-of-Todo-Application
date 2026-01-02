# Todo Application - Phase I: In-Memory Console Application

A simple, in-memory console-based todo application built with Python 3.13+ following Spec-Driven Development principles.

## Features

- ✅ **Create Tasks**: Add new tasks with title and optional description
- ✅ **View Tasks**: Display all tasks with completion status
- ✅ **Update Tasks**: Modify task titles and descriptions
- ✅ **Delete Tasks**: Remove tasks with confirmation prompt
- ✅ **Mark Complete**: Toggle tasks between complete and incomplete states

## Prerequisites

- Python 3.13 or higher
- No external dependencies required (uses Python standard library only)

## Installation

1. Clone or download this repository
2. Ensure Python 3.13+ is installed:
   ```bash
   python --version
   ```

## Running the Application

Run the application from the project root directory:

```bash
PYTHONPATH=src python src/main.py
```

Or on Windows:
```cmd
set PYTHONPATH=src && python src/main.py
```

## Usage

Once the application starts, you'll see a main menu with 6 options:

```
=== Todo Application ===
1. View all tasks
2. Add new task
3. Update task
4. Delete task
5. Mark task as complete/incomplete
6. Exit
```

### Example Workflow

1. **Add a task**: Select option 2, enter title and optional description
2. **View tasks**: Select option 1 to see all tasks with ☐ (pending) or ☑ (completed) status
3. **Mark complete**: Select option 5, enter task ID to toggle completion
4. **Update task**: Select option 3, enter task ID and new details
5. **Delete task**: Select option 4, enter task ID and confirm with 'yes'
6. **Exit**: Select option 6 to quit

## Important Notes

⚠️ **In-Memory Storage**: All tasks are stored in memory only. When you exit the application, all data will be lost. This is by design for Phase I.

## Testing

Run the automated test suite:

```bash
PYTHONPATH=src python test_main_manual.py
```

All tests should pass with the message:
```
✓ ALL TESTS PASSED!
The application is ready for use!
```

## Project Structure

```
.
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py          # Task entity (dataclass)
│   ├── services/
│   │   ├── __init__.py
│   │   └── task_manager.py  # Business logic (CRUD operations)
│   ├── cli/
│   │   ├── __init__.py
│   │   └── console_interface.py  # User interface
│   └── main.py              # Application entry point
├── tests/
│   ├── unit/
│   └── integration/
├── specs/
│   └── 001-phase1-console-todo/
│       ├── spec.md          # Feature specification
│       ├── plan.md          # Architecture plan
│       └── tasks.md         # Implementation tasks
├── test_main_manual.py      # Automated test suite
└── README.md
```

## Architecture

The application follows a three-layer architecture:

1. **Models Layer** (`src/models/`): Data structures (Task entity)
2. **Services Layer** (`src/services/`): Business logic (TaskManager)
3. **CLI Layer** (`src/cli/`): User interface (ConsoleInterface)

## Success Criteria

All success criteria from the specification have been validated:

- ✅ **SC-001**: Users can create a new task in under 10 seconds
- ✅ **SC-002**: Users can view task list with a single menu selection
- ✅ **SC-003**: Completed tasks visually distinguished from pending tasks
- ✅ **SC-004**: All 5 operations accessible from main menu
- ✅ **SC-005**: Task state maintained correctly throughout session
- ✅ **SC-006**: Clear feedback for every user action
- ✅ **SC-007**: Full task lifecycle works without errors
- ✅ **SC-008**: Edge cases handled gracefully

## Future Phases

This is Phase I of a multi-phase evolution:

- **Phase II**: Web interface with persistent database storage (Next.js, FastAPI, Neon DB)
- **Phase III**: AI-powered chatbot for natural language task management
- **Phase IV**: Kubernetes deployment for scalability
- **Phase V**: Event-driven architecture with Kafka and cloud deployment

## License

This project is part of "The Evolution of Todo" educational series demonstrating Spec-Driven Development from console to cloud-native AI.
