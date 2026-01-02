# Tasks: Phase I - In-Memory Console Todo App

**Input**: Design documents from `/specs/001-phase1-console-todo/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/, research.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow single project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create src/ directory structure with models/, services/, cli/ subdirectories
- [x] T002 Create tests/ directory structure with unit/ and integration/ subdirectories
- [x] T003 [P] Create empty __init__.py files in src/models/, src/services/, src/cli/
- [x] T004 [P] Create pytest.ini configuration file for test discovery
- [x] T005 [P] Create .gitignore file for Python project (__pycache__/, *.pyc, .pytest_cache/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create Task dataclass in src/models/task.py with id, title, description, completed, created_at attributes
- [x] T007 Add __post_init__ validation to Task dataclass to ensure title is non-empty
- [x] T008 Create TaskManager class in src/services/task_manager.py with __init__ method (initialize tasks list and next_id counter)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create and View Tasks (Priority: P1) 🎯 MVP

**Goal**: Enable users to add new tasks and view their task list

**Independent Test**: Launch application, add tasks with titles and descriptions, view task list to verify they appear correctly

### Implementation for User Story 1

- [x] T009 [P] [US1] Implement TaskManager.add_task(title, description) method in src/services/task_manager.py
- [x] T010 [P] [US1] Implement TaskManager.get_all_tasks() method in src/services/task_manager.py
- [x] T011 [US1] Create ConsoleInterface class in src/cli/console_interface.py with __init__(task_manager) constructor
- [x] T012 [P] [US1] Implement ConsoleInterface.display_menu() method in src/cli/console_interface.py
- [x] T013 [P] [US1] Implement ConsoleInterface.get_user_choice() method with input validation in src/cli/console_interface.py
- [x] T014 [US1] Implement ConsoleInterface.display_tasks(tasks) method in src/cli/console_interface.py with formatting for empty/populated lists
- [x] T015 [US1] Implement ConsoleInterface.prompt_task_details() method in src/cli/console_interface.py to collect title and description
- [x] T016 [US1] Implement ConsoleInterface.display_message(message, type) method in src/cli/console_interface.py with success/error/info formatting
- [x] T017 [US1] Implement ConsoleInterface.run_add_task_workflow() method in src/cli/console_interface.py
- [x] T018 [US1] Implement ConsoleInterface.run_view_tasks_workflow() method in src/cli/console_interface.py
- [x] T019 [US1] Create main() function in src/main.py with TaskManager and ConsoleInterface initialization
- [x] T020 [US1] Implement main event loop in src/main.py with menu display and choice routing for options 1 (view) and 2 (add)
- [x] T021 [US1] Add exit functionality (option 6) to main event loop in src/main.py with goodbye message
- [x] T022 [US1] Add exception handling for KeyboardInterrupt and unexpected errors in src/main.py
- [x] T023 [US1] Add if __name__ == "__main__" guard to src/main.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (MVP complete!)

---

## Phase 4: User Story 2 - Mark Tasks Complete (Priority: P2)

**Goal**: Enable users to toggle task completion status

**Independent Test**: Create tasks, mark some as complete, verify completed tasks are visually distinguished from pending tasks in list view

### Implementation for User Story 2

- [x] T024 [P] [US2] Implement TaskManager.get_task(task_id) method in src/services/task_manager.py
- [x] T025 [P] [US2] Implement TaskManager.toggle_complete(task_id) method in src/services/task_manager.py
- [x] T026 [US2] Implement ConsoleInterface.prompt_task_id() method in src/cli/console_interface.py with integer validation
- [x] T027 [US2] Update ConsoleInterface.display_tasks() in src/cli/console_interface.py to show ☐ for pending and ☑ for completed tasks
- [x] T028 [US2] Implement ConsoleInterface.run_toggle_complete_workflow() method in src/cli/console_interface.py
- [x] T029 [US2] Add option 5 (mark complete/incomplete) routing to main event loop in src/main.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Update Task Details (Priority: P3)

**Goal**: Enable users to modify existing task titles and descriptions

**Independent Test**: Create a task, update its title and/or description, verify changes are reflected in task list

### Implementation for User Story 3

- [x] T030 [P] [US3] Implement TaskManager.update_task(task_id, title, description) method in src/services/task_manager.py
- [x] T031 [US3] Implement ConsoleInterface.run_update_task_workflow() method in src/cli/console_interface.py
- [x] T032 [US3] Add option 3 (update task) routing to main event loop in src/main.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Delete Tasks (Priority: P4)

**Goal**: Enable users to remove tasks from their list

**Independent Test**: Create several tasks, delete specific tasks, verify they no longer appear in task list

### Implementation for User Story 4

- [x] T033 [P] [US4] Implement TaskManager.delete_task(task_id) method in src/services/task_manager.py
- [x] T034 [US4] Implement ConsoleInterface.run_delete_task_workflow() method in src/cli/console_interface.py with confirmation prompt
- [x] T035 [US4] Add option 4 (delete task) routing to main event loop in src/main.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T036 [P] Add welcome message to src/main.py informing users about in-memory storage limitation
- [x] T037 [P] Verify all error messages are clear and actionable across all ConsoleInterface methods
- [x] T038 [P] Add blank line spacing between menu iterations in src/main.py for readability
- [x] T039 Test application manually using checklist from quickstart.md (all 14 items)
- [x] T040 Verify application handles all edge cases from spec.md gracefully

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 (uses Task entity, display methods) but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable

### Within Each User Story

- Core implementations (Task Manager, Console Interface methods) before workflows
- Workflows before main.py routing
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005)
- Within User Story 1: T009, T010 (TaskManager methods), T012, T013 (ConsoleInterface methods) can run in parallel
- Within User Story 2: T024, T025 (TaskManager methods) can run in parallel
- Different user stories can be worked on in parallel by different team members after Foundational phase
- All Polish phase tasks marked [P] can run in parallel (T036, T037, T038)

---

## Parallel Example: User Story 1

```bash
# After Foundational phase, launch these tasks together:
Task: "Implement TaskManager.add_task(title, description) method in src/services/task_manager.py"
Task: "Implement TaskManager.get_all_tasks() method in src/services/task_manager.py"
Task: "Implement ConsoleInterface.display_menu() method in src/cli/console_interface.py"
Task: "Implement ConsoleInterface.get_user_choice() method in src/cli/console_interface.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (tasks T001-T005)
2. Complete Phase 2: Foundational (tasks T006-T008) - CRITICAL
3. Complete Phase 3: User Story 1 (tasks T009-T023)
4. **STOP and VALIDATE**: Test User Story 1 independently using manual checklist
5. Application is now minimally viable - users can add and view tasks!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP DEPLOYED** ✅
3. Add User Story 2 → Test independently → Deploy (users can now mark tasks complete)
4. Add User Story 3 → Test independently → Deploy (users can now update tasks)
5. Add User Story 4 → Test independently → Deploy (users can now delete tasks)
6. Complete Polish phase → Final release
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (tasks T001-T008)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (tasks T009-T023)
   - **Developer B**: User Story 2 (tasks T024-T029) - waits for T006-T008, T011
   - **Developer C**: User Story 3 (tasks T030-T032) - waits for T006-T008, T011
   - **Developer D**: User Story 4 (tasks T033-T035) - waits for T006-T008, T011
