# MCP Server Implementation for Todo AI Chatbot

## Overview

This document describes the MCP (Model Context Protocol) server implementation for the Todo Application, which exposes task management operations as stateless tools that can be consumed by MCP-compatible clients.

## Architecture

### Components

1. **MCP Service Layer** (`src/services/mcp_service.py`)
   - Core tool implementations (add_task, list_tasks, complete_task, delete_task, update_task)
   - Pydantic validation models
   - Error handling and response formatting
   - User context validation

2. **MCP API Layer** (`src/api/mcp.py`)
   - FastAPI REST endpoints exposing MCP tools
   - JWT authentication via Authorization header
   - HTTP status code mapping
   - Tool discovery endpoint

3. **Authentication Middleware** (`src/middleware/mcp_auth.py`)
   - JWT token validation
   - User ID extraction
   - Reuses existing security infrastructure

## API Endpoints

### Tool Discovery

```
GET /api/mcp/tools/list
```

Returns manifest of all available MCP tools with schemas. **No authentication required.**

**Response:**
```json
{
  "tools": [
    {
      "name": "add_task",
      "description": "Create a new task...",
      "input_schema": {
        "type": "object",
        "properties": {...},
        "required": ["title"]
      }
    },
    ...
  ]
}
```

### Tool Invocation

All tool endpoints require JWT authentication via `Authorization: Bearer <token>` header.

#### 1. add_task

```
POST /api/mcp/tools/add_task?title=<title>&priority=<priority>&...
```

**Parameters:**
- `title` (required): Task title (1-200 chars)
- `description` (optional): Task description
- `priority` (optional): low/medium/high (default: medium)
- `category` (optional): Category/tag
- `due_date` (optional): ISO format YYYY-MM-DD

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "...",
    "priority": "high",
    ...
  },
  "message": "Task 'title' created successfully"
}
```

#### 2. list_tasks

```
GET /api/mcp/tools/list_tasks?status_filter=<status>&priority=<priority>&...
```

**Parameters:**
- `status_filter` (optional): all/pending/completed (default: all)
- `priority` (optional): low/medium/high
- `category` (optional): Filter by category
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": {
    "tasks": [...],
    "total": 10,
    "filters": {...}
  },
  "message": "Found 10 tasks"
}
```

#### 3. complete_task

```
POST /api/mcp/tools/complete_task?task_id=<id>
```

**Parameters:**
- `task_id` (required): ID of task to mark complete

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "completed": true,
    ...
  },
  "message": "Task 'title' marked as completed"
}
```

#### 4. delete_task

```
DELETE /api/mcp/tools/delete_task?task_id=<id>
```

**Parameters:**
- `task_id` (required): ID of task to delete

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted_task_id": 123,
    "deleted_task_title": "..."
  },
  "message": "Task 'title' deleted successfully"
}
```

#### 5. update_task

```
PUT /api/mcp/tools/update_task?task_id=<id>&title=<new_title>&...
```

**Parameters:**
- `task_id` (required): ID of task to update
- `title` (optional): New title
- `description` (optional): New description
- `priority` (optional): New priority
- `category` (optional): New category
- `due_date` (optional): New due date (ISO format)

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "Updated Title",
    ...
  },
  "message": "Task 'title' updated successfully (title, priority)"
}
```

## Error Handling

All errors follow MCP protocol format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additional": "context"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT token |
| `NOT_FOUND` | 404 | Task not found or no access |
| `INTERNAL_ERROR` | 500 | Server error |

## Authentication

All MCP tool endpoints (except `/tools/list`) require JWT authentication.

**Header Format:**
```
Authorization: Bearer <jwt_token>
```

**Token Requirements:**
- Valid signature (verified against BETTER_AUTH_SECRET)
- Not expired
- Contains `id` field (user_id)
- Contains `email` field

**User Scoping:**
All operations are automatically scoped to the authenticated user. Users can only:
- Create tasks for themselves
- List their own tasks
- Complete/delete/update only their own tasks

## Data Consistency

MCP operations write to the same PostgreSQL database as REST API endpoints, ensuring:
- **Immediate Consistency**: Changes via MCP are instantly visible via REST and vice versa
- **ACID Transactions**: All operations are atomic
- **User Isolation**: Proper user_id scoping prevents data leakage

### Consistency Examples

```python
# Create via MCP → Query via REST
POST /api/mcp/tools/add_task?title=Test
GET /api/tasks  # Task appears immediately

# Update via REST → Verify via MCP
PUT /api/tasks/123 {"priority": "high"}
GET /api/mcp/tools/list_tasks  # Shows updated priority

