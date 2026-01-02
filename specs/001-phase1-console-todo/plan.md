# Implementation Plan: Phase I - In-Memory Console Todo App

**Branch**: `001-phase1-console-todo` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-phase1-console-todo/spec.md`

**Note**: This plan defines the architecture and implementation approach for Phase I of the Evolution of Todo project.

## Summary

Build an in-memory Python console application that implements core todo functionality (add, delete, update, view, mark complete). The application follows a three-layer architecture: Task Manager (business logic), Console Interface (user interaction), and Application Runner (orchestration). All data is stored in memory using Python data structures. The design prioritizes simplicity, testability, and clean separation of concerns to enable seamless evolution to Phase II (web application).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Standard library only (no external packages)
**Storage**: In-memory data structures (list of dictionaries or custom Task objects)
**Testing**: pytest for unit and integration testing
**Target Platform**: Any OS with Python 3.13+ (Linux, Windows, macOS)
**Project Type**: Single project (console application)
**Performance Goals**: Instant response for all operations (< 100ms for task lists up to 1000 items)
**Constraints**: No external dependencies, no persistent storage, synchronous operations only
**Scale/Scope**: Single-user, session-scoped, up to 1000 tasks per session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Specification First
- **Status**: PASS
- **Evidence**: Complete spec.md created and validated before planning phase

### ✅ II. Deterministic Behavior
- **Status**: PASS
- **Evidence**: All operations use in-memory data structures with predictable state transitions. Same inputs produce same outputs.

### ✅ III. Incremental Evolution
- **Status**: PASS
- **Evidence**: Phase I establishes foundation for Phase II (web app). Architecture designed for evolution (Task entity and operations will map to API/database).

### ✅ IV. Separation of Concerns
- **Status**: PASS
- **Evidence**: Three distinct layers: Task Manager (business logic), Console Interface (presentation), Application Runner (orchestration). Each layer independently testable.

### ✅ V. Testability (NON-NEGOTIABLE)
- **Status**: PASS
- **Evidence**: pytest-based testing strategy. Each module (task_manager, console_interface, main) can be unit tested. Integration tests for full workflows.

### ✅ VI. Observability
- **Status**: PASS
- **Evidence**: Console output provides visibility into all operations. Error messages for invalid operations. Success/failure feedback for every action.

### ✅ VII. AI Constraint and Explainability
- **Status**: N/A (Phase I)
- **Evidence**: No AI components in Phase I. Principle applies to Phase III.

### ✅ VIII. Simplicity and YAGNI
- **Status**: PASS
- **Evidence**: Minimal design with no speculative features. Standard library only. Simple data structures (list/dict). No premature optimization.

### Phase I Constraints Check
- **Technology**: ✅ Python 3.13+
- **Storage**: ✅ In-memory data structures only
- **Interface**: ✅ CLI (Console-based, text I/O)
- **Constraints**: ✅ No external databases or APIs, all operations synchronous
- **Focus**: ✅ Correctness, simplicity, spec completeness

**Gate Decision**: ✅ **APPROVED** - All constitution principles satisfied. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase1-console-todo/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output - Python best practices
├── data-model.md        # Phase 1 output - Task entity design
├── quickstart.md        # Phase 1 output - How to run the app
├── contracts/           # Phase 1 output - Module interface contracts
│   ├── task_manager.md  # TaskManager class/module contract
│   ├── console_interface.md  # ConsoleInterface contract
│   └── main.md          # Application runner contract
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
src/
├── models/
│   └── task.py          # Task entity (dataclass or class)
├── services/
│   └── task_manager.py  # TaskManager - business logic for CRUD operations
├── cli/
│   └── console_interface.py  # ConsoleInterface - menu display, input handling
└── main.py              # Application entry point and main loop

tests/
├── unit/
│   ├── test_task.py                 # Task model tests
│   ├── test_task_manager.py         # TaskManager business logic tests
│   └── test_console_interface.py    # Console interface tests
└── integration/
    └── test_full_workflow.py        # End-to-end user workflow tests
```

