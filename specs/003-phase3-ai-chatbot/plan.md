# Implementation Plan: Todo AI Chatbot with MCP Server Integration

**Branch**: `003-phase3-ai-chatbot` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-phase3-ai-chatbot/spec.md`

**Phases**: This plan covers Phase 0 (Research), Phase 1 (Design & Contracts), and will be followed by Phase 2 (Tasks Generation).

## Summary

**Primary Requirement**: Build an AI-powered conversational Todo chatbot using MCP (Model Context Protocol) server architecture while preserving all existing chat widget functionality. The feature adds an MCP server that exposes task operations as stateless tools via the Official MCP SDK, enabling external integration while maintaining bi-directional data consistency with the existing REST API.

**Technical Approach**:
1. **Phase 0 (Research)**: Validate MCP SDK integration patterns, confirm JWT/database sharing architecture, research Official MCP SDK best practices
2. **Phase 1 (Design)**: Define data model for MCP operations, create REST-based contracts for MCP tools (as internal endpoints), design authentication layer
3. **Key Architecture Decisions**:
   - MCP server runs on same FastAPI backend (not separate microservice)
   - Reuse existing SQLModel ORM and JWT authentication
   - Stateless tool design (all context in request parameters)
   - Bi-directional consistency between REST and MCP operations
   - Official MCP SDK for protocol compliance

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/Node 20+ (frontend)
**Primary Dependencies**:
  - Backend: FastAPI, SQLModel, Pydantic, python-jose (JWT), openai-agents (0.8.1+), mcp (Official SDK)
  - Frontend: Next.js 16+, Framer Motion, axios/fetch API
**Storage**: Neon PostgreSQL (serverless, existing for Phase 2+)
**Testing**: pytest (backend), Jest (frontend), integration tests for MCP client
**Target Platform**: Linux server (backend), modern web browsers (frontend)
**Project Type**: Web application (frontend + backend with new MCP layer)
**Performance Goals**:
  - AI response: < 5 seconds for chat messages
  - MCP tool calls: < 2 seconds per operation
  - Tool discovery: < 500ms (tools/list endpoint)
  - Chat panel: 60fps animations
**Constraints**:
  - JWT token < 5KB (existing pattern)
  - Conversation history: max 200 messages per user (auto-prune oldest)
  - AI context window: last 20 messages (sliding window)
  - Concurrent MCP connections: ≥ 10 without resource leaks
**Scale/Scope**:
  - 5 MCP tools (add_task, list_tasks, complete_task, delete_task, update_task)
  - 1 active conversation per user
  - Task operations: create, read, update, delete, complete via both REST and MCP
  - ~2-3 new backend endpoints for MCP integration
  - No frontend changes needed (MCP is server-side protocol)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principles Validation

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Specification First** | Complete spec before implementation | ✅ PASS | Spec.md complete with 42 FRs, 20 SCs, 10 user stories |
| **II. Deterministic Behavior** | Same input → same output; predictable system | ✅ PASS | MCP tools are stateless; JWT auth determines output; database is ACID |
| **III. Incremental Evolution** | Build on verified Phase 2 outcomes | ✅ PASS | Phase 2 (fullstack) complete; Phase 3 adds chat + MCP on top |
| **IV. Separation of Concerns** | Layers independently testable & replaceable | ✅ PASS | Chat widget, AI agent, MCP tools, REST API all independent |
| **V. Testability (NON-NEGOTIABLE)** | All features verifiable via deterministic tests | ⚠️ NEEDS PLAN | Test-first approach for MCP tools required; contract tests for tool invocations |
| **VI. Observability** | Structured logs, metrics, tracing at every phase | ✅ PASS | Error logging fixed (Phase 3 frontend); MCP logging spec'd (FR-MCP-015) |
| **VII. AI Constraint & Explainability** | AI responses follow predefined intents; explainable | ✅ PASS | OpenAI Agents SDK + MCP both bound to predefined task operations only |
| **VIII. Simplicity & YAGNI** | No speculative features; justify complexity | ✅ PASS | MCP is justified by spec requirements; stateless design is simple |

**GATE RESULT**: ✅ PASS (with testability plan required in Phase 2 tasks)

### Phase III Constraints

| Constraint | Status | Detail |
|-----------|--------|--------|
| **Technology Stack** | ✅ OK | OpenAI ChatKit, Agents SDK, Official MCP SDK (per constitution) |
| **AI Constraint** | ✅ OK | AI responses follow 5 predefined task operations only (FR-MCP-002 to FR-MCP-006) |
| **Safety** | ✅ OK | No hallucinated actions outside defined Todo operations (spec validates this) |
| **Explainability** | ✅ OK | All AI decisions logged with reasoning traces (FR-MCP-015, chat logging complete) |
| **No Breaking Changes** | ✅ OK | Existing REST API unchanged; chat widget preserved; backward compatible |

**CONSTITUTION COMPLIANCE**: ✅ APPROVED

## Project Structure

### Documentation (this feature)

```text
specs/003-phase3-ai-chatbot/
├── plan.md              # This file (implementation architecture)
├── research.md          # Phase 0 output (TBD via /sp.plan Phase 0)
├── spec.md              # Feature specification (COMPLETE)
├── data-model.md        # Phase 1 output (TBD via /sp.plan Phase 1)
├── quickstart.md        # Phase 1 output (TBD via /sp.plan Phase 1)
├── checklists/
│   └── requirements.md   # Specification quality checklist (COMPLETE)
└── contracts/           # Phase 1 output (TBD via /sp.plan Phase 1)
    ├── mcp-tools.openapi.yaml       # MCP tools as internal endpoints
    ├── chat-api.openapi.yaml        # Chat API (existing, preserved)
    └── authentication.yaml          # JWT validation layer (shared)
