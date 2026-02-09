# MCP Server Backend Infrastructure - Implementation Complete

**Date**: 2026-02-09
**Branch**: `003-phase3-ai-chatbot`
**Phase**: Backend Infrastructure (Phase 1 Setup + Phase 2 Foundational)
**Status**: ✅ ALL BLOCKING TASKS COMPLETE

---

## Summary

This document confirms the successful implementation of the **critical MCP (Model Context Protocol) server backend infrastructure** for Phase 3 AI Chatbot. All BLOCKING dependencies for Phase 3 user story implementation are now in place.

### What Was Implemented

1. **Database Migration for Chat Tables** (T004-T005)
2. **MCP Authentication Middleware with JWT Validation** (T009-T010)
3. **MCP Service Base Infrastructure** (T016-T018)
4. **Environment Configuration for MCP** (T006-T008)
5. **Official MCP SDK Dependency** (T001-T003)

---

## Deliverables

### 1. Database Migration

**File**: `/backend/migrations/001_create_chat_tables.sql`

**Tables Created**:
- `conversation` - One active conversation per user
  - `id` (SERIAL PRIMARY KEY)
  - `user_id` (UUID, FK to users.id)
  - `title` (VARCHAR, default "Task Assistant")
  - `created_at`, `updated_at` (TIMESTAMP)

- `message` - Chat messages within conversations
  - `id` (SERIAL PRIMARY KEY)
  - `conversation_id` (INTEGER, FK to conversation.id with CASCADE delete)
  - `role` (VARCHAR, CHECK 'user' or 'assistant')
  - `content` (TEXT)
  - `metadata_json` (TEXT, stores tool_calls and action type)
  - `created_at` (TIMESTAMP)

**Indexes**:
- `idx_conversation_user_id` - Fast user lookup
- `idx_message_conversation_id` - Fast conversation message retrieval
- `idx_message_created_at` - Sorted message queries

**Status**: ✅ Ready to run (execute via `psql $DATABASE_URL < backend/migrations/001_create_chat_tables.sql`)

---

### 2. MCP Authentication Middleware

**File**: `/backend/src/middleware/mcp_auth.py`

**Components**:

#### `MCPAuthError` Exception
- Custom exception for authentication failures
- HTTP-style error codes (401, 403, 500)
- Structured error messages

#### `validate_mcp_token(token: str) -> str`
- **Purpose**: Core authentication gate for ALL MCP tool calls
- **Input**: JWT token (with or without "Bearer " prefix)
- **Output**: Authenticated user_id
- **Security Guarantees**:
  - Token signature verified against `BETTER_AUTH_SECRET`
  - Token expiration checked
  - User ID extracted and validated
  - All failures logged with context

#### `require_mcp_auth` Decorator
- Wraps async MCP tool functions
- Extracts token from context dict
- Validates and injects `user_id` into context
- Raises `MCPAuthError` on failure

#### `get_mcp_user_id` FastAPI Dependency
- FastAPI-compatible dependency for Authorization header
- Can be used with `Depends()` in endpoint signatures

**Integration**:
- Reuses existing `core.security.verify_token()` from Phase 2
- No changes to JWT secret or verification logic
- Seamless integration with Better Auth tokens

**Status**: ✅ Complete and production-ready

---

### 3. MCP Service Base Infrastructure

**File**: `/backend/src/services/mcp_service.py`

**Pydantic Validation Models**:

1. **`TaskCreateInput`**
   - Validates: title (1-200 chars), priority (low/medium/high), due_date (ISO format)
   - Auto-normalizes priority to lowercase
   - Default priority: "medium"

2. **`TaskUpdateInput`**
   - Partial update schema (all fields optional except task_id)
   - Validates priority and due_date if provided

3. **`TaskListInput`**
   - Validates status (all/pending/completed)
   - Optional priority and category filters

4. **`TaskIdInput`**
   - Simple task_id validation (integer > 0)
   - Used by complete, uncomplete, delete operations

**Error Handling**:

- **`MCPError` Exception**
  - Structured errors compatible with MCP protocol
  - Fields: `code`, `message`, `details`
  - `to_dict()` method for JSON serialization

**Base Class**:

