# Quickstart: Phase 3 AI Chatbot

**Feature**: `003-phase3-ai-chatbot`
**Date**: 2026-02-08

## Prerequisites

- Phase 2 fullstack app running (frontend + backend + Neon PostgreSQL)
- OpenAI API key (for GPT model access)
- Python 3.11+ with existing backend virtual environment
- Node.js 20+ with existing frontend dependencies

## 1. Backend Setup

### Install New Dependencies

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install openai-agents>=0.8.0
pip install openai>=1.0.0
```

### Add Environment Variable

Add to `backend/.env`:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Database Tables

New tables (`conversation`, `message`) are auto-created by SQLModel on startup via `create_db_and_tables()`. No manual migration needed.

### New Backend Files

```
backend/src/
├── api/
│   └── chat.py              # POST /api/chat, GET /api/chat/history
├── models/
│   └── chat.py              # Conversation, Message SQLModel models
└── services/
    ├── chat_service.py       # Agent orchestration (OpenAI Agents SDK)
    └── task_tools.py         # @function_tool definitions for task CRUD
```

### Start Backend

```bash
uvicorn src.main:app --reload --port 8000
```

## 2. Frontend Setup

No new npm dependencies needed. Uses existing Framer Motion + Tailwind CSS.

### New Frontend Files

```
frontend/src/
├── components/
│   └── chat/
│       ├── ChatWidget.tsx        # FAB + panel container
│       ├── ChatHeader.tsx        # Header bar
│       ├── ChatMessages.tsx      # Scrollable message list
│       ├── ChatMessage.tsx       # Individual message bubble
│       ├── ChatInput.tsx         # Text input + send button
│       ├── TypingIndicator.tsx   # Animated dots
│       └── QuickActionPills.tsx  # Shortcut buttons
└── app/
    └── dashboard/
        └── DashboardClient.tsx   # Modified: embed ChatWidget, add onTaskChange callback
```

### Start Frontend

```bash
cd frontend
npm run dev
```

## 3. Verify Integration

1. Open http://localhost:3000/dashboard
2. Click the FAB (bottom-right, neon gradient button)
3. Type "Show all my tasks" and press Enter
4. Verify AI responds with your task list
5. Type "Add a task to test the chatbot with high priority"
6. Verify the task appears in the dashboard list (auto-refresh)

## API Endpoints (New)

| Method | Endpoint            | Description                          | Auth     |
|--------|---------------------|--------------------------------------|----------|
| POST   | `/api/chat`         | Send message, receive AI response    | JWT      |
| GET    | `/api/chat/history` | Load conversation history            | JWT      |

All existing endpoints remain unchanged.
