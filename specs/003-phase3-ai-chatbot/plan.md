# Implementation Plan: Todo AI Chatbot - Cyberpunk UI/UX

**Branch**: `003-phase3-ai-chatbot` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-phase3-ai-chatbot/spec.md`

## Summary

Add an AI-powered floating chat widget to the existing dashboard that enables users to manage tasks via natural language. The backend uses OpenAI Agents SDK with `@function_tool` decorators wrapping existing task CRUD operations. The frontend is a cyberpunk-themed chat panel built with React + Framer Motion + Tailwind CSS. Conversations are persisted in Neon PostgreSQL with a 200-message cap and 20-message AI context window.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/Node.js 20+ (frontend)
**Primary Dependencies**: OpenAI Agents SDK `openai-agents>=0.8.0` (backend), Framer Motion (frontend, existing)
**Storage**: Neon PostgreSQL (existing) — new tables: `conversation`, `message`
**Testing**: pytest (backend), manual + visual (frontend)
**Target Platform**: Web (Next.js 15+ frontend, FastAPI backend on Linux)
**Project Type**: Web application (monorepo with `frontend/` + `backend/`)
**Performance Goals**: AI response <5s, animations 60fps, chat open <500ms
**Constraints**: Existing backend endpoints (tasks, auth) MUST NOT be modified (NFR-006)
**Scale/Scope**: Single-user conversations, 200 messages max, ~10 new files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification First | PASS | Spec created and clarified before planning |
| II. Deterministic Behavior | PASS | AI constrained to predefined intents/tools (FR-018); same tool call → same DB operation |
| III. Incremental Evolution | PASS | Builds on Phase 2 verified outcomes; existing code untouched (NFR-006) |
| IV. Separation of Concerns | PASS | AI logic (services/), API layer (api/chat.py), UI components (components/chat/) all separated |
| V. Testability | PASS | Tool functions testable independently; API endpoint testable with pytest; UI testable visually |
| VI. Observability | PASS | FR-017 requires all AI decisions logged with reasoning traces |
| VII. AI Constraint & Explainability | PASS | FR-018 constrains to task intents only; metadata stores tool calls and reasoning |
| VIII. Simplicity & YAGNI | PASS | Single chat endpoint, callback for refresh (no global state), no MCP server overhead |

**Phase III Standards Check**:
- Technology: OpenAI Agents SDK (matches constitution "Agents SDK") ✓
- AI Constraints: `@function_tool` + agent instructions enforce bounded operations ✓
- Safety: Agent instructions explicitly prohibit non-task actions ✓
- Explainability: Message metadata stores tool_calls and reasoning traces ✓

## Project Structure

### Documentation (this feature)

```text
specs/003-phase3-ai-chatbot/
├── plan.md              # This file
├── research.md          # Phase 0: Technology research
├── data-model.md        # Phase 1: Conversation + Message entities
├── quickstart.md        # Phase 1: Developer setup guide
├── contracts/
│   └── chat-api.yaml    # Phase 1: OpenAPI contract for chat endpoints
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── chat.py              # NEW: POST /api/chat, GET /api/chat/history
│   │   ├── tasks.py             # EXISTING (unchanged)
│   │   ├── health.py            # EXISTING (unchanged)
│   │   └── deps.py              # EXISTING (unchanged)
│   ├── models/
│   │   ├── chat.py              # NEW: Conversation, Message, ChatRequest, ChatResponse
│   │   ├── task.py              # EXISTING (unchanged)
│   │   └── user.py              # EXISTING (unchanged)
│   ├── services/
│   │   ├── chat_service.py      # NEW: Agent setup, message processing, history management
│   │   └── task_tools.py        # NEW: @function_tool wrappers for task CRUD
│   ├── core/
│   │   ├── config.py            # MODIFIED: add OPENAI_API_KEY setting
│   │   ├── database.py          # EXISTING (auto-creates new tables)
│   │   └── security.py          # EXISTING (unchanged)
│   └── main.py                  # MODIFIED: register chat router
└── requirements.txt             # MODIFIED: add openai-agents, openai

