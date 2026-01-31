# Tasks: Authentication & API Security for Multi-User Todo Application

**Input**: Design documents from `/specs/002-phase2-fullstack/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth-api.yaml

**Tests**: Not explicitly requested - tests will be included as part of implementation validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for both backend and frontend

- [x] T001 Create backend directory structure per plan.md: backend/src/{models,services,api,core}
- [x] T002 Create frontend directory structure per plan.md: frontend/src/{lib,app}
- [x] T003 [P] Initialize Python backend with FastAPI in backend/requirements.txt (fastapi, uvicorn, sqlmodel, pyjwt, python-dotenv, psycopg2-binary)
- [x] T004 [P] Initialize Next.js frontend with better-auth in frontend/package.json
- [x] T005 [P] Create backend environment template in backend/.env.example (BETTER_AUTH_SECRET, DATABASE_URL)
- [x] T006 [P] Create frontend environment template in frontend/.env.example (BETTER_AUTH_SECRET, BETTER_AUTH_URL, NEXT_PUBLIC_API_URL)
- [x] T007 Add .gitignore entries for .env files, __pycache__, node_modules, .next

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Backend Core Infrastructure

- [x] T008 Create environment config loader in backend/src/core/config.py (load BETTER_AUTH_SECRET, DATABASE_URL)
- [x] T009 Create database connection module in backend/src/core/database.py (SQLModel + Neon PostgreSQL)
- [x] T010 [P] Create User SQLModel in backend/src/models/user.py per data-model.md (id, email, password_hash, name, timestamps)
- [x] T011 [P] Create Task SQLModel in backend/src/models/task.py per data-model.md (id, user_id FK, title, description, completed, priority, category, due_date, timestamps)
- [x] T012 Create JWT verification functions in backend/src/core/security.py (verify_token, extract_user_id using PyJWT)
- [x] T013 Create get_current_user dependency in backend/src/api/deps.py (HTTPBearer + JWT verification)
- [x] T014 Create FastAPI app entry point in backend/src/main.py (CORS, routers, exception handlers)
- [x] T015 [P] Create health check endpoint in backend/src/api/health.py (GET /health - no auth required)

### Frontend Core Infrastructure

- [x] T016 Create Better Auth server configuration in frontend/src/lib/auth.ts (emailAndPassword, JWT plugin, BETTER_AUTH_SECRET)
- [x] T017 Create Better Auth client configuration in frontend/src/lib/auth-client.ts (@better-auth/react client)
- [x] T018 Create Better Auth API route handler in frontend/src/app/api/auth/[...all]/route.ts
- [x] T019 Create route protection middleware in frontend/src/middleware.ts (redirect unauthenticated users)
- [x] T020 Create authenticated fetch utility in frontend/src/lib/api.ts (attach Bearer token to requests)

### Database Setup

- [x] T021 Create database migration script in backend/scripts/init_db.sql per data-model.md (users, sessions, tasks tables with indexes)
- [ ] T022 Test database connection and run migrations (MANUAL - requires DATABASE_URL)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - New User Registration (Priority: P1) MVP

**Goal**: New users can create accounts with email/password and are automatically signed in

**Independent Test**: Submit registration form with valid credentials, verify account creation and automatic sign-in

**Acceptance Criteria** (from spec.md):
- Valid email + password (min 8 chars) creates account and signs in automatically
- Duplicate email shows "already registered" error
- Password < 8 chars shows validation error

### Implementation for User Story 1

- [x] T023 [US1] Create signup page component in frontend/src/app/(auth)/signup/page.tsx (email, password, name fields)
- [x] T024 [US1] Implement form validation in signup page (email format, password min 8 chars)
- [x] T025 [US1] Connect signup form to Better Auth signUp.email() in frontend/src/app/(auth)/signup/page.tsx
- [x] T026 [US1] Handle signup errors (duplicate email, validation) with user-friendly messages
- [x] T027 [US1] Implement auto-redirect to dashboard after successful signup
- [ ] T028 [US1] Verify Better Auth stores user with hashed password (scrypt) - manual test

**Checkpoint**: User Story 1 complete - new users can register and are signed in automatically

---

## Phase 4: User Story 2 - Existing User Sign In (Priority: P1)

**Goal**: Registered users can sign in with email/password to access their tasks

**Independent Test**: Sign in with valid credentials, verify redirect to dashboard

**Acceptance Criteria** (from spec.md):
- Correct email + password signs in and redirects to dashboard
- Incorrect password shows generic "invalid credentials" error
- Non-existent email shows same generic error (security)

### Implementation for User Story 2

- [x] T029 [US2] Create signin page component in frontend/src/app/(auth)/signin/page.tsx (email, password fields)
- [x] T030 [US2] Connect signin form to Better Auth signIn.email() in frontend/src/app/(auth)/signin/page.tsx
- [x] T031 [US2] Handle signin errors with generic "Invalid credentials" message (never reveal if email exists)
- [x] T032 [US2] Implement redirect to dashboard after successful signin
- [x] T033 [US2] Add "Create account" link on signin page to navigate to signup

**Checkpoint**: User Story 2 complete - existing users can sign in

---

## Phase 5: User Story 3 - Authenticated API Access (Priority: P1)

**Goal**: Signed-in users can perform task CRUD operations with proper authentication

**Independent Test**: Make API requests with/without JWT token, verify acceptance/rejection

**Acceptance Criteria** (from spec.md):
- Valid JWT returns only user's tasks
- Missing JWT returns 401 Unauthorized
- New tasks auto-associate with authenticated user

### Backend Implementation for User Story 3

- [x] T034 [US3] Implement GET /tasks endpoint in backend/src/api/tasks.py (list user's tasks, filtered by user_id)
- [x] T035 [US3] Implement POST /tasks endpoint in backend/src/api/tasks.py (create task with user_id from JWT)
- [x] T036 [US3] Implement GET /tasks/{task_id} endpoint in backend/src/api/tasks.py (single task, ownership check)
- [x] T037 [US3] Implement PATCH /tasks/{task_id} endpoint in backend/src/api/tasks.py (update, ownership check)
- [x] T038 [US3] Implement DELETE /tasks/{task_id} endpoint in backend/src/api/tasks.py (delete, ownership check)
- [x] T039 [US3] Implement POST /tasks/{task_id}/complete endpoint in backend/src/api/tasks.py (mark complete)
- [x] T040 [US3] Implement DELETE /tasks/{task_id}/complete endpoint in backend/src/api/tasks.py (mark incomplete)
- [x] T041 [US3] Add query parameters support (completed, priority, category, sort, order) to GET /tasks
- [x] T042 [US3] Register tasks router in backend/src/main.py

### Frontend Implementation for User Story 3

- [x] T043 [US3] Create dashboard page in frontend/src/app/dashboard/page.tsx (protected route)
- [x] T044 [US3] Implement task list component with API fetch in frontend/src/app/dashboard/page.tsx
- [x] T045 [US3] Implement create task form in frontend/src/app/dashboard/page.tsx
- [x] T046 [US3] Implement task update (edit) functionality in frontend/src/app/dashboard/page.tsx
- [x] T047 [US3] Implement task delete functionality in frontend/src/app/dashboard/page.tsx
- [x] T048 [US3] Implement task completion toggle in frontend/src/app/dashboard/page.tsx
- [x] T049 [US3] Handle 401 errors by redirecting to signin page

**Checkpoint**: User Story 3 complete - authenticated users can manage their tasks

---

## Phase 6: User Story 4 - User Data Isolation (Priority: P2)

**Goal**: Users can only see and modify their own tasks, not other users' tasks

**Independent Test**: Create tasks as User A, sign in as User B, verify User B cannot see User A's tasks

**Acceptance Criteria** (from spec.md):
- User B sees only their own tasks (not User A's)
- User B updating User A's task returns 404 Not Found
- User B deleting User A's task returns 404 Not Found

### Implementation for User Story 4

- [x] T050 [US4] Verify all task queries in backend/src/api/tasks.py include user_id filter (code review)
- [x] T051 [US4] Verify GET /tasks/{id} returns 404 for other user's tasks (not 403)
- [x] T052 [US4] Verify PATCH /tasks/{id} returns 404 for other user's tasks (not 403)
- [x] T053 [US4] Verify DELETE /tasks/{id} returns 404 for other user's tasks (not 403)
- [ ] T054 [US4] Manual test: Create two users, verify data isolation

**Checkpoint**: User Story 4 complete - data isolation enforced

---

## Phase 7: User Story 5 - User Sign Out (Priority: P2)

**Goal**: Users can sign out, which terminates their session

**Independent Test**: Sign out and verify subsequent API requests are rejected

**Acceptance Criteria** (from spec.md):
- Click sign out terminates session, redirects to signin
- Protected pages redirect to signin after sign out
- Old token rejected with 401 after sign out

### Implementation for User Story 5

- [x] T055 [US5] Add sign out button to dashboard in frontend/src/app/dashboard/page.tsx
- [x] T056 [US5] Connect sign out button to Better Auth signOut() in frontend/src/app/dashboard/page.tsx
- [x] T057 [US5] Implement redirect to signin page after sign out
- [x] T058 [US5] Verify middleware redirects unauthenticated users on protected routes
- [ ] T059 [US5] Manual test: Sign out and verify old token is rejected

**Checkpoint**: User Story 5 complete - sign out functionality working

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T060 [P] Add logging for authentication events in backend/src/core/security.py (sign-in success/failure)
- [x] T061 [P] Add logging for task operations in backend/src/api/tasks.py
- [x] T062 [P] Add error handling for database connection failures in backend/src/core/database.py
- [x] T063 [P] Add loading states to frontend forms in frontend/src/app/(auth)/
- [x] T064 [P] Add error boundary for frontend pages
- [ ] T065 Validate quickstart.md instructions by following setup steps (MANUAL)
- [ ] T066 Run full end-to-end test: register, sign in, create tasks, sign out, sign in again, verify tasks (MANUAL)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational) ← BLOCKS ALL USER STORIES
    │
    ├───────────────────┬───────────────────┐
    ▼                   ▼                   ▼
Phase 3 (US1)     Phase 4 (US2)      Phase 5 (US3)
Registration      Sign In            API Access
    │                   │                   │
    └───────────────────┴───────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    ▼                   ▼                   ▼
Phase 6 (US4)     Phase 7 (US5)
Data Isolation    Sign Out
    │                   │
    └───────────────────┘
                │
                ▼
        Phase 8 (Polish)
```