```

### Source Code (repository root)

```text
# Web application structure (existing from Phase 2, with MCP additions)

backend/
├── src/
│   ├── models/
│   │   ├── chat.py              # Chat models (COMPLETE - fixed metadata issue)
│   │   ├── task.py              # Task models (existing)
│   │   └── user.py              # User models (existing)
│   │
│   ├── services/
│   │   ├── chat_service.py      # Chat AI orchestration (EXISTING - FIXED)
│   │   ├── task_tools.py        # AI tools for task operations (EXISTING - 6 tools)
│   │   └── mcp_service.py       # NEW: MCP server integration
│   │
│   ├── api/
│   │   ├── chat.py              # Chat endpoints (EXISTING)
│   │   ├── tasks.py             # Task endpoints (EXISTING)
│   │   └── mcp.py               # NEW: MCP transport & tool routing
│   │
│   └── middleware/
│       └── auth.py              # JWT validation (EXISTING, reused)
│
└── tests/
    ├── unit/
    │   ├── test_mcp_tools.py     # NEW: MCP tool unit tests
    │   └── test_task_ops.py      # Existing task operation tests
    │
    ├── integration/
    │   ├── test_mcp_client.py    # NEW: MCP client integration tests
    │   ├── test_chat_api.py      # Existing chat API tests
    │   └── test_rest_mcp_consistency.py  # NEW: Bi-directional consistency
    │
    └── contract/
        └── test_mcp_contracts.py # NEW: MCP tool contract tests

frontend/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWidget.tsx       # Chat panel (EXISTING - error logging fixed)
│   │   │   ├── ChatHeader.tsx       # (existing)
│   │   │   ├── ChatMessages.tsx     # (existing)
│   │   │   ├── ChatInput.tsx        # (existing)
│   │   │   └── QuickActionPills.tsx # (existing)
│   │   └── ...
│   │
│   ├── lib/
│   │   ├── errorLogger.ts       # Error logging utility (NEW - complete)
│   │   ├── api.ts               # API client (EXISTING)
│   │   └── auth.ts              # Auth utilities (EXISTING)
│   │
│   └── pages/
│       └── dashboard.tsx         # Dashboard host (EXISTING)
│
└── tests/
    └── chat/
        └── integration/          # Chat widget integration tests (EXISTING)