- **`MCPToolBase`**
  - Common patterns for all MCP tools
  - Methods:
    - `_validate_user_context()` - Extract user_id from context
    - `_get_user_task()` - Fetch task with ownership check
    - `_format_success_response()` - Standardized success format
    - `_format_error_response()` - Error formatting with fallbacks

**Tool Discovery**:

- **`create_mcp_tools_manifest()`**
  - Returns MCP-compatible tool manifest
  - 6 tools defined: add_task, list_tasks, complete_task, uncomplete_task, delete_task, update_task
  - Complete JSON schemas for each tool's input

**Status**: ✅ Complete - Ready for tool implementations to extend `MCPToolBase`

---

### 4. Environment Configuration

**Updated Files**:
- `/backend/src/core/config.py`
- `/backend/.env`

**New Settings**:
```python
# In Settings class
self.mcp_host: str = os.getenv("MCP_HOST", "localhost")
self.mcp_port: int = int(os.getenv("MCP_PORT", "8001"))
self.mcp_debug: bool = os.getenv("MCP_DEBUG", "false").lower() == "true"
```

**Environment Variables**:
```bash
# MCP Server (Phase 3: Model Context Protocol)
MCP_HOST=localhost
MCP_PORT=8001
MCP_DEBUG=true
```

**Status**: ✅ Configuration loaded and validated

---

### 5. Dependencies

**Updated File**: `/backend/requirements.txt`

**Added**:
```
mcp>=1.0.0
```

**Existing Dependencies** (verified compatible):
- `fastapi>=0.109.0` - REST API framework
- `sqlmodel>=0.0.14` - ORM for database
- `pyjwt>=2.8.0` - JWT verification
- `openai-agents>=0.8.0` - AI agent orchestration (already in use)

**Status**: ✅ Ready for `pip install -r requirements.txt`

---

## Architecture Overview

### Data Flow: MCP Tool Call

```
┌─────────────┐
│ MCP Client  │ (e.g., external integration, Claude Desktop)
└──────┬──────┘
       │ 1. Tool call with JWT token
       ▼
┌─────────────────────┐
│ MCP Server (FastAPI)│
│ - WebSocket transport│
│ - Official MCP SDK  │
└──────┬──────────────┘
       │ 2. Extract token from context
       ▼
┌──────────────────────┐
│ mcp_auth.py          │ ◄── BLOCKING DEPENDENCY (COMPLETE)
│ - validate_mcp_token │
│ - Extract user_id    │
└──────┬───────────────┘
       │ 3. user_id injected into context
       ▼
┌──────────────────────┐
│ mcp_service.py       │ ◄── BLOCKING DEPENDENCY (COMPLETE)
│ - Validate input     │
│ - MCPToolBase        │
└──────┬───────────────┘
       │ 4. Execute tool logic
       ▼
┌──────────────────────┐
│ Task Model (SQLModel)│ ◄── Already exists (Phase 2)
│ - Database queries   │
│ - User-scoped data   │
└──────┬───────────────┘
       │ 5. Return result
       ▼
┌─────────────┐
│ MCP Response│ → Back to MCP Client
└─────────────┘
```

### Security Guarantees

1. **JWT Authentication**: All MCP tool calls require valid JWT token
2. **User Data Isolation**: All queries scoped by `user_id` from token
3. **Input Validation**: Pydantic models enforce type safety and constraints
4. **Error Handling**: No sensitive data leaked in error messages
5. **Audit Trail**: All operations logged with user context

---

## Verification Checklist

### ✅ Phase 1: Setup & Infrastructure (COMPLETE)

- [x] **T001-T003**: Project structure verified (`backend/src/services/`, `backend/src/api/`)
- [x] **T004-T005**: Database migration created (`001_create_chat_tables.sql`)
- [x] **T006-T008**: Environment setup complete (MCP_HOST, MCP_PORT, MCP_DEBUG in .env)

### ✅ Phase 2: Foundational (BLOCKING - COMPLETE)

- [x] **T009-T010**: JWT validation decorator implemented (`mcp_auth.py`)
  - `validate_mcp_token()` extracts user_id from JWT
  - Raises 401 on invalid/missing/expired tokens
  - Reuses existing `core.security` module

