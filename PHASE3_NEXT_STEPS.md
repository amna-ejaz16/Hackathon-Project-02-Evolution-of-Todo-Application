# Phase 3: MCP Server Implementation - Next Steps

**Prerequisites**: ✅ ALL Phase 1-2 infrastructure complete (see MCP_INFRASTRUCTURE_COMPLETE.md)

---

## Quick Start: Run Database Migration

**CRITICAL FIRST STEP**: Create the conversation and message tables before proceeding.

```bash
# From project root
cd backend

# Load environment variables
export $(cat .env | xargs)

# Run migration
psql "$DATABASE_URL" < migrations/001_create_chat_tables.sql

# Verify tables created
psql "$DATABASE_URL" -c "\d conversation"
psql "$DATABASE_URL" -c "\d message"
```

**Expected output**:
- `conversation` table with 5 columns
- `message` table with 6 columns
- 3 indexes created

---

## Phase 3 Implementation Order

### User Story 1: MCP Server Initialization (US1)
**Status**: Not started
**BLOCKING**: Must complete before all other user stories

#### Tasks

**T019**: Create MCP server module with Official SDK
- **File**: `backend/src/mcp_server.py`
- **Requirements**:
  - Import `mcp` package (Official MCP SDK)
  - Create `MCPServer` instance
  - Configure WebSocket transport on `MCP_PORT` (8001)
  - Set up logging and error handling
  - Register shutdown handlers

**T020**: Implement tool discovery endpoint
- **Endpoint**: `/mcp/tools` (GET)
- **Response**: Tool manifest from `create_mcp_tools_manifest()`
- **Auth**: No auth required (public endpoint for discovery)

**T021**: Register all 5 MCP tools with server
- **Tools**: add_task, list_tasks, complete_task, delete_task, update_task
- **Registration**: Call `server.register_tool()` for each
- **Context**: Inject database session and JWT middleware

#### Implementation Template

```python
# backend/src/mcp_server.py
from mcp import MCPServer, WebSocketTransport
from .services.mcp_service import create_mcp_tools_manifest
from .core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class TodoMCPServer:
    """MCP server for Todo task management operations."""

    def __init__(self):
        self.settings = get_settings()
        self.server = MCPServer(
            name="todo-task-manager",
            version="1.0.0"
        )
        self.transport = WebSocketTransport(
            host=self.settings.mcp_host,
            port=self.settings.mcp_port
        )

    def register_tools(self):
        """Register all MCP tools with the server."""
        # Import tool implementations here
        # self.server.register_tool(add_task_tool)
        # self.server.register_tool(list_tasks_tool)
        # etc.
        pass

    async def start(self):
        """Start the MCP server."""
        self.register_tools()
        logger.info(f"Starting MCP server on {self.settings.mcp_host}:{self.settings.mcp_port}")
        await self.server.start(self.transport)

    async def stop(self):
        """Stop the MCP server."""
        await self.server.stop()
        logger.info("MCP server stopped")
```

#### Acceptance Criteria
- [ ] MCP server starts without errors
- [ ] WebSocket listening on port 8001
- [ ] `/mcp/tools` endpoint returns manifest with 6 tools
- [ ] Graceful shutdown on SIGTERM

---

### User Story 2: Add Task via MCP (US2)
**Status**: Not started
**Dependencies**: US1 (server initialization)

#### Tasks

**T022**: Implement add_task tool function
- **File**: `backend/src/services/mcp_tools/add_task.py`
- **Base class**: Extend `MCPToolBase`
- **Input**: `TaskCreateInput` (Pydantic validation)
- **Output**: Success response with task_id and confirmation message

**T023**: Add JWT authentication to add_task
- **Decorator**: Use `@require_mcp_auth`
- **Context**: Extract `user_id` from JWT token
- **Scope**: Create task owned by authenticated user

**T024**: Write unit tests for add_task
- **File**: `backend/tests/test_mcp_tools_add.py`
- **Coverage**:
  - Valid input creates task
  - Invalid priority defaults to "medium"
  - Invalid due_date raises validation error
  - Missing title raises validation error
  - Missing token raises 401
  - Task owned by correct user_id

#### Implementation Template

