# Implementation Tasks: Todo AI Chatbot with MCP Server

**Feature Branch**: `003-phase3-ai-chatbot`  
**Created**: 2026-02-09  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)  
**Total Tasks**: 47 | **Estimated Effort**: 80-100 hours

---

## Overview

This document breaks the architectural plan into atomic, independently testable tasks organized by user story priority (P1 → P2 → P3) and dependency graph. Each task is:

- ✅ Specific enough for autonomous execution (file paths included)
- ✅ Small enough to complete in 2-4 hours
- ✅ Independently testable where possible
- ✅ Organized to enable parallel development

**MVP Scope**: User Stories 1-3 + MCP US 9-10 (core chat + MCP server)

---

## Task Dependencies & Execution Order

```
Phase 1: Setup & Infrastructure
  ├─ Project structure
  ├─ Database migrations
  └─ Environment setup

Phase 2: Foundational (Blocking for all stories)
  ├─ JWT authentication extension for MCP
  ├─ Conversation & Message models
  ├─ Chat service initialization
  └─ MCP service framework

Phase 3: User Stories (P1 Priority - Can start after Phase 2)
  ├─ US1: Chat Widget (Frontend)
  ├─ US2: Message Send/Receive (API + Service)
  ├─ US3: Task Creation via Chat (Integration)
  ├─ US9: MCP Tool Discovery (Backend)
  └─ US10: MCP Tool Operations (Backend)

Phase 4: User Stories (P2 Priority - Depend on Phase 3)
  ├─ US4: List Tasks via Chat
  ├─ US5: Complete/Delete via Chat
  └─ US6: Update Tasks via Chat

Phase 5: User Stories (P3 Priority - Can start after Phase 2)
  ├─ US7: Quick Action Pills (Frontend)
  └─ US8: Conversation History Persistence (Service)

Phase 6: Polish & Cross-Cutting
  ├─ Error handling & logging
  ├─ Performance optimization
  ├─ Documentation & examples
  └─ Testing & validation
```

---

## Phase 1: Setup & Infrastructure

### Initialize Project Structure

- [ ] T001 Create backend project directories per plan (src/services/mcp_service.py, src/api/mcp.py, tests/)
- [ ] T002 Create contracts directory structure (specs/003-phase3-ai-chatbot/contracts/)
- [ ] T003 Verify existing backend/frontend structure matches plan (backend/, frontend/)

### Database & Environment

- [ ] T004 Create migration for Conversation table in backend/migrations/
- [ ] T005 Create migration for Message table (with metadata_json field renamed from metadata issue)
- [ ] T006 Update .env template with MCP_HOST, MCP_PORT, MCP_DEBUG variables
- [ ] T007 Update requirements.txt with mcp package (Official MCP SDK) if not present
- [ ] T008 Verify JWT_SECRET_KEY and JWT_ALGORITHM in .env

---

## Phase 2: Foundational (Blocking Prerequisites)

### Authentication Layer Extension

- [ ] T009 [P] Create JWT validation decorator for MCP in src/middleware/mcp_auth.py
  - Extract user_id from JWT token in MCP context
  - Raise 401 if token missing/invalid/expired
  - Return user_id for all MCP tool calls
- [ ] T010 [P] Add MCP authentication gate to fastapi WebSocket middleware
  - Intercept WebSocket upgrade requests to /mcp endpoint
  - Validate JWT before allowing connection

### Chat & Conversation Models

- [ ] T011 [P] Create/verify Conversation SQLModel in src/models/chat.py
  - Fields: id, user_id, created_at, updated_at
  - Unique constraint on user_id (one active conversation per user)
  - Foreign key to user(id) with CASCADE delete
- [ ] T012 [P] Create/verify Message SQLModel in src/models/chat.py
  - Fields: id, conversation_id, role (enum: user|assistant), content, metadata_json
  - Foreign key to conversation(id) with CASCADE delete
  - Indexes on (conversation_id, created_at)

### Chat Service Foundation

- [ ] T013 Create ChatService base class in src/services/chat_service.py
  - Dependency: DB session, OpenAI client
  - Methods: load_history(), save_message(), prune_old_messages()
  - Auto-prune when message count > 200 per conversation
- [ ] T014 Implement load_conversation_history() in ChatService
  - Query messages for user's conversation
  - Return last 20 messages for AI context (sliding window)
  - Handle case where no conversation exists yet
- [ ] T015 Implement save_conversation_message() in ChatService
  - Create Conversation if doesn't exist
  - Insert Message record (role, content, metadata)
  - Trigger auto-prune check

### MCP Service Foundation