```

**Structure Decision**:
- **Option 2 (Web Application)** - Existing backend/frontend split maintained
- **MCP as Backend Service Layer**: MCP server is NOT a separate microservice but a new service layer within the existing FastAPI backend
- **New Files (Backend)**:
  - `src/services/mcp_service.py` - Core MCP tool implementations
  - `src/api/mcp.py` - MCP transport layer (WebSocket/HTTP)
  - `tests/integration/test_mcp_client.py` - Client integration tests
  - `tests/integration/test_rest_mcp_consistency.py` - Data consistency tests
  - `tests/unit/test_mcp_tools.py` - Tool unit tests
  - `tests/contract/test_mcp_contracts.py` - Contract tests
- **New Files (Contracts)**:
  - `specs/003-phase3-ai-chatbot/contracts/mcp-tools.openapi.yaml` - Internal tool endpoints
  - `specs/003-phase3-ai-chatbot/contracts/authentication.yaml` - JWT validation (shared)
- **Modified Files**:
  - `backend/src/services/chat_service.py` - Already fixed, no additional changes
  - `backend/src/models/chat.py` - Already fixed for metadata issue
- **Frontend**: No changes needed (MCP is server-side only)

## Complexity Tracking

> No Constitution Check violations. All complexity is justified by specification requirements and Principle VIII (Simplicity & YAGNI).

| Design Choice | Why Needed | Simpler Alternative Rejected Because |
|---------------|-----------|-------------------------------------|
| MCP Server on same backend | Unified auth + database | Separate microservice adds deployment complexity without benefit for MVP |
| Stateless tool design | Concurrent connection handling | Stateful approach requires session management and recovery logic |
| 5 separate MCP tools | Spec-driven requirement (FR-MCP-002 to FR-MCP-006) | Single generic tool would lose semantic meaning |
| Bi-directional consistency | Spec requirement (SC-MCP-006, SC-MCP-007) | Eventual consistency would require eventual-consistency infrastructure |

---

## Architecture Overview

### Layer 1: Authentication (Shared)

**Existing JWT Validation** (from Phase 2, reused):
- Token issued by Better Auth
- Validated by middleware in both REST and MCP
- Contains user ID + email
- Expires per configured duration
- No changes needed - MCP reuses this layer

**MCP Authentication Gate** (NEW):
```
MCP Client connects → Provides JWT token in request headers
→ JWT Middleware validates token
→ Token decoded to extract user_id
→ All subsequent tool calls scoped to user_id
```

### Layer 2: MCP Tools (NEW)

**MCP Tool Service** (`src/services/mcp_service.py`):
```
MCP Tool Call (tool_name, parameters, user_id from JWT)
→ Route to corresponding tool handler
→ Each tool validates inputs (Pydantic models)
→ Each tool operates on database (SQLModel ORM)
→ Each tool returns structured response
→ Each tool invocation logged (FR-MCP-015)
```

**5 Tools Implemented**:
1. **add_task**(user_id, title, description, priority, category, due_date)
   - Creates task in database
   - Returns created task with ID
   - Validates inputs (title required, priority enum, etc.)

2. **list_tasks**(user_id, status, priority, category, page, page_size)
   - Queries database with filters
   - Returns paginated results
   - Applies user scoping (WHERE user_id = ?)

3. **complete_task**(user_id, task_id)
   - Marks task as complete
   - Returns updated task
   - Validates task ownership (task.user_id == user_id)

4. **delete_task**(user_id, task_id)
   - Deletes task from database
   - Returns confirmation
   - Validates task ownership

5. **update_task**(user_id, task_id, title, description, priority, category, due_date, status)
   - Updates only provided fields
   - Returns updated task
   - Validates task ownership

**Design Pattern**:
- Each tool is a pure function: (inputs, user_id) → result
- No side effects beyond database writes
- All database writes use SQLModel ORM (existing)
- All operations immediately consistent (ACID transactions)

### Layer 3: MCP Transport (NEW)

**MCP Server** (`src/api/mcp.py`):
```
FastAPI MCP endpoint (WebSocket or HTTP)
→ Official MCP SDK handles protocol negotiation
→ SDK calls tool methods from mcp_service.py
→ SDK returns responses to client
→ No business logic in transport layer
```

**Official MCP SDK Usage**:
- Use `@MCP.tool` decorator or equivalent Official SDK pattern
- Handles tools/list discovery endpoint
- Handles tool invocation routing
- Returns structured errors per MCP spec
- Supports WebSocket transport (primary) + HTTP fallback

**No Custom Protocol Implementation** - Official SDK handles all MCP details

### Layer 4: Chat System (PRESERVED)

**Existing Chat Widget** (frontend, unchanged):
- User types message
- Sends to `/api/chat` endpoint (existing REST)
- Receives response from OpenAI Agents SDK
- Agent internally may call task tools (existing pattern)

**Chat Service** (`src/services/chat_service.py`, already fixed):
- Receives message
- Constructs context (last 20 messages)
- Calls OpenAI Agents with task tools available
- Agent decides which task operation to invoke
- Results stored in database

**Key Point**: Chat widget does NOT use MCP directly. MCP is for external clients only.

### Data Flow Diagrams

#### Scenario 1: REST API Task Creation
```
Client → POST /api/tasks
  ↓
