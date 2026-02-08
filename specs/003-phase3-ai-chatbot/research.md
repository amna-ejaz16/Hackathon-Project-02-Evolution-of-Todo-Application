# Research: Phase 3 AI Chatbot

**Feature**: `003-phase3-ai-chatbot`
**Date**: 2026-02-08

## 1. OpenAI Agents SDK

**Decision**: Use `openai-agents` Python SDK for AI agent orchestration.

**Rationale**: Production-ready framework (v0.8.0+) that handles the tool-calling loop automatically. Provides `@function_tool` decorator for defining tools, `Runner.run()` for executing agent with message, and built-in session/conversation management. Eliminates the need to manually manage the function-calling loop with the raw OpenAI API.

**Alternatives considered**:
- **Raw OpenAI Chat Completions API with function calling**: Lower-level, requires manual tool loop management, no built-in session handling. Rejected for unnecessary complexity.
- **LangChain**: Heavier dependency, more abstraction than needed for a bounded tool-calling agent. Rejected per YAGNI principle.

**Key patterns**:
```python
from agents import Agent, function_tool, Runner

@function_tool
def add_task(title: str, priority: str = "medium") -> str:
    """Add a new task."""
    # calls existing task CRUD
    return "Task created: ..."

agent = Agent(
    name="TaskManager",
    instructions="You help users manage tasks...",
    tools=[add_task, list_tasks, ...]
)

result = await Runner.run(agent, user_message)
# result.final_output contains the AI response
```

**Package**: `openai-agents>=0.8.0`

## 2. MCP (Model Context Protocol) Integration

**Decision**: Use OpenAI Agents SDK's native `@function_tool` directly instead of a separate MCP server.

**Rationale**: The OpenAI Agents SDK already provides a tool-calling mechanism (`@function_tool`) that is simpler and sufficient for our use case. MCP adds value when tools need to be shared across multiple AI clients (Claude Desktop, VS Code, etc.), but our tools are only consumed by a single FastAPI-hosted agent. Adding a separate MCP server would introduce unnecessary process management complexity.

**Alternatives considered**:
- **Separate MCP server with `fastmcp`**: Adds inter-process communication overhead (stdio/SSE transport), requires running a second process alongside FastAPI. Rejected for Phase 3 scope — can be added in Phase 5 if multi-client tool sharing is needed.
- **`fastapi-mcp` to expose FastAPI routes as MCP tools**: Interesting but auto-exposes ALL endpoints as tools, less control over tool definitions and descriptions. Rejected for lack of fine-grained control.

**Future evolution**: If Phase 4/5 requires exposing task tools to external AI clients (Claude Desktop, etc.), the `@function_tool` implementations can be migrated to MCP tools with minimal refactoring since the function signatures and logic remain identical.

## 3. Conversation Persistence

**Decision**: Use SQLModel tables in existing Neon PostgreSQL database for conversation and message storage.

**Rationale**: Reuses existing database infrastructure and ORM. No new database or connection needed. SQLModel models follow the same pattern as the existing `Task` model. Conversations and messages are scoped to `user_id` just like tasks.

**Alternatives considered**:
- **In-memory only (no persistence)**: Simpler but violates FR-020 (conversation history persistence). Rejected.
- **Redis for session/chat storage**: Adds infrastructure dependency. Rejected per YAGNI — PostgreSQL is sufficient for conversation storage at this scale.
- **OpenAI Agents SDK's built-in `SQLiteSession`**: Uses local SQLite which doesn't work for deployed environments (Vercel/HuggingFace). Rejected.

## 4. Frontend Chat UI

**Decision**: Build chat components with React + Framer Motion + Tailwind CSS inside the existing Next.js app. No separate ChatKit library needed.

**Rationale**: The existing dashboard already uses Framer Motion for animations and Tailwind CSS for styling. Building custom chat components ensures full control over cyberpunk theme consistency and avoids adding a heavy UI library dependency.

**Alternatives considered**:
- **Vercel AI SDK `useChat` hook**: Provides streaming chat UI helpers but couples to Vercel's AI SDK patterns and would require adapting the backend to match. Rejected for unnecessary coupling.
- **ChatKit (OpenAI)**: Not a standalone library; "ChatKit" refers to OpenAI's internal playground UI, not an installable package. Not applicable.

**Components to build**:
- `ChatWidget.tsx` — FAB + panel container with open/close state
- `ChatHeader.tsx` — AI avatar, title, close button
- `ChatMessages.tsx` — Scrollable message list with auto-scroll
- `ChatMessage.tsx` — Individual message bubble (user vs assistant styling)
- `ChatInput.tsx` — Text input + send button
- `TypingIndicator.tsx` — Animated dots
- `QuickActionPills.tsx` — Shortcut buttons

## 5. Dashboard-Chat Communication

**Decision**: Use a React callback pattern to trigger dashboard task list refresh after chat operations.

**Rationale**: The `DashboardClient` component already has a `fetchTasks()` function. The `ChatWidget` can accept an `onTaskChange` callback prop that calls `fetchTasks()` after the chat receives a response indicating a task mutation (create/update/delete/complete). No global state management library needed.

**Alternatives considered**:
- **Global state (Zustand/Redux)**: Over-engineering for a single callback. Rejected per YAGNI.
- **Server-Sent Events for real-time sync**: Adds backend complexity. Rejected — callback is sufficient.
- **React Context**: Possible but a simple prop callback is lighter. Rejected for unnecessary abstraction.

## 6. Chat API Endpoint Design

**Decision**: Single `POST /api/chat` endpoint on the FastAPI backend that accepts a message + conversation_id and returns the AI response.

**Rationale**: Keeps the API surface minimal. The endpoint handles: fetching conversation history, running the agent, storing messages, and returning the response. User identification comes from the existing JWT token (same as task endpoints).

**Alternatives considered**:
- **`POST /api/{user_id}/chat`**: user_id in URL path leaks user information and is redundant since JWT already contains user_id. Rejected for security.
- **Separate endpoints for conversation CRUD + message send**: Over-complicates the API for a chat feature. Rejected per simplicity principle.
- **WebSocket for bidirectional streaming**: Adds complexity. Rejected — HTTP POST with single response is sufficient for Phase 3. Streaming can be added later if needed.