### User Story Dependencies

| Story | Depends On | Can Start After |
|-------|------------|-----------------|
| US1 (Registration) | Foundational | Phase 2 complete |
| US2 (Sign In) | Foundational | Phase 2 complete |
| US3 (API Access) | Foundational | Phase 2 complete |
| US4 (Data Isolation) | US3 | Phase 5 complete |
| US5 (Sign Out) | US1 or US2 | Phase 3 or 4 complete |

### Within Each User Story

1. Backend tasks before frontend tasks (if applicable)
2. Core functionality before edge cases
3. Verify checkpoint before moving to next story

### Parallel Opportunities

**Phase 1 (parallel)**:
- T003, T004, T005, T006 can all run in parallel

**Phase 2 (parallel)**:
- T010, T011 (models) can run in parallel
- T015, T016, T017 can run in parallel after core setup

**User Stories (parallel)**:
- US1, US2, US3 can all start in parallel after Phase 2
- US4, US5 can start in parallel after US3 completes

---

## Parallel Example: Phase 2 Foundational

```bash
# After T008, T009 complete, launch models in parallel:
Task: "Create User SQLModel in backend/src/models/user.py"
Task: "Create Task SQLModel in backend/src/models/task.py"

# After models complete, launch security in parallel:
Task: "Create JWT verification functions in backend/src/core/security.py"
Task: "Create Better Auth server configuration in frontend/src/lib/auth.ts"
```