**Structure Decision**: Using single project structure (Option 1) as this is a standalone console application. The `src/` directory organizes code by layer (models, services, cli, main), following separation of concerns. The `tests/` directory mirrors `src/` structure for clarity. This structure will evolve in Phase II where `src/models/task.py` and `src/services/task_manager.py` will inform database schemas and API endpoints.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: No violations. No complexity tracking required.

---

## Phase 0: Research & Decision Log

*See [research.md](./research.md) for detailed findings.*

### Research Topics

1. **Python 3.13+ Best Practices for Console Applications**
   - Input validation patterns
   - Menu-driven interface design
   - Error handling strategies

2. **In-Memory Data Structure Selection**
   - List vs dictionary for task storage
   - Task entity design (dataclass vs class vs dict)
   - ID generation strategies

3. **Testing Strategy for Console Apps**
   - pytest best practices
   - Mocking console I/O
   - Integration test patterns

4. **Code Organization Patterns**
   - Module structure for maintainability
   - Separation of concerns implementation
   - Preparing for Phase II evolution

---

## Phase 1: Design Artifacts

### Data Model
*See [data-model.md](./data-model.md) for complete entity definitions.*

**Task Entity**:
- `id`: int (unique, auto-incrementing)
- `title`: str (required, non-empty)
- `description`: str (optional, defaults to "")
- `completed`: bool (defaults to False)
- `created_at`: datetime (timestamp of creation)

**TaskManager State**:
- `tasks`: List[Task] (in-memory list of all tasks)
- `next_id`: int (counter for generating unique IDs)

### Module Contracts
*See [contracts/](./contracts/) for detailed interface specifications.*

**TaskManager** (`src/services/task_manager.py`):
- `add_task(title: str, description: str = "") -> Task`
- `get_task(task_id: int) -> Task | None`
- `get_all_tasks() -> List[Task]`
- `update_task(task_id: int, title: str = None, description: str = None) -> bool`
- `delete_task(task_id: int) -> bool`
- `toggle_complete(task_id: int) -> bool`

**ConsoleInterface** (`src/cli/console_interface.py`):
- `display_menu() -> None`
- `get_user_choice() -> str`
- `display_tasks(tasks: List[Task]) -> None`
- `prompt_task_details() -> dict`
- `prompt_task_id() -> int`
- `display_message(message: str, message_type: str) -> None`

**Application Runner** (`src/main.py`):
- `main() -> None` (main loop: display menu → get choice → execute action → repeat)

### Quickstart
*See [quickstart.md](./quickstart.md) for user instructions.*

**Running the application**:
```bash
python src/main.py
```

**Expected workflow**:
1. User sees main menu with 6 options
2. User selects option (1-6)
3. Application executes corresponding action
4. User sees result/feedback
5. Menu redisplays (loop continues until exit)

---

## Architecture Decisions

### 1. Data Structure: List of Task Objects

**Decision**: Use a Python list to store Task objects (dataclass), managed by TaskManager.

**Rationale**:
- Simple and sufficient for in-memory storage
- Maintains insertion order (creation order)
- Easy to iterate for display
- Task objects provide type safety and clarity

**Alternatives Considered**:
- **Dict (task_id → Task)**: Faster lookups by ID, but list iteration is already O(n) and acceptable for up to 1000 tasks
- **List of dicts**: Less type-safe, harder to maintain

**Tradeoffs**:
- Pro: Simplicity, readability, type safety
- Con: O(n) lookups by ID (acceptable for Phase I scale)

### 2. Task ID Generation: Auto-Incrementing Counter

**Decision**: Use a simple integer counter (`next_id`) managed by TaskManager.

**Rationale**:
- Deterministic and predictable
- Easy for users to reference tasks ("Delete task #3")
- No external dependencies (no UUID library needed)