REST Endpoint → Validate JWT
  ↓
Task Service → SQLModel ORM → PostgreSQL
  ↓
Response → Client
```

#### Scenario 2: Chat-based Task Creation
```
Chat Widget → POST /api/chat
  ↓
Chat Service → OpenAI Agent
  ↓
Agent (internal) → task_tools.add_task()
  ↓
add_task() → SQLModel ORM → PostgreSQL
  ↓
Chat Service → Format response
  ↓
Response → Chat Widget
```

#### Scenario 3: MCP Client Task Creation
```
MCP Client → Connect with JWT
  ↓
MCP Transport → Validate JWT
  ↓
MCP Tool (add_task) → mcp_service.py
  ↓
add_task() → SQLModel ORM → PostgreSQL
  ↓
MCP Response → Client
```

**Key**: All three paths write to same PostgreSQL database → Immediate consistency

---

## Implementation Strategy

### Phase 0: Research (This Plan - IN PROGRESS)

**Research Tasks** (via agent delegation):
1. ✅ Official MCP SDK integration patterns - Confirm WebSocket vs HTTP transport
2. ✅ JWT validation in async context - FastAPI middleware pattern
3. ✅ PostgreSQL transaction handling for concurrent writes - ACID guarantees
4. ⏳ MCP tool discovery endpoint format - tools/list response schema
5. ⏳ MCP error response standards - Error codes and formats

**Deliverables**:
- `research.md` - Consolidated findings with decision rationale

### Phase 1: Design & Contracts

**Design Tasks**:
1. **Data Model** (`data-model.md`):
   - Confirm Task entity schema (existing from Phase 2)
   - Define MCP tool input schemas (Pydantic models)
   - Define MCP tool response schemas

2. **API Contracts** (`contracts/`):
   - `mcp-tools.openapi.yaml` - Internal tool endpoint specs
   - `authentication.yaml` - JWT validation layer
   - Tool signatures with parameter definitions

3. **Quickstart** (`quickstart.md`):
   - How to run MCP server locally
   - How to connect MCP client for testing
   - Example MCP tool invocations

**Deliverables**:
- `data-model.md` - Complete data model
- `contracts/mcp-tools.openapi.yaml` - Tool signatures
- `contracts/authentication.yaml` - JWT validation pattern
- `quickstart.md` - Development guide

### Phase 2: Task Generation

**NOT in this `/sp.plan` output** - Will be generated by `/sp.tasks` command

Will generate actionable, dependency-ordered tasks for:
1. Create MCP service module (`src/services/mcp_service.py`)
2. Create MCP transport layer (`src/api/mcp.py`)
3. Write MCP tool unit tests
4. Write MCP integration tests
5. Test REST ↔ MCP consistency
6. Add observability/logging
7. Documentation and quickstart

---

## Success Criteria for This Plan

| Criterion | How to Verify |
|-----------|---------------|
| Technical Context complete | All NEEDS CLARIFICATION resolved |
| Constitution Check passes | All principles verified ✅ |
| Architecture is clear | Data flows documented and justified |
| No implementation ambiguity | Contracts and data model ready for coding |
| Phase 1 deliverables ready | research.md, data-model.md, contracts/ prepared |

**Status**: ⏳ In Progress - Phase 0 research tasks pending

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| MCP SDK learning curve | Low | Official SDK is well-documented; start with hello-world example |
| JWT validation in async context | Low | FastAPI has built-in async support; use existing auth middleware |
| Database transaction isolation | Low | PostgreSQL ACID guarantees; SQLModel handles transactions |
| Concurrent MCP connections | Medium | Test with 10+ simultaneous connections; monitor resource usage |
| REST ↔ MCP data sync | Medium | Immediate consistency (same ACID transactions); contract tests verify |