---

## Parallel Example: User Stories After Foundational

```bash
# After Phase 2 completes, launch all P1 stories in parallel:

# Developer A: User Story 1
Task: "Create signup page component in frontend/src/app/(auth)/signup/page.tsx"

# Developer B: User Story 2
Task: "Create signin page component in frontend/src/app/(auth)/signin/page.tsx"

# Developer C: User Story 3
Task: "Implement GET /tasks endpoint in backend/src/api/tasks.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Registration)
4. Complete Phase 4: User Story 2 (Sign In)
5. Complete Phase 5: User Story 3 (API Access)
6. **STOP and VALIDATE**: Test full auth + task CRUD flow
7. Deploy/demo MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Registration) → Test → Can create accounts!
3. Add US2 (Sign In) → Test → Returning users can access!
4. Add US3 (API Access) → Test → Full task management! (MVP complete)
5. Add US4 (Data Isolation) → Test → Multi-user security verified
6. Add US5 (Sign Out) → Test → Session management complete
7. Polish → Production ready

### Suggested MVP Scope

**Minimum viable: User Stories 1, 2, 3**
- Users can register, sign in, and manage tasks
- Authentication and authorization working end-to-end
- Data properly isolated (US4) is security-critical, should be included

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend uses FastAPI + SQLModel + PyJWT per plan.md
- Frontend uses Next.js 16+ + Better Auth per plan.md
- All task endpoints require valid JWT except /health