```python
# backend/src/services/mcp_tools/add_task.py
from typing import Dict, Any
from datetime import date
from sqlmodel import Session
from ..mcp_service import MCPToolBase, TaskCreateInput, MCPError
from ...models.task import Task
from ...middleware.mcp_auth import require_mcp_auth
import logging

logger = logging.getLogger(__name__)

class AddTaskTool(MCPToolBase):
    """MCP tool for creating new tasks."""

    @require_mcp_auth
    async def execute(self, context: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task for the authenticated user.

        Args:
            context: MCP context with user_id (injected by auth middleware)
            input_data: Task creation parameters

        Returns:
            Success response with task details
        """
        try:
            # Validate user context
            user_id = self._validate_user_context(context)

            # Validate input
            validated_input = TaskCreateInput(**input_data)

            # Parse due_date if provided
            parsed_due_date = None
            if validated_input.due_date:
                parsed_due_date = date.fromisoformat(validated_input.due_date)

            # Create task
            task = Task(
                user_id=user_id,
                title=validated_input.title,
                description=validated_input.description,
                priority=validated_input.priority,
                category=validated_input.category,
                due_date=parsed_due_date
            )

            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)

            logger.info(f"[MCP_ADD_TASK] Created task {task.id} for user {user_id}")

            # Format response
            return self._format_success_response(
                data={
                    "task_id": task.id,
                    "title": task.title,
                    "priority": task.priority,
                    "category": task.category,
                    "due_date": str(task.due_date) if task.due_date else None
                },
                message=f"Created task '{task.title}' (ID: {task.id})"
            )

        except Exception as e:
            logger.error(f"[MCP_ADD_TASK] Error: {type(e).__name__}: {e}", exc_info=True)
            return self._format_error_response(e)
```

#### Acceptance Criteria
- [ ] add_task creates task in database
- [ ] Task owned by authenticated user
- [ ] Returns task_id in response
- [ ] All validation errors caught and formatted
- [ ] 401 error if token invalid

---

### User Story 3: List Tasks via MCP (US3)
**Status**: Not started
**Dependencies**: US1

#### Tasks

**T025**: Implement list_tasks tool function
- **File**: `backend/src/services/mcp_tools/list_tasks.py`
- **Input**: `TaskListInput` (status, priority, category filters)
- **Output**: Array of tasks with formatting

**T026**: Add filtering and sorting
- **Filters**: status (all/pending/completed), priority, category
- **Sort**: created_at DESC (newest first)
- **Limit**: No limit (return all matching tasks)

**T027**: Format task list response
- **Format**: Numbered list with status icon, priority emoji, title, details
- **Empty state**: "No tasks found" message