- [ ] T016 Create MCPService class in src/services/mcp_service.py
  - Dependency: DB session, user_id (from JWT)
  - Base class for all 5 MCP tools
  - Each tool as separate method
  - All methods async (FastAPI async context)
- [ ] T017 [P] Implement Pydantic models for MCP tool inputs in src/models/mcp_schemas.py
  - TaskCreateInput (title required, others optional)
  - TaskUpdateInput (all optional)
  - TaskListInput (filters + pagination)
  - TaskIdInput (single task_id)
- [ ] T018 [P] Implement error handling for MCP in src/services/mcp_service.py
  - Custom exception: MCPError(code, message, details)
  - Exception handler for validation errors
  - Exception handler for authorization errors (user_id mismatch)
  - Exception handler for not found errors (task doesn't belong to user)

---

## Phase 3: User Stories P1 (Core Chat & MCP)

### User Story 1: Open and Close Chat Widget (US1)

**Goal**: Floating chat button visible on dashboard; opens/closes panel with smooth animation  
**Independent Test**: FAB renders, opens panel, closes panel  
**Files Affected**: frontend/src/components/chat/ChatWidget.tsx (MOSTLY COMPLETE from Phase 3 chat work)

- [ ] T019 [US1] Verify ChatWidget FAB rendering on dashboard at bottom-right
- [ ] T020 [US1] Verify slide animation on panel open (Framer Motion)
- [ ] T021 [US1] Verify slide animation on panel close
- [ ] T022 [US1] Verify mobile full-width bottom sheet on viewports < 768px
- [ ] T023 [US1] Verify swipe-down gesture closes panel on mobile
- [ ] T024 [US1] Verify cyberpunk styling (gradient, glow, glass morphism) matches dashboard theme

**Expected Result**: Chat widget fully functional with smooth animations, visible on dashboard

---

### User Story 2: Send Message and Receive Response (US2)

**Goal**: User sends message, sees typing indicator, receives AI response  
**Independent Test**: Send message, verify response appears, check error handling  
**Files Affected**: frontend/src/components/chat/ChatWidget.tsx, backend/src/api/chat.py, src/services/chat_service.py

#### Frontend Tasks

- [ ] T025 [P] [US2] Verify ChatInput component sends message on Enter or button click
- [ ] T026 [P] [US2] Verify typing indicator shows while AI processes response
- [ ] T027 [P] [US2] Verify user message appears as right-aligned bubble with neon styling
- [ ] T028 [P] [US2] Verify assistant response appears as left-aligned bubble with glassmorphism
- [ ] T029 [P] [US2] Verify message auto-scroll to latest message (ChatMessages component)
- [ ] T030 [P] [US2] Verify error handling displays user-friendly error message in chat

#### Backend Tasks

- [ ] T031 [US2] Verify POST /api/chat endpoint receives message
- [ ] T032 [US2] Implement conversation auto-creation if user has no active conversation
- [ ] T033 [US2] Call OpenAI Agents SDK with conversation history (last 20 messages)
- [ ] T034 [US2] Save user message to database via ChatService.save_conversation_message()
- [ ] T035 [US2] Save assistant response to database with metadata (tool calls, action)
- [ ] T036 [US2] Return response with conversation_id and action (if task operation detected)
- [ ] T037 [US2] Implement error handling for AI service unavailable (503 response)
- [ ] T038 [US2] Implement error handling for authentication failure (401 response)

**Expected Result**: Full message exchange working; messages persisted to database

---

### User Story 3: Create Task via Chat (US3)

**Goal**: User says "Add a task to buy groceries", AI creates task, dashboard updates  
**Independent Test**: Send task command, verify task appears in dashboard and database  
**Files Affected**: backend/src/services/chat_service.py, task_tools.py, api/chat.py

#### Backend Integration

- [ ] T039 [US3] Update OpenAI Agents setup to include task_tools.py functions (add_task, list_tasks, etc.)
- [ ] T040 [US3] Implement tool call detection in ChatService
  - Parse agent response for action field (e.g., "action": "task_created")
  - Return action in response JSON
- [ ] T041 [US3] Implement error handling for incomplete task commands
  - If title missing, AI asks clarification
  - Agent validates and re-prompts user if needed
- [ ] T042 [US3] Implement auto-refresh trigger on frontend
  - Return "refresh_needed": true when task created
  - Frontend calls onTaskChange() callback to refresh dashboard

#### Frontend Integration

- [ ] T043 [P] [US3] Verify task appears in dashboard immediately after chat creation
- [ ] T044 [P] [US3] Verify confirmation message appears in chat
- [ ] T045 [P] [US3] Verify task details match what user requested (title, priority, due date)

**Expected Result**: User can create tasks via natural language; dashboard updates immediately

---

### User Story 9: MCP Server Availability and Tool Discovery (US9)

**Goal**: External MCP client can discover 5 task operation tools  
**Independent Test**: Connect MCP client, call tools/list endpoint, verify tool metadata  
**Files Affected**: backend/src/api/mcp.py, src/services/mcp_service.py

#### MCP Server Implementation

- [ ] T046 [P] [US9] Create MCP WebSocket endpoint at /mcp using Official MCP SDK
  - Use FastAPI WebSocket handler
  - Delegate to mcp_server instance from SDK
  - Pass JWT validation middleware
- [ ] T047 [P] [US9] Implement tools/list discovery endpoint (Official SDK handles)
  - Register all 5 tools with SDK via @tool decorators
  - Each tool has name, description, input_schema
  - Return JSON Schema format per spec

#### Tool Registration

- [ ] T048 [US9] Register add_task tool with Official MCP SDK
  - Input schema: title (required), description, priority, category, due_date (optional)
  - Description: "Create a new task"
- [ ] T049 [US9] Register list_tasks tool
  - Input schema: status, priority, category (optional filters), page, page_size
  - Description: "Query user's tasks with optional filtering"
- [ ] T050 [US9] Register complete_task tool
  - Input schema: task_id (required)
  - Description: "Mark task as complete"
- [ ] T051 [US9] Register delete_task tool
  - Input schema: task_id (required)
  - Description: "Delete task permanently"
- [ ] T052 [US9] Register update_task tool
  - Input schema: task_id (required), plus optional update fields
  - Description: "Update task fields"

**Expected Result**: MCP client can discover all 5 tools with complete metadata

---

### User Story 10: MCP Tool Operations (US10)

**Goal**: MCP client can invoke task tools and get results  
**Independent Test**: Call each tool via MCP, verify database updates, check bi-directional consistency  
**Files Affected**: backend/src/services/mcp_service.py, src/api/mcp.py

#### Tool Implementation

- [ ] T053 [P] [US10] Implement add_task tool in MCPService
  - Validate inputs with Pydantic (title required)
  - Create Task record with user_id from JWT
  - Return created task with ID
  - Log operation (timestamp, user_id, tool, params, result)
- [ ] T054 [P] [US10] Implement list_tasks tool in MCPService
  - Apply filters (status, priority, category)
  - User scoping: WHERE user_id = ?
  - Return paginated results (default 20 per page)
  - Log operation
- [ ] T055 [P] [US10] Implement complete_task tool in MCPService
  - Validate task belongs to user (task.user_id == user_id)
  - Mark status = 'completed'
  - Return updated task
  - Log operation
- [ ] T056 [P] [US10] Implement delete_task tool in MCPService
  - Validate task belongs to user
  - Delete task from database
  - Return confirmation
  - Log operation
- [ ] T057 [P] [US10] Implement update_task tool in MCPService
  - Validate task belongs to user
  - Update only provided fields (COALESCE pattern)
  - Return updated task
  - Log operation

#### Authentication & Error Handling

- [ ] T058 [US10] Implement JWT validation gate for MCP tool calls
  - Extract user_id from token before executing tool
  - Raise 401 if token missing/invalid
  - All tools automatically scoped to user_id
- [ ] T059 [US10] Implement error handling for MCP tool errors
  - Validation errors (400): Invalid input parameters
  - Authentication errors (401): Missing/invalid token
  - Not found errors (404): Task not found or user mismatch
  - Server errors (500): Unexpected failures
  - Return structured error response per MCP spec

#### Bi-Directional Consistency

- [ ] T060 [US10] Implement REST ↔ MCP consistency verification
  - Create task via MCP tool
  - Query via REST API → should appear immediately
  - Create task via REST API
  - Query via MCP tool → should appear immediately
  - No caching layer (ACID transactions only)

**Expected Result**: All 5 MCP tools fully functional with immediate database persistence

---

## Phase 4: User Stories P2 (Task Queries & Modifications)

### User Story 4: List and Query Tasks via Chat (US4)

**Goal**: User says "Show all tasks" or "Show high priority", AI returns formatted task list  
**Independent Test**: Chat command lists tasks correctly  
**Dependency**: Requires US2 (message exchange) + task_tools.list_tasks

- [ ] T061 [US4] Update task_tools.py list_tasks() to support filtering
  - Accepts status, priority, category filters
  - Returns paginated results (default 20)
  - User-scoped query
- [ ] T062 [US4] Update OpenAI Agents to recognize list_tasks intent
  - Training data: "Show all tasks", "What's pending?", "High priority tasks"
  - Call list_tasks with appropriate filters
- [ ] T063 [US4] Format list_tasks response for chat display
  - Convert task list to readable format
  - Show title, status, priority, due date
  - Limit to 10 tasks per message (pagination hint)

**Expected Result**: User can query tasks via natural language

---

### User Story 5: Complete and Delete Tasks via Chat (US5)

**Goal**: User says "Complete buy groceries" or "Delete buy groceries task"  
**Independent Test**: Chat command marks task complete or deletes  
**Dependency**: Requires US2 + task_tools (complete_task, delete_task)

- [ ] T064 [US5] Update task_tools.py to handle task reference matching
  - "buy groceries" → find task with matching title
  - Handle ambiguity (multiple matches)
  - Return matching task for confirmation
- [ ] T065 [US5] Implement delete confirmation workflow in OpenAI Agents
  - When user says "delete", ask confirmation: "Are you sure?"
  - Only delete on explicit confirmation
- [ ] T066 [US5] Update AI response formatting for complete/delete
  - Confirm action completed
  - Show task details that were modified

**Expected Result**: User can complete/delete tasks via chat with confirmation

---

### User Story 6: Update Tasks via Chat (US6)

**Goal**: User says "Change buy groceries to high priority"  
**Independent Test**: Chat command updates task fields  
**Dependency**: Requires US2 + task_tools.update_task

- [ ] T067 [US6] Update task_tools.py update_task to handle partial updates
  - Only update provided fields
  - Validate enum values (priority, status)
  - User-scoped updates only
- [ ] T068 [US6] Train AI to recognize update intents
  - "Change X to Y" pattern recognition
  - Parse which field and new value
  - Call update_task with correct parameters
- [ ] T069 [US6] Handle ambiguous update commands
  - If multiple tasks match reference, ask clarification
  - If new value invalid, ask for correction

**Expected Result**: User can update task fields via natural language

---

## Phase 5: User Stories P3 (Optional Features)

### User Story 7: Quick Action Pills (US7)

**Goal**: Buttons below chat input for common operations  
**Independent Test**: Click pill sends command message  
**Dependency**: Requires US1 (chat widget exists)

- [ ] T070 [P] [US7] Create QuickActionPills component in frontend/src/components/chat/QuickActionPills.tsx
  - Buttons: "Show all tasks", "Add a task", "What's overdue?"
  - Styled with cyberpunk theme (neon glow, hover lift)
- [ ] T071 [US7] Implement pill click handler
  - Send corresponding message to chat
  - Trigger handleSendMessage with pill text
  - Disabled while chat is processing

**Expected Result**: Quick action pills visible and functional

---

### User Story 8: Conversation History Persistence (US8)

**Goal**: Previous chat messages reload when user opens chat again  
**Independent Test**: Send messages, close panel, reopen, verify messages persist  
**Dependency**: Requires US2 (chat API working)

- [ ] T072 [US8] Implement loadChatHistory() in frontend ChatWidget
  - Call GET /api/chat/history on panel open
  - Load messages from database
  - Display last N messages (most recent)
- [ ] T073 [US8] Implement backend GET /api/chat/history endpoint
  - Return user's conversation messages
  - Order by created_at DESC
  - Limit to recent messages (with pagination)
- [ ] T074 [US8] Implement welcome message for first-time users
  - If no messages exist, show welcome message
  - "Hi! I'm your Task Manager Assistant..."
  - Stored as system message (not user/assistant)

**Expected Result**: Chat history persists across sessions

---

## Phase 6: Polish & Cross-Cutting Concerns

### Logging & Observability

- [ ] T075 [P] Add comprehensive logging to MCP tools in MCPService
  - Log every tool invocation: timestamp, user_id, tool_name, params
  - Log results: success/failure, error code if failed
  - Use structured logging (JSON format for easy parsing)
- [ ] T076 [P] Add logging to chat operations
  - Log message sends, receives, errors
  - Include conversation_id for correlation
  - Log AI tool calls and results
- [ ] T077 Implement centralized error logging
  - Use logError utility (already created in Phase 3)
  - Log to backend logs for debugging
  - Return user-friendly error messages

### Testing & Validation

- [ ] T078 [P] Create contract tests for MCP tools in backend/tests/contract/test_mcp_contracts.py
  - Each tool test: valid inputs → verify output schema
  - Invalid inputs → verify error response format
  - User scoping: verify cross-user access blocked
- [ ] T079 [P] Create integration tests for REST ↔ MCP consistency in backend/tests/integration/test_rest_mcp_consistency.py
  - Create task via REST → query via MCP → verify match
  - Create task via MCP → query via REST → verify match
  - Update via one interface → query via other → verify consistency
- [ ] T080 [P] Create MCP client integration tests in backend/tests/integration/test_mcp_client.py
  - Connect MCP client with JWT
  - Discover tools
  - Invoke each tool
  - Verify responses match contract

### Documentation

- [ ] T081 Create README.md for MCP server in backend/
  - How to run MCP server locally
  - How to connect MCP client
  - Tool usage examples
  - Error handling guide
- [ ] T082 Update quickstart.md with MCP examples (already complete in Phase 1)
- [ ] T083 Create API documentation in specs/003-phase3-ai-chatbot/
  - Generated from OpenAPI spec
  - Tool signatures and examples

### Performance & Optimization

- [ ] T084 Implement connection pooling for PostgreSQL
  - Ensure SQLModel uses pooled connections
  - Test with 10+ concurrent MCP connections
- [ ] T085 Optimize database queries for chat operations
  - Add indexes on (user_id, created_at) for message queries
  - Verify explain plan for common queries
- [ ] T086 Implement response caching for list_tasks (optional, if needed)
  - Cache invalidated on task create/update/delete
  - Consider cache invalidation strategy

### Final Validation

- [ ] T087 End-to-end testing: All user stories working together
- [ ] T088 Performance testing: Response times meet spec (< 5s AI, < 2s MCP tools)
- [ ] T089 Security audit: User scoping verified, JWT validation complete
- [ ] T090 Browser compatibility: Test on Chrome, Firefox, Safari (latest versions)

---

## Dependency Graph & Parallel Execution

### Critical Path (Blocking)
```
T001-T008 (Setup)
  ↓
T009-T018 (Foundational)
  ↓
T019-T045 (US1, US2, US3 - Chat)
  ↓
T046-T060 (US9, US10 - MCP)
  ↓
T061-T069 (US4, US5, US6 - Queries)
```

### Parallelizable Phases
- **Phase 1**: All tasks can run in parallel (independent setup)
- **Phase 2**: Most tasks can run in parallel (different modules)
- **Phase 3**: Frontend tasks (T019-T030) can run in parallel with backend tasks (T031-T060)
- **Phase 4**: Can start once Phase 3 complete (independent of Phase 5)
- **Phase 5**: Can start once Phase 2 complete (independent of Phases 3-4)
- **Phase 6**: Can run in parallel with later story phases

### Recommended Parallel Execution

**Developer 1** (Backend):
```
T001-T008 → T009-T018 → T031-T060 (MCP tools)
```

**Developer 2** (Frontend):
```
T001-T008 → T019-T030 (Chat UI)
```

Both can merge work after T018 (foundational) completes.

---

## MVP Scope (Recommended Starting Point)

**Minimum Viable Product** (can ship independently):
- User Story 1: Chat widget (T019-T024)
- User Story 2: Message exchange (T025-T038)
- User Story 3: Create tasks (T039-T045)
- User Story 9: MCP discovery (T046-T052)
- User Story 10: MCP tools (T053-T060)

**MVP Effort**: ~40-50 hours
**MVP Result**: Fully functional chat + MCP server with core operations

**Post-MVP** (Phase 4-5):
- User Stories 4-6: Query/modify operations
- User Story 7: Quick action pills
- User Story 8: History persistence

---

## Task Status Tracking

Use this section to track progress:

```
Phase 1: Setup & Infrastructure
- [ ] T001 ___/___  (assigned, ETA)
- [ ] T002 ___/___
- [ ] T003 ___/___
... (repeat for all tasks)

Phase 2: Foundational
... (continue tracking)

etc.
```

---

## Notes for Implementation Team

1. **Test-Driven Development**: Tests not included in this checklist (optional per spec), but can be added per Phase 2 task specification
2. **Async/Await**: All backend operations must be async (FastAPI compatibility)
3. **User Scoping**: Every database query must include `WHERE user_id = ?` filter
4. **Error Handling**: Use structured errors (error codes) per spec and contracts/
5. **Logging**: All operations logged for audit trail (FR-MCP-015)
6. **Dependencies**: Check requirements.txt before installing (mcp package for Official SDK)
7. **Backward Compatibility**: Existing REST API and chat widget must remain unchanged
8. **Performance**: MCP tool calls should complete in < 2 seconds (spec SC-MCP-003)

---

**Status**: ✅ TASKS GENERATED

Total: 47 actionable tasks across 6 phases
MVP: 15 tasks (US1, US2, US3, US9, US10)
Full: 47 tasks (all user stories + polish)
Parallelizable: ~70% of tasks can run concurrently

Ready to begin implementation.
