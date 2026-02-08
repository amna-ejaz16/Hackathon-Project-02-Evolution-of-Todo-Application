# Tasks: Todo AI Chatbot - Cyberpunk UI/UX

**Input**: Design documents from `/specs/003-phase3-ai-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/chat-api.yaml

**Tests**: Not explicitly requested — verification is manual via quickstart.md integration test flow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/requirements.txt`
- **Frontend**: `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and configure environment for AI chatbot feature

- [x] T001 Add `openai-agents>=0.8.0` and `openai>=1.0.0` to `backend/requirements.txt` and install via pip
- [x] T002 Add `OPENAI_API_KEY` setting to `backend/src/core/config.py` in the `Settings.__init__` method (required, with validation)
- [x] T003 [P] Add `OPENAI_API_KEY=sk-your-key-here` to `backend/.env.example` as documentation for other developers
- [x] T004 [P] Create `frontend/src/components/chat/` directory for all chat UI components

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Chat data models and database table registration — MUST be complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create `Conversation` SQLModel (table=True) in `backend/src/models/chat.py` with fields: id (PK, auto-increment), user_id (Text, NOT NULL, indexed), title (Text, default "Task Assistant"), created_at (datetime, default utcnow), updated_at (datetime, default utcnow). user_id is TEXT to match Better Auth's user.id format per data-model.md
- [x] T006 Create `Message` SQLModel (table=True) in `backend/src/models/chat.py` with fields: id (PK, auto-increment), conversation_id (Integer, FK→conversation.id, indexed), role (Text, NOT NULL, "user" or "assistant"), content (Text, NOT NULL), metadata (Optional JSON/Text, nullable), created_at (datetime, default utcnow). Follow existing Task model patterns from `backend/src/models/task.py`
- [x] T007 [P] Create Pydantic schemas in `backend/src/models/chat.py`: ChatRequest (message: str, minLength 1, maxLength 2000), ChatResponse (response: str, conversation_id: int, action: Optional[str], task_id: Optional[int]), ChatHistoryResponse (messages: List[MessageRead], conversation_id: Optional[int], total: int), MessageRead (id: int, role: str, content: str, metadata: Optional[dict], created_at: datetime). Match contract in `contracts/chat-api.yaml`
- [x] T008 Register chat models in `backend/src/core/database.py` by adding `from ..models.chat import Conversation, Message` in the `create_db_and_tables()` function (next to existing Task import at line 52). Tables auto-created by SQLModel.metadata.create_all with checkfirst=True

**Checkpoint**: Foundation ready — chat tables created on next backend startup, schemas available for all stories

---

## Phase 3: User Story 1 — Open and Close the AI Chat Widget (Priority: P1) MVP

**Goal**: Logged-in user sees a FAB on the dashboard, clicks to open a cyberpunk-themed chat panel, clicks again to close

**Independent Test**: Verify FAB renders on dashboard, opens panel on click, closes on dismiss. No backend needed.

**Acceptance Criteria** (from spec.md US1):
- FAB visible at bottom-right with neon purple-to-magenta gradient and soft glow
- Chat panel slides open with smooth animation on click
- Close button or swipe-down (mobile) dismisses panel
- Mobile < 768px: full-width bottom sheet; Desktop: side panel ~380px wide

### Implementation for User Story 1

- [x] T009 [P] [US1] Create `ChatHeader.tsx` in `frontend/src/components/chat/ChatHeader.tsx` — AI avatar icon (robot/sparkles emoji or SVG), title "Task Manager Assistant", close button (X), gradient accent strip at top. Props: `onClose: () => void`. Use existing cyberpunk classes: `card-dark`, `text-gradient`, glassmorphism backdrop
- [x] T010 [P] [US1] Create `ChatInput.tsx` in `frontend/src/components/chat/ChatInput.tsx` — dark glassmorphism input field with `input-dark` class, neon focus ring (purple glow on focus), gradient send button with hover/press states. Props: `onSend: (message: string) => void`, `disabled: boolean`. Enter key submits, empty input blocked (FR-005). Use existing `btn-neon` patterns
- [x] T011 [US1] Create `ChatWidget.tsx` in `frontend/src/components/chat/ChatWidget.tsx` — FAB button (fixed bottom-right, neon gradient, hover lift animation via Framer Motion `whileHover`/`whileTap`) + panel container. State: `isOpen` boolean. FAB: circular, 56px, `bg-gradient-to-r from-purple-500 to-pink-500` with shadow glow. Panel: conditional render with `AnimatePresence` + `motion.div` slide animation. Props: `onTaskChange: () => void`. Desktop: 380px wide, 560px tall, fixed bottom-right. Mobile < 768px: full-width bottom sheet. Compose ChatHeader + ChatInput inside panel. FR-001, FR-002, FR-003
- [x] T012 [US1] Implement mobile bottom-sheet behavior in `ChatWidget.tsx` — use Framer Motion `drag="y"` on panel header (NOT message area) with `dragConstraints` and `onDragEnd` to dismiss when dragged down >100px. Media query or `useMediaQuery` hook for < 768px breakpoint (FR-003, NFR-002)
- [x] T013 [US1] Embed `ChatWidget` in `frontend/src/app/dashboard/DashboardClient.tsx` — import ChatWidget and render at end of component JSX (before closing fragment). Pass `onTaskChange={fetchTasks}` callback prop. This connects the chat to dashboard refresh (FR-025)

**Checkpoint**: FAB visible on dashboard, panel opens/closes with animations. No backend wiring yet.

---

## Phase 4: User Story 2 — Send a Message and Receive AI Response (Priority: P1)

**Goal**: User types a message, sees it as a user bubble, typing indicator shows, AI response appears as assistant bubble

**Independent Test**: Type any message, verify send/receive loop works, messages display correctly with proper styling

**Acceptance Criteria** (from spec.md US2):
- User message appears as right-aligned bubble with neon styling
- Typing indicator (pulsing dots) while AI processes
- AI response appears as left-aligned bubble with glassmorphism
- Empty messages blocked; auto-scroll to latest message

### Backend Implementation for User Story 2

- [ ] T014 [US2] Create `backend/src/services/task_tools.py` — define `create_task_tools(user_id: str, session: Session)` factory function that returns a list of `@function_tool` decorated functions. Start with a single placeholder tool `list_tasks` that queries tasks for user_id and returns a formatted string. Import from `agents` package: `from agents import function_tool`. Each tool receives `user_id` via closure. Tools will be expanded in US3-US6
- [ ] T015 [US2] Create `backend/src/services/chat_service.py` — implement `ChatService` class with methods: `get_or_create_conversation(user_id, session)` → returns Conversation, `get_context_messages(conversation_id, session, limit=20)` → last 20 messages as list (FR-026), `store_message(conversation_id, role, content, metadata, session)` → saves Message + prunes if >200 (FR-027), `process_message(user_message, user_id, session)` → full flow: get/create conversation → store user message → fetch context → create Agent with tools → run via `Runner.run()` → extract response + metadata → store assistant message → return ChatResponse. Use `from agents import Agent, Runner` and `from .task_tools import create_task_tools`
- [ ] T016 [US2] Create `backend/src/api/chat.py` — implement `POST /api/chat` endpoint. Auth: `get_current_user` dependency (same as tasks.py). Input: `ChatRequest`. Process: call `ChatService.process_message()`. Output: `ChatResponse`. Error handling: try/except for OpenAI errors → HTTP 503 with "AI service temporarily unavailable" message. Validation: 422 for empty message. Match contract in `contracts/chat-api.yaml`
- [ ] T017 [US2] Add `GET /api/chat/history` endpoint in `backend/src/api/chat.py` — Auth: `get_current_user`. Query param: `limit` (default 50, min 1, max 200). Returns `ChatHistoryResponse` with messages array, conversation_id (null if no conversation), and total count. Match contract in `contracts/chat-api.yaml`
- [ ] T018 [US2] Register chat router in `backend/src/main.py` — import chat router and add `app.include_router(chat_router, prefix="/api/chat", tags=["chat"])` after the existing tasks router registration (line 66)

### Frontend Implementation for User Story 2

- [ ] T019 [P] [US2] Create `ChatMessage.tsx` in `frontend/src/components/chat/ChatMessage.tsx` — individual message bubble. Props: `role: "user" | "assistant"`, `content: string`, `timestamp: string`. User bubble: right-aligned, neon purple/magenta gradient bg, white text. Assistant bubble: left-aligned, `glass-strong` or dark translucent bg, light text. Framer Motion `initial={{ opacity: 0, y: 10 }}` → `animate={{ opacity: 1, y: 0 }}` for fade+slide entrance (FR-006, FR-008)
- [ ] T020 [P] [US2] Create `TypingIndicator.tsx` in `frontend/src/components/chat/TypingIndicator.tsx` — three pulsing dots with staggered animation using Framer Motion. Each dot: 8px circle, neon purple. Stagger delay: 0.15s between dots. Animation: scale 0.5→1→0.5 with infinite repeat (FR-007)
- [ ] T021 [US2] Create `ChatMessages.tsx` in `frontend/src/components/chat/ChatMessages.tsx` — scrollable container for messages. Props: `messages: Array<{id, role, content, created_at}>`, `isLoading: boolean`. Uses `useRef` for scroll container + `useEffect` to auto-scroll to bottom on new messages (FR-009). Renders `ChatMessage` for each message + `TypingIndicator` when `isLoading=true`. Overflow-y auto, dark themed scrollbar
- [ ] T022 [US2] Wire ChatWidget to backend API in `frontend/src/components/chat/ChatWidget.tsx` — add state: `messages[]`, `isSending` boolean, `conversationId`. On panel open (first time): call `GET /api/chat/history` via existing `api.get("/api/chat/history")` from `frontend/src/lib/api.ts` to load history. On send: append user message to state → set `isSending=true` → call `POST /api/chat` with `{ message }` → append AI response to state → set `isSending=false`. Check response `action` field — if task mutation action (task_created/task_updated/task_completed/task_uncompleted/task_deleted), call `onTaskChange()` (FR-025). Compose ChatMessages inside panel between ChatHeader and ChatInput

**Checkpoint**: Full send/receive loop working. User can type messages, see typing indicator, get AI responses. Dashboard auto-refreshes on task mutations.

---

## Phase 5: User Story 3 — Create a Task via Chat (Priority: P1)

**Goal**: User says "Add a task to buy groceries by Friday with high priority" and the AI creates it, confirms, and dashboard updates

**Independent Test**: Send create-task command via chat, verify AI confirms with details, verify task appears in dashboard

**Acceptance Criteria** (from spec.md US3):
- Natural language task creation with AI confirmation including details
- Dashboard auto-refreshes showing new task
- Incomplete commands trigger clarification (not blank task creation)

### Implementation for User Story 3

- [ ] T023 [US3] Implement `add_task` function tool in `backend/src/services/task_tools.py` — `@function_tool` decorator. Parameters: title (str, required), description (str, optional), priority (str, default "medium"), category (str, optional), due_date (str, optional, ISO format). Creates Task via SQLModel session (same pattern as `backend/src/api/tasks.py` lines 84-121). Returns formatted string: "Created task '{title}' (ID: {id}) with priority {priority}..." including due_date and category if provided. Bind user_id via closure from factory function
- [ ] T024 [US3] Configure Agent instructions for task creation in `backend/src/services/chat_service.py` — set Agent `instructions` string to include: "You are a task management assistant. You help users manage their todo tasks. When a user wants to create a task, extract the title, description, priority (low/medium/high), category, and due date from their message. If the title is unclear or missing, ask for clarification. Apply reasonable defaults: medium priority, no category, no due date. Always confirm what you created." (FR-018, FR-023). Instructions must explicitly prohibit non-task actions
- [ ] T025 [US3] Set `action` field in ChatResponse metadata — in `chat_service.py`, after agent execution, parse tool calls from agent result to determine action type. If `add_task` was called, set `action="task_created"` and `task_id` from the tool return. If no tool called, set `action="conversation"`. Map to enum values from `contracts/chat-api.yaml`: task_created, task_updated, task_completed, task_uncompleted, task_deleted, tasks_listed, clarification, conversation

**Checkpoint**: Task creation via chat works end-to-end. Dashboard auto-refreshes.

---

## Phase 6: User Story 4 — List and Query Tasks via Chat (Priority: P2)

**Goal**: User asks "Show all my tasks" or "What's pending?" and AI responds with formatted task list

**Independent Test**: Ask AI to list tasks, verify response matches dashboard data

**Acceptance Criteria** (from spec.md US4):
- "Show all my tasks" returns formatted list with title, status, priority, due date
- "What's pending?" returns only incomplete tasks
- "Show high priority tasks" filters correctly
- No tasks returns friendly suggestion message

### Implementation for User Story 4

- [ ] T026 [US4] Implement `list_tasks` function tool in `backend/src/services/task_tools.py` — replace placeholder from T014 with full implementation. Parameters: status (str, optional: "all"/"pending"/"completed"), priority (str, optional: "low"/"medium"/"high"), category (str, optional). Queries Task table filtered by user_id + optional filters (same pattern as `backend/src/api/tasks.py` lines 24-80). Returns formatted string listing tasks or "You don't have any tasks yet" if empty. Set action to "tasks_listed"
- [ ] T027 [US4] Update Agent instructions in `backend/src/services/chat_service.py` to handle list queries — add: "When a user asks to see tasks, use list_tasks tool with appropriate filters. Format the response as a numbered list with title, priority, status, and due date. If no tasks match, suggest creating one."

**Checkpoint**: Users can list and filter tasks via chat.

---

## Phase 7: User Story 5 — Complete and Delete Tasks via Chat (Priority: P2)

**Goal**: User can mark tasks complete or delete them via natural language, with disambiguation for ambiguous references

**Independent Test**: Complete a known task via chat, delete a task with confirmation, verify dashboard updates

**Acceptance Criteria** (from spec.md US5):
- "Complete the buy groceries task" marks it done with confirmation
- "Delete the buy groceries task" asks for confirmation before deleting
- Non-existent task returns helpful message
- Multiple matches triggers disambiguation list

### Implementation for User Story 5

- [ ] T028 [US5] Implement `complete_task` function tool in `backend/src/services/task_tools.py` — Parameters: task_id (int, required). Queries Task by id + user_id (ownership check). Sets completed=True, updates updated_at. Returns confirmation string with task title. Returns error string if task not found. Pattern from `backend/src/api/tasks.py` lines 227-256. Set action to "task_completed"
- [ ] T029 [US5] Implement `uncomplete_task` function tool in `backend/src/services/task_tools.py` — Parameters: task_id (int, required). Sets completed=False. Pattern from `backend/src/api/tasks.py` lines 259-289. Set action to "task_uncompleted"
- [ ] T030 [US5] Implement `delete_task` function tool in `backend/src/services/task_tools.py` — Parameters: task_id (int, required). Queries Task by id + user_id. Deletes task. Returns confirmation string. Pattern from `backend/src/api/tasks.py` lines 197-223. Set action to "task_deleted"
- [ ] T031 [US5] Update Agent instructions for completion/deletion in `backend/src/services/chat_service.py` — add: "When user wants to complete or delete a task, first use list_tasks to find matching tasks by title keywords. If exactly one match, proceed with the operation. If multiple matches, list them with IDs and ask user to specify. If no match, inform user and offer to list tasks. For delete, always confirm before proceeding." (FR-023, FR-024)

**Checkpoint**: Complete and delete task operations work via chat with disambiguation.

---

## Phase 8: User Story 6 — Update Tasks via Chat (Priority: P2)

**Goal**: User can change task priority, category, due date, title, or description via natural language

**Independent Test**: Update a task field via chat, verify change in dashboard

**Acceptance Criteria** (from spec.md US6):
- "Change buy groceries to high priority" updates priority
- "Set due date for buy groceries to next Monday" updates due date
- "Rename buy groceries to Get weekly groceries" updates title
- Ambiguous update triggers clarification

### Implementation for User Story 6

- [ ] T032 [US6] Implement `update_task` function tool in `backend/src/services/task_tools.py` — Parameters: task_id (int, required), title (str, optional), description (str, optional), priority (str, optional), category (str, optional), due_date (str, optional). Queries Task by id + user_id. Updates only provided fields (partial update). Pattern from `backend/src/api/tasks.py` lines 150-193. Returns confirmation string with what was changed. Set action to "task_updated"
- [ ] T033 [US6] Update Agent instructions for task updates in `backend/src/services/chat_service.py` — add: "When user wants to update a task, first find the task using list_tasks, then call update_task with only the fields that need changing. Confirm what was updated."

**Checkpoint**: All CRUD operations (create, read, update, delete, complete) work via chat. Full task management capability.

---

## Phase 9: User Story 7 — Quick Action Pills (Priority: P3)

**Goal**: Quick action shortcut buttons below chat input for common operations

**Independent Test**: Tap a pill, verify corresponding message is sent as a chat message

**Acceptance Criteria** (from spec.md US7):
- Pills displayed below input area with cyberpunk styling
- Tapping "Show all tasks" sends that as a user message

### Implementation for User Story 7

- [ ] T034 [P] [US7] Create `QuickActionPills.tsx` in `frontend/src/components/chat/QuickActionPills.tsx` — static array of pill objects: [{label: "Show all tasks", message: "Show all my tasks"}, {label: "Add a task", message: "I want to add a new task"}, {label: "What's overdue?", message: "Show me overdue tasks"}]. Props: `onPillClick: (message: string) => void`, `disabled: boolean`. Each pill: rounded-full, small text, neon border glow, hover lift via Framer Motion `whileHover={{ scale: 1.05, y: -2 }}`. Styled with `border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 text-purple-300` (FR-019)
- [ ] T035 [US7] Integrate QuickActionPills into ChatWidget in `frontend/src/components/chat/ChatWidget.tsx` — render between ChatMessages and ChatInput. Pass `onPillClick` that calls the same send function used by ChatInput. Hide pills when `isSending` is true

**Checkpoint**: Quick action pills provide convenient shortcuts for common operations.

---

## Phase 10: User Story 8 — Conversation History Persistence (Priority: P3)

**Goal**: Chat messages persist across panel open/close and page reloads

**Independent Test**: Send messages, close panel, reopen — verify messages still visible. Reload page — verify messages load.

**Acceptance Criteria** (from spec.md US8):
- Previous messages displayed when panel reopens
- Multi-turn context maintained for coherent dialogue (20-message window)
- First-time open shows welcome message
- 200-message cap enforced with auto-pruning

### Implementation for User Story 8

- [ ] T036 [US8] Implement conversation loading in `ChatWidget.tsx` — on first panel open, call `GET /api/chat/history` to load existing messages. Set `messages` state from response. If `conversation_id` is null (no prior conversation), display welcome message. Track `historyLoaded` boolean to avoid re-fetching on subsequent opens within same session
- [ ] T037 [US8] Implement welcome message in `ChatWidget.tsx` — when no conversation exists (first open), show a static assistant message: "Hi! I'm your Task Manager Assistant. I can help you create, list, complete, update, and delete tasks. Try typing 'Show all my tasks' or use the quick actions below!" (FR-021). This message is displayed locally, not stored in DB
- [ ] T038 [US8] Verify 20-message context window in `backend/src/services/chat_service.py` — ensure `get_context_messages()` returns only last 20 messages ordered by created_at ASC for AI context. This should already be implemented in T015 but verify it works with >20 messages (FR-026)
- [ ] T039 [US8] Verify 200-message cap with auto-pruning in `backend/src/services/chat_service.py` — ensure `store_message()` checks message count after insert and deletes oldest messages if count >200. Use `SELECT id FROM message WHERE conversation_id = ? ORDER BY created_at ASC LIMIT (count - 200)` then bulk delete (FR-027)

**Checkpoint**: Conversation history persists. Multi-turn dialogue coherent. Message cap enforced.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Responsive design, error handling, visual consistency across all stories

- [ ] T040 [P] Implement error states in `ChatWidget.tsx` — handle: (1) AI service unavailable (503) → show error message in chat with retry suggestion, (2) network error → show offline message, (3) JWT expired (401) → show "Session expired, please refresh" message. Match FR-022, edge cases from spec
- [ ] T041 [P] Implement AI reasoning trace logging in `backend/src/services/chat_service.py` — store tool_calls array and action type in Message metadata JSON field. Log each tool invocation with `logger.info(f"AI tool call: {tool_name}({args}) for user {user_id}")`. Ensures FR-017 observability
- [ ] T042 [P] Desktop panel polish in `ChatWidget.tsx` — 380px width, max 560px height, fixed bottom-right with 24px margin. Shadow: `shadow-xl shadow-purple-500/20`. Border: `border border-purple-500/20`. Rounded corners: `rounded-2xl`. Glass effect: `backdrop-blur-xl bg-gray-900/90` (NFR-001)
- [ ] T043 Glassmorphism consistency audit — verify all chat components use existing dashboard CSS classes (`glass-strong`, `card-dark`, `card-glow`, `btn-neon`, `input-dark`, `text-gradient`, `feature-card`) where applicable. Ensure neon purple/magenta gradient consistency (NFR-001)
- [ ] T044 Run quickstart.md validation — follow all 6 verification steps from `specs/003-phase3-ai-chatbot/quickstart.md`: (1) Open dashboard, (2) Click FAB, (3) Type "Show all my tasks", (4) Verify AI response, (5) Type "Add a task to test the chatbot with high priority", (6) Verify task appears in dashboard list

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001, T002) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 1 T004 only (frontend directory). Can start in parallel with Phase 2 backend work
- **US2 (Phase 4)**: Depends on Phase 2 (models + schemas) for backend. Depends on US1 (Phase 3) for frontend (ChatWidget exists)
- **US3 (Phase 5)**: Depends on US2 (Phase 4) — needs working send/receive loop
- **US4 (Phase 6)**: Depends on US2 (Phase 4) — needs working send/receive loop. Can run in parallel with US3
- **US5 (Phase 7)**: Depends on US4 (Phase 6) — needs list_tasks for disambiguation
- **US6 (Phase 8)**: Depends on US4 (Phase 6) — needs list_tasks for finding tasks. Can run in parallel with US5
- **US7 (Phase 9)**: Depends on US2 (Phase 4) — needs working chat input. Can run in parallel with US3-US6
- **US8 (Phase 10)**: Depends on US2 (Phase 4) — needs history endpoint wired. Can run in parallel with US3-US6
- **Polish (Phase 11)**: Depends on all user stories being complete

### Within Each User Story

- Backend implementation before frontend wiring (for stories with both)
- Models before services
- Services before API endpoints
- API endpoints before frontend integration
- Core implementation before polish

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Phase 2 T007 (schemas) can run in parallel with T005/T006 (models)
- US1 frontend work (Phase 3) can run in parallel with US2 backend work (Phase 4 T014-T018)
- US3 and US4 can run in parallel after US2 completes
- US5 and US6 can run in parallel after US4 completes
- US7 and US8 can run independently after US2 completes
- All Polish tasks marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (P1 Stories: US1 + US2 + US3)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational models (T005-T008)
3. Complete Phase 3: US1 — Chat widget opens/closes (T009-T013)
4. Complete Phase 4: US2 — Send/receive messages end-to-end (T014-T022)
5. Complete Phase 5: US3 — Create tasks via chat (T023-T025)
6. **STOP and VALIDATE**: Run quickstart.md steps 1-6
7. Deploy/demo if ready — core chatbot is functional

### Incremental Delivery (P2 Stories)

8. Add US4 — List/query tasks (T026-T027)
9. Add US5 — Complete/delete tasks (T028-T031)
10. Add US6 — Update tasks (T032-T033)
11. **VALIDATE**: Full CRUD via chat works

### Final Polish (P3 Stories)

12. Add US7 — Quick action pills (T034-T035)
13. Add US8 — Conversation history persistence (T036-T039)
14. Complete Phase 11 — Polish and validation (T040-T044)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing backend endpoints (tasks, auth, health) MUST NOT be modified (NFR-006)
- Total: 44 tasks across 11 phases
- New files: 5 backend, 7 frontend, 1 modified backend config, 1 modified backend main, 1 modified frontend DashboardClient