3. Stories complete and integrate independently
4. All developers collaborate on Polish phase (tasks T036-T040)

---

## Task Breakdown by Phase

| Phase | Task Range | Count | Description |
|-------|------------|-------|-------------|
| Phase 1: Setup | T001-T005 | 5 | Project initialization |
| Phase 2: Foundational | T006-T008 | 3 | Core infrastructure (BLOCKING) |
| Phase 3: User Story 1 (P1) | T009-T023 | 15 | Create and View Tasks (MVP) |
| Phase 4: User Story 2 (P2) | T024-T029 | 6 | Mark Tasks Complete |
| Phase 5: User Story 3 (P3) | T030-T032 | 3 | Update Task Details |
| Phase 6: User Story 4 (P4) | T033-T035 | 3 | Delete Tasks |
| Phase 7: Polish | T036-T040 | 5 | Cross-cutting improvements |
| **TOTAL** | T001-T040 | **40** | All implementation tasks |

---

## Testing Validation

After completing all phases, validate against success criteria from spec.md:

- [x] **SC-001**: Users can create a new task in under 10 seconds
- [x] **SC-002**: Users can view task list with a single menu selection
- [x] **SC-003**: Completed tasks visually distinguished from pending tasks
- [x] **SC-004**: All 5 operations accessible from main menu
- [x] **SC-005**: Task state maintained correctly throughout session
- [x] **SC-006**: Clear feedback for every user action
- [x] **SC-007**: Full task lifecycle works without errors
- [x] **SC-008**: Edge cases handled gracefully

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **IMPORTANT**: All tasks follow required checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

---

**Tasks Status**: ✅ Complete - Ready for implementation via `/sp.implement` or manual execution