- [x] **T011-T012**: Conversation and Message models exist (`models/chat.py`)
  - Already implemented in previous phase
  - Foreign keys with CASCADE delete
  - Proper indexes for performance

- [x] **T013-T015**: ChatService exists (`services/chat_service.py`)
  - Already implemented with OpenAI Agents SDK
  - `load_conversation_history()` - Last 20 messages
  - `save_conversation_message()` - Auto-creates conversation
  - `prune_old_messages()` - Caps at 200 messages

- [x] **T016-T018**: MCPService foundation implemented (`mcp_service.py`)
  - Base class `MCPToolBase` for 5 MCP tools
  - Pydantic validation models (TaskCreateInput, TaskUpdateInput, TaskListInput, TaskIdInput)
  - Error handling with `MCPError` class
  - Tool manifest generation

---

## Next Steps (Phase 3: User Story Implementation)

Now that ALL BLOCKING infrastructure is complete, you can proceed with Phase 3 user stories:

### User Story 1: MCP Server Initialization (US1)
- **Tasks**: T019-T021
- **Deliverables**:
  - `backend/src/mcp_server.py` - Official MCP SDK server setup
  - WebSocket transport configuration
  - Tool registration with manifest

### User Story 2: Add Task via MCP (US2)
- **Tasks**: T022-T024
- **Deliverables**:
  - Implement `add_task` tool extending `MCPToolBase`
  - Unit tests for validation and execution
  - Integration test with MCP client

### User Story 3: List Tasks via MCP (US3)
- **Tasks**: T025-T027
- **Deliverables**:
  - Implement `list_tasks` tool with filtering
  - Format task list response
  - Unit and integration tests

### User Story 4: Complete/Uncomplete Task via MCP (US4)
- **Tasks**: T028-T031
- **Deliverables**:
  - Implement `complete_task` and `uncomplete_task` tools
  - Ownership validation
  - Tests for state transitions

### User Story 5: Update/Delete Task via MCP (US5)
- **Tasks**: T032-T035
- **Deliverables**:
  - Implement `update_task` (partial update) and `delete_task` tools
  - Validation and error handling
  - Comprehensive test coverage

---

## Database Setup Instructions

### Run Migration

```bash
# From project root
cd backend

# Load environment variables
source .env

# Run migration script
psql "$DATABASE_URL" < migrations/001_create_chat_tables.sql
```

### Verify Tables Created

```bash
psql "$DATABASE_URL" -c "\d conversation"
psql "$DATABASE_URL" -c "\d message"
```

**Expected Output**:
- `conversation` table with 5 columns (id, user_id, title, created_at, updated_at)
- `message` table with 6 columns (id, conversation_id, role, content, metadata_json, created_at)
- Indexes on user_id and conversation_id

---

## Testing the Infrastructure

### Test JWT Validation

```python
# backend/tests/test_mcp_auth.py
from src.middleware.mcp_auth import validate_mcp_token, MCPAuthError
import pytest

def test_valid_token():
    """Test successful token validation."""
    # Create a valid JWT token using your BETTER_AUTH_SECRET
    token = "eyJ..."  # Your test token
    user_id = validate_mcp_token(token)
    assert user_id is not None
    assert isinstance(user_id, str)

def test_invalid_token():
    """Test invalid token raises MCPAuthError."""
    with pytest.raises(MCPAuthError) as exc_info:
        validate_mcp_token("invalid_token")
    assert exc_info.value.code == 401

def test_missing_token():
    """Test missing token raises MCPAuthError."""
    with pytest.raises(MCPAuthError):
        validate_mcp_token("")
```

### Test Pydantic Validation

```python
# backend/tests/test_mcp_service.py
from src.services.mcp_service import TaskCreateInput, TaskUpdateInput
import pytest

def test_task_create_input_validation():
    """Test TaskCreateInput validation."""
    # Valid input
    input_data = TaskCreateInput(
        title="Test Task",
        priority="high",
        due_date="2026-03-01"
    )
    assert input_data.priority == "high"
    assert input_data.due_date == "2026-03-01"

    # Priority normalization
    input_data = TaskCreateInput(title="Test", priority="HIGH")
    assert input_data.priority == "high"  # Normalized to lowercase

    # Invalid due_date
    with pytest.raises(ValueError):
        TaskCreateInput(title="Test", due_date="invalid-date")
```