frontend/
├── src/
│   ├── components/
│   │   └── chat/                # NEW: All chat UI components
│   │       ├── ChatWidget.tsx
│   │       ├── ChatHeader.tsx
│   │       ├── ChatMessages.tsx
│   │       ├── ChatMessage.tsx
│   │       ├── ChatInput.tsx
│   │       ├── TypingIndicator.tsx
│   │       └── QuickActionPills.tsx
│   ├── app/
│   │   └── dashboard/
│   │       └── DashboardClient.tsx  # MODIFIED: embed ChatWidget with onTaskChange callback
│   └── lib/
│       └── api.ts               # EXISTING (unchanged — chat uses same apiFetch)
└── package.json                 # EXISTING (no new dependencies)
```

**Structure Decision**: Web application pattern (Option 2). New files added to existing `backend/src/` and `frontend/src/` directories. No new top-level directories. Chat components organized under `frontend/src/components/chat/` following component colocation pattern.

## Implementation Phases

### Phase A: Backend — Models & Database (Foundation)

**Files**: `backend/src/models/chat.py`

1. Create `Conversation` SQLModel (table=True) with fields: id, user_id, title, created_at, updated_at
2. Create `Message` SQLModel (table=True) with fields: id, conversation_id, role, content, metadata, created_at
3. Create Pydantic schemas: `ChatRequest`, `ChatResponse`, `ChatHistoryResponse`, `MessageRead`
4. Tables auto-created by existing `create_db_and_tables()` — import models in `database.py`

**Dependencies**: None (foundational)

### Phase B: Backend — Task Tool Functions

**Files**: `backend/src/services/task_tools.py`

1. Define `@function_tool` for each task operation:
   - `add_task(title, description, priority, category, due_date)` → calls existing `Task` model + session
   - `list_tasks(status, priority, category)` → queries tasks table
   - `complete_task(task_id)` → sets `completed=True`
   - `delete_task(task_id)` → removes task
   - `update_task(task_id, title, description, priority, category, due_date)` → partial update
2. Each tool receives `user_id` via function context/closure (scoped per request)
3. Each tool returns a string description of what happened (for AI to relay to user)

**Dependencies**: Phase A (models)

### Phase C: Backend — Chat Service (Agent Orchestration)

**Files**: `backend/src/services/chat_service.py`, `backend/src/core/config.py`

1. Add `OPENAI_API_KEY` to `Settings` in config.py
2. Create `ChatService` class:
   - `get_or_create_conversation(user_id, session)` → returns Conversation
   - `get_context_messages(conversation_id, session, limit=20)` → last 20 messages
   - `store_message(conversation_id, role, content, metadata, session)` → saves + prunes if >200
   - `process_message(user_message, user_id, session)` → full flow:
     - Get/create conversation
     - Store user message
     - Fetch context (last 20)
     - Create Agent with task tools (user_id bound)
     - Run agent via `Runner.run()`
     - Store assistant response with metadata
     - Return ChatResponse with action type

**Dependencies**: Phase A (models), Phase B (tools)

### Phase D: Backend — Chat API Endpoint

**Files**: `backend/src/api/chat.py`, `backend/src/main.py`

1. Create `POST /api/chat` endpoint:
   - Auth: `get_current_user` dependency (existing)
   - Input: `ChatRequest` (message string)
   - Process: call `ChatService.process_message()`
   - Output: `ChatResponse` (response, conversation_id, action, task_id)
   - Error handling: 503 for AI service errors, 422 for validation
2. Create `GET /api/chat/history` endpoint:
   - Auth: `get_current_user` dependency
   - Query param: `limit` (default 50)
   - Returns: `ChatHistoryResponse` (messages array, conversation_id)
3. Register chat router in `main.py` at prefix `/api/chat`
4. Add CORS — no changes needed (existing wildcard methods)

**Dependencies**: Phase C (chat service)

### Phase E: Frontend — Chat UI Components

**Files**: `frontend/src/components/chat/*.tsx`

1. `ChatWidget.tsx`: FAB button + panel container
   - State: `isOpen` boolean
   - FAB: fixed bottom-right, neon gradient, hover lift animation
   - Panel: conditional render, slide animation (desktop: side panel, mobile: bottom sheet)
   - Props: `onTaskChange: () => void` callback
2. `ChatHeader.tsx`: AI avatar icon, "Task Manager Assistant" title, close button, gradient strip
3. `ChatMessages.tsx`: Scrollable container, auto-scroll to bottom on new messages, ref-based scroll
4. `ChatMessage.tsx`: User bubble (right, neon) vs assistant bubble (left, glass), fade+slide entrance
5. `ChatInput.tsx`: Dark glass input, neon focus ring, gradient send button, Enter to submit, disabled when sending
6. `TypingIndicator.tsx`: Three pulsing dots with staggered animation
7. `QuickActionPills.tsx`: Static pills ("Show all tasks", "Add a task", "What's overdue?"), neon glow, hover lift

**Dependencies**: None (can be built with mock data in parallel with backend)

### Phase F: Frontend — Chat API Integration & Dashboard Wiring

**Files**: `frontend/src/components/chat/ChatWidget.tsx`, `frontend/src/app/dashboard/DashboardClient.tsx`

1. Wire `ChatWidget` to backend API:
   - `POST /api/chat` via existing `api.post()` (sends JWT automatically)
   - `GET /api/chat/history` via `api.get()` on panel open
   - Handle loading states, errors, typing indicator
2. Implement message state management inside `ChatWidget`:
   - `messages[]` state array
   - `isSending` boolean for typing indicator
   - Load history on first open
   - Append user message → show indicator → append AI response
3. Auto-refresh dashboard: check `action` field in `ChatResponse`
   - If action is `task_created`, `task_updated`, `task_completed`, `task_uncompleted`, `task_deleted` → call `onTaskChange()`
4. Embed `ChatWidget` in `DashboardClient`:
   - Pass `onTaskChange={fetchTasks}` as callback
   - Render at end of component (portal or absolute positioned)

**Dependencies**: Phase D (backend API), Phase E (UI components)

### Phase G: Responsive Design & Polish

1. Mobile bottom-sheet behavior (< 768px):
   - Full-width panel, swipe-down gesture to dismiss (Framer Motion drag)
   - Touch-friendly input sizing
2. Desktop side-panel:
   - 380px width, 560px height, fixed bottom-right positioning
   - Shadow and border glow effects
3. Welcome message on first open (no conversation history)
4. Error states in chat (AI unavailable, network error)
5. Glassmorphism consistency: match existing `glass-strong`, `card-dark`, `card-glow` classes

**Dependencies**: Phase E, Phase F

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| AI Framework | OpenAI Agents SDK (`@function_tool`) | Built-in tool calling loop, no manual orchestration needed |
| MCP Server | Not used (deferred) | `@function_tool` is simpler and sufficient; MCP adds inter-process overhead |
| Chat API | Single `POST /api/chat` | Minimal API surface; agent handles all tool routing internally |
| Conversation Storage | SQLModel tables in Neon PostgreSQL | Reuses existing DB; consistent with Phase 2 patterns |
| Dashboard Refresh | Callback prop (`onTaskChange`) | Simplest pattern; no global state library needed |
| Frontend Chat UI | Custom components (no ChatKit) | Full control over cyberpunk theme; ChatKit is not an installable library |
| Context Window | Last 20 messages | Balances dialogue coherence with API cost/speed |
| Message Cap | 200 per conversation | Bounds storage; oldest pruned automatically |

## Complexity Tracking

No constitution violations. All complexity is justified by spec requirements.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI API latency >5s | User perceives chatbot as slow | Typing indicator provides feedback; timeout with user-friendly error |
| OpenAI API key exposure | Security breach | Key stored in `.env`, never committed; backend-only access |
| AI hallucinates non-existent tasks | User confusion, data integrity | Agent instructions + tool return values constrain behavior; disambiguation flow |
| Mobile swipe gesture conflicts with scroll | UX bug | Swipe only on panel header, not message area |
| Token cost overruns | Unexpected bills | 20-message context window limits tokens per request; can add rate limiting later |
