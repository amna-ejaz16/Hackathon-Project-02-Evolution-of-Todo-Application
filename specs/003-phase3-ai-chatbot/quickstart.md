# Quickstart: Local Development

**Date**: 2026-02-09
**Purpose**: Get MCP server + chat running locally
**Status**: Planned (for implementation phase)

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (local or Docker)
- pip + npm
- Git

---

## Part 1: Backend Setup (FastAPI + MCP Server)

### 1. Install Backend Dependencies

```bash
cd backend
python -m venv venv

# Activate venv
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install requirements (includes mcp, fastapi, sqlmodel, python-jose)
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` file in backend directory:
```env
# Database (Neon or local PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db

# JWT
JWT_SECRET_KEY=your-super-secret-key-for-jwt
JWT_ALGORITHM=HS256

# API URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# OpenAI (for chat AI)
OPENAI_API_KEY=your-openai-api-key

# MCP Server
MCP_HOST=localhost
MCP_PORT=8001
MCP_DEBUG=true
```

### 3. Database Initialization

```bash
# Create database (if using local PostgreSQL)
createdb todo_db

# Run migrations (if using Alembic)
alembic upgrade head

# Or manually create tables
psql todo_db < scripts/init.sql
```

### 4. Start Backend Server

```bash
# Terminal 1: FastAPI server (includes MCP endpoint)
python -m uvicorn src.main:app --reload --port 8000

# Backend should log:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# MCP server available at ws://localhost:8001/mcp
```

---

## Part 2: Frontend Setup (Next.js)

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Configuration

Create `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3. Start Frontend Dev Server

```bash
# Terminal 2: Next.js development server
npm run dev

# Frontend should log:
# ▲ Next.js 16.0.0
# - Local: http://localhost:3000
```

---

## Part 3: Testing MCP Server

### Option A: Using Python MCP Client

```python
# test_mcp_client.py
import asyncio
from mcp import ClientSession
from mcp.client import StdioClientSession

async def test_mcp():
    async with ClientSession() as session:
        # Connect to MCP server
        await session.connect("ws://localhost:8001/mcp")
        
        # Discover tools
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Call add_task tool
        result = await session.call_tool("add_task", {
            "title": "Buy milk",
            "priority": "high"
        })
        print(f"Result: {result}")

asyncio.run(test_mcp())
```

### Option B: Using curl (HTTP)

```bash
# Call MCP tool via HTTP (if HTTP fallback implemented)
curl -X POST http://localhost:8000/mcp/tools/add_task \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy milk",
    "priority": "high"
  }'
```

### Option C: Browser DevTools

```javascript
// In browser console while logged in
const token = localStorage.getItem('auth_token')

// Test REST API first (simpler than MCP)
fetch('http://localhost:8000/api/tasks', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json()).then(console.log)
```

---

## Part 4: Testing Chat Widget

### 1. Login to Dashboard

- Open http://localhost:3000
- Sign up or sign in with test account
- Navigate to /dashboard

### 2. Open Chat Widget

- Click the floating purple button (💬) in bottom-right
- Chat panel slides open

### 3. Test Chat Commands

Try these in chat:

```
# Create a task
"Add a task to buy groceries by Friday with high priority"
→ Assistant creates task and confirms

# List tasks
"Show all my tasks"
→ Assistant lists all tasks

# Mark complete
"Complete the buy groceries task"
→ Assistant marks task as complete

# Delete task
"Delete the buy groceries task"
→ Assistant confirms before deletion

# Update task
"Change buy groceries to low priority"
→ Assistant updates priority
```

---

## Part 5: Verify Bi-Directional Consistency

### Test REST → MCP Consistency

```bash
# Terminal 3: Create task via REST API
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "priority": "high"}'

# Verify via MCP client or chat
# - Task should appear in list_tasks() immediately
# - No delay or caching
```

### Test MCP → REST Consistency

```bash
# Call MCP tool (add_task)
# → Task inserted into database

# Check via REST API
curl http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $JWT_TOKEN"

# Task should appear immediately in results
```

### Test Chat → Dashboard Consistency

```
1. In chat: "Create a task to test consistency"
2. Check dashboard task list
3. New task should appear (triggered auto-refresh)
4. All three interfaces show same task
```

---

## Debugging

### Backend Logs

```bash
# Tail backend logs
tail -f logs/app.log

# Grep for MCP logs
grep "MCP" logs/app.log

# Check error logs
grep "ERROR" logs/app.log
```

### Database Queries

```bash
# Connect to database
psql todo_db

# Check tasks
SELECT id, user_id, title, status FROM task;

# Check conversations
SELECT id, user_id, created_at FROM conversation;

# Check messages
SELECT id, conversation_id, role, created_at FROM message;
```

### MCP Server Status

```bash
# Check if MCP server is running
curl http://localhost:8000/health

# List MCP tools
curl http://localhost:8000/mcp/tools/list \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `DATABASE_URL` not found | Create `.env` with DATABASE_URL in backend directory |
| `JWT_SECRET_KEY` missing | Generate with `openssl rand -hex 32` and add to `.env` |
| Port 8000 already in use | Change port: `--port 9000` or kill process using port |
| CORS errors | Check FRONTEND_URL in `.env`; should match http://localhost:3000 |
| MCP WebSocket connection fails | Ensure MCP_PORT=8001 and endpoint is `/mcp` |
| Chat not showing responses | Check OpenAI API key in `.env`; verify OpenAI Agents SDK installed |
| Task not appearing in dashboard | Check user_id scoping; verify JWT token is valid |

---

## Development Workflow

### Making Changes

```bash
# Backend changes
1. Edit src/services/mcp_service.py
2. Server auto-reloads (uvicorn --reload)
3. Changes take effect immediately

# Frontend changes
1. Edit src/components/chat/ChatWidget.tsx
2. Next.js hot-reloads
3. Changes visible in browser immediately

# Database changes
1. Modify data models in src/models/
2. Create migration with alembic
3. Run migration: alembic upgrade head
4. Restart backend server
```

### Running Tests

```bash
# Backend unit tests
pytest backend/tests/unit

# Backend integration tests
pytest backend/tests/integration

# Frontend tests
npm run test

# Contract tests (MCP tools)
pytest backend/tests/contract/test_mcp_contracts.py
```

---

## Production Deployment Preview

This section is planned for later phases. For MVP:
- Deploy backend to Heroku or DigitalOcean
- Deploy frontend to Vercel
- Use managed PostgreSQL (Neon)
- Enable HTTPS and proper CORS

---

**Status**: ✅ PLANNED

Quickstart template ready for implementation phase. Once code is written, update with actual command examples and screenshot references.