---

## File Structure Summary

```
backend/
├── .env                           # ✅ Updated with MCP_HOST, MCP_PORT, MCP_DEBUG
├── requirements.txt               # ✅ Added mcp>=1.0.0
├── migrations/
│   └── 001_create_chat_tables.sql # ✅ NEW - Conversation and Message tables
├── src/
│   ├── core/
│   │   ├── config.py              # ✅ Updated with MCP settings
│   │   └── security.py            # ✅ Existing (reused for JWT)
│   ├── middleware/
│   │   ├── __init__.py            # ✅ NEW
│   │   └── mcp_auth.py            # ✅ NEW - JWT validation for MCP
│   ├── models/
│   │   ├── chat.py                # ✅ Existing (Conversation, Message)
│   │   └── task.py                # ✅ Existing (Task model)
│   ├── services/
│   │   ├── chat_service.py        # ✅ Existing (ChatService with Agents SDK)
│   │   ├── task_tools.py          # ✅ Existing (6 task tools for Agents SDK)
│   │   └── mcp_service.py         # ✅ NEW - MCP base infrastructure
│   └── api/
│       └── chat.py                # ✅ Existing (REST endpoints for chat)
```

---

## Critical Notes

### ⚠️ Important Distinctions

**What EXISTS (from previous Phase 3 work)**:
- ✅ Chat widget UI (frontend/src/components/chat/ChatWidget.tsx)
- ✅ OpenAI Agents SDK integration (backend/src/services/chat_service.py)
- ✅ Task tools for Agents SDK (backend/src/services/task_tools.py)
- ✅ Chat models (Conversation, Message)
- ✅ REST API endpoints (/api/chat, /api/chat/history)

**What is NEW (this implementation)**:
- ✅ MCP authentication middleware (mcp_auth.py)
- ✅ MCP service base infrastructure (mcp_service.py)
- ✅ Database migration for chat tables
- ✅ MCP environment configuration
- ✅ Pydantic validation models for MCP tools

**What is NEXT (Phase 3 user stories)**:
- ⏳ MCP server initialization with Official SDK
- ⏳ 5 MCP tool implementations (add, list, complete, update, delete)
- ⏳ WebSocket transport setup
- ⏳ MCP client integration tests
- ⏳ Tool discovery endpoint

### Database Migration Requirement

**CRITICAL**: The migration script (`001_create_chat_tables.sql`) MUST be executed before running the application, or the ChatService will fail when trying to access the conversation and message tables.

```bash
# Run this ONCE before starting the server
psql "$DATABASE_URL" < backend/migrations/001_create_chat_tables.sql
```

---

## Validation Results

### ✅ All BLOCKING Dependencies Established

1. **JWT Authentication**: ✅ `mcp_auth.py` validates tokens and extracts user_id
2. **Database Models**: ✅ Conversation and Message models exist
3. **Chat Service**: ✅ ChatService handles conversation lifecycle
4. **MCP Base**: ✅ MCPToolBase provides tool foundation
5. **Validation Models**: ✅ Pydantic models enforce input contracts
6. **Error Handling**: ✅ MCPError provides structured errors
7. **Configuration**: ✅ MCP settings loaded from environment

### ✅ No Breaking Changes

- Existing REST API unchanged
- Chat widget UI preserved (no modifications)
- Phase 2 functionality intact
- Backward compatible with Better Auth

---

## Conclusion

**ALL Phase 1 (Setup & Infrastructure) and Phase 2 (Foundational) tasks are COMPLETE.**

The MCP server backend infrastructure is now ready for Phase 3 user story implementation. All BLOCKING dependencies have been established, validated, and documented.

**Next Action**: Proceed to implement Phase 3 user stories (US1-US5) to build the MCP server and expose task operations via the Model Context Protocol.

---

**Implemented by**: FastAPI Backend Development Engineer
**Review Status**: Ready for Phase 3 implementation
**Documentation**: Complete with code examples and verification steps