# Delete via MCP → Verify via REST
DELETE /api/mcp/tools/delete_task?task_id=123
GET /api/tasks/123  # Returns 404
```

## Testing

### Unit Tests

```bash
pytest tests/test_mcp_tools.py -v
```

Tests all 5 MCP tools with:
- Input validation
- User scoping
- Error handling
- Response formatting

### Integration Tests

```bash
pytest tests/integration/test_mcp_api.py -v
```

Tests FastAPI endpoints with:
- Authentication
- HTTP status codes
- Tool discovery
- End-to-end flows

### Consistency Tests

```bash
pytest tests/integration/test_rest_mcp_consistency.py -v
```

Tests bi-directional consistency:
- Create via MCP → Query via REST
- Create via REST → Query via MCP
- Update/delete operations
- Concurrent operations

## Usage Examples

### Python MCP Client (Pseudo-code)

```python
import requests

BASE_URL = "http://localhost:8001/api/mcp"
TOKEN = "your_jwt_token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Discover tools
tools = requests.get(f"{BASE_URL}/tools/list").json()
print(tools["tools"])

# Create task
response = requests.post(
    f"{BASE_URL}/tools/add_task",
    params={
        "title": "Buy groceries",
        "priority": "high",
        "due_date": "2026-03-15"
    },
    headers=headers
)
task = response.json()["data"]
task_id = task["id"]

# List tasks
response = requests.get(
    f"{BASE_URL}/tools/list_tasks",
    params={"status_filter": "pending"},
    headers=headers
)
tasks = response.json()["data"]["tasks"]

# Complete task
response = requests.post(
    f"{BASE_URL}/tools/complete_task",
    params={"task_id": task_id},
    headers=headers
)

# Delete task
response = requests.delete(
    f"{BASE_URL}/tools/delete_task",
    params={"task_id": task_id},
    headers=headers
)
```

### cURL Examples

```bash
# Tool discovery (no auth)
curl http://localhost:8001/api/mcp/tools/list

# Create task
curl -X POST "http://localhost:8001/api/mcp/tools/add_task?title=Test+Task&priority=high" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# List tasks
curl "http://localhost:8001/api/mcp/tools/list_tasks?status_filter=pending" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Complete task
curl -X POST "http://localhost:8001/api/mcp/tools/complete_task?task_id=123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Update task
curl -X PUT "http://localhost:8001/api/mcp/tools/update_task?task_id=123&priority=high" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Delete task
curl -X DELETE "http://localhost:8001/api/mcp/tools/delete_task?task_id=123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Performance

All MCP tool operations meet the following performance targets:

- **Tool Discovery**: < 500ms
- **Tool Invocation**: < 2 seconds (simple operations)
- **List Operations**: < 2 seconds (up to 100 tasks)
- **Concurrent Connections**: ≥ 10 simultaneous connections

## Logging

All MCP operations are logged with:
- Timestamp
- User ID
- Tool name
- Parameters (sanitized)
- Result status

Log format:
```
[MCP_TOOL] add_task: Created task 123 for user user_abc
[MCP_TOOL] list_tasks: Found 5 tasks for user user_abc
[MCP_TOOL] complete_task: Marked task 123 complete for user user_abc
```

## Security

### Authentication
- JWT validation on all tool endpoints
- Token signature verification
- Expiration checking
- User ID extraction

### User Scoping
- All queries include `WHERE user_id = ?`
- No cross-user data access
- Task ownership validation on complete/delete/update

### Input Validation
- Pydantic models for all inputs
- Type coercion and validation
- SQL injection prevention via parameterized queries

## Future Enhancements

### WebSocket Transport
Currently using REST endpoints. Future versions could add WebSocket transport using Official MCP SDK:

```python
from mcp import Server

mcp_server = Server("todo-mcp-server")

@mcp_server.tool()
async def add_task(...):
    # Tool implementation
    pass
```

### Pagination
Currently returns all matching tasks. Future versions could add proper pagination:

```python
# Offset-based pagination
offset = (page - 1) * page_size
query = query.limit(page_size).offset(offset)
```

### Filtering Enhancements
- Date range filters (due_date_from, due_date_to)
- Full-text search on title/description
- Multiple category filtering
- Sorting options (due_date, priority, created_at)

### Batch Operations
- Bulk create/update/delete
- Transaction support for multiple operations
- Rollback on partial failure

## Troubleshooting

### Common Issues

**Issue:** 401 Unauthorized
- **Cause:** Missing or invalid JWT token
- **Fix:** Ensure `Authorization: Bearer <token>` header is present and token is valid

**Issue:** 404 Not Found
- **Cause:** Task doesn't exist or belongs to different user
- **Fix:** Verify task ID and user ownership

**Issue:** 400 Validation Error
- **Cause:** Invalid input parameters
- **Fix:** Check parameter format (especially date format: YYYY-MM-DD)

**Issue:** 500 Internal Server Error
- **Cause:** Database connection or server error
- **Fix:** Check logs, verify database connection, ensure environment variables are set

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs for:
- `[MCP_TOOL]` - Tool execution logs
- `[MCP_AUTH]` - Authentication logs
- `[MCP_API]` - API endpoint logs

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Validation](https://docs.pydantic.dev/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