#### Acceptance Criteria
- [ ] list_tasks returns all user tasks (no other user's tasks)
- [ ] Filters work correctly (status, priority, category)
- [ ] Response formatted as numbered list
- [ ] Empty state handled gracefully

---

### User Story 4: Complete/Uncomplete Task via MCP (US4)
**Status**: Not started
**Dependencies**: US1

#### Tasks

**T028**: Implement complete_task tool
- **File**: `backend/src/services/mcp_tools/complete_task.py`
- **Input**: `TaskIdInput` (task_id)
- **Operation**: Set `completed = True`, update `updated_at`

**T029**: Implement uncomplete_task tool
- **File**: `backend/src/services/mcp_tools/uncomplete_task.py`
- **Input**: `TaskIdInput` (task_id)
- **Operation**: Set `completed = False`, update `updated_at`

**T030**: Add ownership validation
- **Check**: Verify task.user_id == context.user_id
- **Error**: 404 if not found or not owned

**T031**: Write integration tests
- **File**: `backend/tests/test_mcp_tools_complete.py`
- **Coverage**: State transitions, ownership validation, 404 errors

#### Acceptance Criteria
- [ ] complete_task marks task as completed
- [ ] uncomplete_task marks task as not completed
- [ ] Cannot modify other user's tasks (404 error)
- [ ] updated_at timestamp updated

---

### User Story 5: Update/Delete Task via MCP (US5)
**Status**: Not started
**Dependencies**: US1

#### Tasks

**T032**: Implement update_task tool
- **File**: `backend/src/services/mcp_tools/update_task.py`
- **Input**: `TaskUpdateInput` + task_id
- **Operation**: Partial update (only update provided fields)

**T033**: Implement delete_task tool
- **File**: `backend/src/services/mcp_tools/delete_task.py`
- **Input**: `TaskIdInput` (task_id)
- **Operation**: Permanent delete from database

**T034**: Add transaction handling
- **Update**: Wrap in transaction, rollback on error
- **Delete**: Cascade to related records (none in this case)

**T035**: Write comprehensive tests
- **File**: `backend/tests/test_mcp_tools_update_delete.py`
- **Coverage**: Partial updates, validation, ownership, deletion

#### Acceptance Criteria
- [ ] update_task updates only provided fields
- [ ] delete_task permanently removes task
- [ ] Ownership validated for both operations
- [ ] Transactions rollback on error

---

## Testing Strategy

### Unit Tests
Run after each user story:
```bash
cd backend
pytest tests/test_mcp_infrastructure.py -v
pytest tests/test_mcp_tools_*.py -v
```

### Integration Tests
Create MCP client tests:
```python
# backend/tests/test_mcp_integration.py
import asyncio
from mcp.client import MCPClient

async def test_mcp_add_task_integration():
    """Test add_task via MCP client."""
    client = MCPClient("ws://localhost:8001")
    await client.connect()

    # Call add_task tool
    response = await client.call_tool(
        tool_name="add_task",
        arguments={
            "title": "Test Task",
            "priority": "high"
        },
        context={
            "token": "Bearer <valid_jwt_token>"
        }
    )

    assert response["success"] is True
    assert "task_id" in response["data"]

    await client.disconnect()
```

### Manual Testing with Claude Desktop
1. Configure Claude Desktop to connect to MCP server
2. Send messages: "Create a task called 'Buy groceries'"
3. Verify task created in database
4. Test filtering: "Show me all high priority tasks"

---

## Deployment Checklist

### Before Production

- [ ] Run all migrations
- [ ] Environment variables set (MCP_HOST, MCP_PORT, MCP_DEBUG)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run test suite: `pytest backend/tests/ -v`
- [ ] Configure WebSocket proxy (if behind nginx/load balancer)
- [ ] Set up monitoring for MCP server health
- [ ] Document MCP endpoint for clients

### Production Settings

```bash
# .env.production
MCP_HOST=0.0.0.0  # Listen on all interfaces
MCP_PORT=8001
MCP_DEBUG=false   # Disable debug logging
```

---

## Troubleshooting

### Common Issues

**Issue**: "Table 'conversation' does not exist"
**Solution**: Run migration script (see Quick Start above)

**Issue**: "Module 'mcp' not found"
**Solution**: `pip install -r requirements.txt`

**Issue**: "Authentication failed (401)"
**Solution**: Verify JWT token is valid and not expired

**Issue**: "WebSocket connection refused"
**Solution**: Check MCP_PORT (8001) is not in use, firewall allows connections

---

## Success Metrics

### Phase 3 Complete When:

1. **MCP server starts successfully** on port 8001
2. **All 6 tools registered** and discoverable via `/mcp/tools`
3. **JWT authentication works** for all tools
4. **User data isolation enforced** (no cross-user data access)
5. **All unit tests pass** (100% coverage for MCP tools)
6. **Integration tests pass** with real MCP client
7. **Manual testing successful** with Claude Desktop or similar MCP client

---

## Timeline Estimate

- **US1 (MCP Server Init)**: 4-6 hours
- **US2 (Add Task)**: 3-4 hours
- **US3 (List Tasks)**: 3-4 hours
- **US4 (Complete/Uncomplete)**: 2-3 hours
- **US5 (Update/Delete)**: 3-4 hours
- **Testing & Documentation**: 4-6 hours

**Total**: ~20-30 hours for complete Phase 3 implementation

---

## Support Resources

### Documentation
- Official MCP SDK: https://github.com/modelcontextprotocol/python-sdk
- FastAPI WebSocket: https://fastapi.tiangolo.com/advanced/websockets/
- Pydantic Validation: https://docs.pydantic.dev/latest/

### Reference Implementation
- See `backend/src/services/task_tools.py` for similar tool patterns (OpenAI Agents SDK)
- Use `backend/src/middleware/mcp_auth.py` for all authentication
- Extend `backend/src/services/mcp_service.py::MCPToolBase` for all tools

---

**Ready to Start**: All infrastructure is in place. Proceed with US1 (MCP Server Initialization).