**Alternatives Considered**:
- **UUID**: Overkill for single-user, in-memory app
- **Index-based**: Fragile if tasks are deleted (IDs would shift)

**Tradeoffs**:
- Pro: Simple, user-friendly, deterministic
- Con: IDs are not globally unique (fine for Phase I, will change in Phase II with database)

### 3. Task Entity: Dataclass

**Decision**: Use Python dataclass for Task entity.

**Rationale**:
- Built-in to Python 3.7+ (no external deps)
- Automatic `__init__`, `__repr__`, `__eq__`
- Type annotations for clarity
- Lightweight and appropriate for Phase I

**Alternatives Considered**:
- **Plain class**: More boilerplate code
- **Dict**: No type safety, harder to maintain

**Tradeoffs**:
- Pro: Clean, Pythonic, minimal boilerplate
- Con: Slightly less flexible than plain class (not a concern for Phase I)

### 4. Module Organization: Three-Layer Architecture

**Decision**: Separate Task Manager (services), Console Interface (cli), and Application Runner (main).

**Rationale**:
- Enforces separation of concerns (Constitution IV)
- Each layer independently testable (Constitution V)
- Enables evolution to Phase II (Task Manager logic → API layer, Console Interface → Web UI)

**Alternatives Considered**:
- **Single file**: Violates separation of concerns, hard to test
- **More layers**: Overkill for Phase I (YAGNI violation)

**Tradeoffs**:
- Pro: Testability, maintainability, evolvability
- Con: Slightly more files (acceptable for clean architecture)

### 5. Testing Strategy: pytest with Unit + Integration Tests

**Decision**: Use pytest for unit tests (per module) and integration tests (full workflows).

**Rationale**:
- Industry standard for Python testing
- Easy to mock console I/O for testing
- Supports both unit and integration testing

**Alternatives Considered**:
- **unittest**: More verbose, less Pythonic
- **No tests**: Violates Constitution V (Testability NON-NEGOTIABLE)

**Tradeoffs**:
- Pro: Comprehensive test coverage, industry standard
- Con: Requires pytest installation (acceptable dev dependency)

---

## Risk Analysis

### Risk 1: Console I/O Testing Complexity
**Impact**: Medium
**Likelihood**: Medium
**Mitigation**: Use pytest's `capsys` fixture to capture stdout/stdin. Mock user input with `monkeypatch`.

### Risk 2: Task ID Management Across Deletions
**Impact**: Low
**Likelihood**: Low
**Mitigation**: Use auto-incrementing counter that never resets. Deleted task IDs are never reused (user-friendly and prevents confusion).

### Risk 3: Input Validation Edge Cases
**Impact**: Medium
**Likelihood**: High
**Mitigation**: Comprehensive validation in ConsoleInterface. Clear error messages for invalid inputs. Return to menu on errors.

---

## Next Steps

1. ✅ **Phase 0 Complete**: Research.md generated (see next section)
2. ✅ **Phase 1 Complete**: Data model, contracts, and quickstart generated
3. ⏭️ **Phase 2**: Run `/sp.tasks` to generate tasks.md with detailed implementation tasks
4. ⏭️ **Implementation**: Execute tasks via Claude Code following TDD workflow

---

## Success Validation

After implementation, validate against success criteria from spec.md:

- [ ] **SC-001**: Users can create a new task in under 10 seconds
- [ ] **SC-002**: Users can view task list with a single menu selection
- [ ] **SC-003**: Completed tasks visually distinguished from pending tasks
- [ ] **SC-004**: All 5 operations accessible from main menu
- [ ] **SC-005**: Task state maintained correctly throughout session
- [ ] **SC-006**: Clear feedback for every user action
- [ ] **SC-007**: Full task lifecycle works without errors
- [ ] **SC-008**: Edge cases handled gracefully

---

**Plan Status**: ✅ Complete - Ready for task generation (`/sp.tasks`)
