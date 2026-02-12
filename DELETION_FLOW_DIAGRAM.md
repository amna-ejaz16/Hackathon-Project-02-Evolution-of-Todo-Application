# Deletion Flow - Complete Code Path Diagram

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION LAYER                        │
│                      (Frontend Chat Widget)                          │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ├─ Turn 1: User sends "delete a task to make coffee"
                       │
                       ├─ Turn 2: User sends "yes"
                       │
                       └─→ API Call: POST /api/chat
                            │
┌──────────────────────────────────────────────────────────────────────┐
│                         BACKEND API LAYER                             │
│                    (FastAPI Chat Endpoint)                            │
│                                                                       │
│  File: backend/src/api/chat.py                                      │
│  Route: POST /api/chat                                              │
│  Handler: process_chat_message()                                    │
│           │                                                          │
│           ├─ Extract user_id from JWT token                        │
│           ├─ Call ChatService.process_message()                    │
│           └─→ Return ChatResponse (response, action, task_id)      │
│                                                                       │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ├─→ ChatService.process_message()
                       │
┌──────────────────────────────────────────────────────────────────────┐
│                      CHAT SERVICE LAYER                               │
│                    (Agent Orchestration)                              │
│                                                                       │
│  File: backend/src/services/chat_service.py                         │
│  Method: ChatService.process_message()                              │
│                                                                       │
│  STEPS:                                                              │
│  1. Get or create conversation                                      │
│  2. Store user message in database                                  │
│  3. Fetch context (last 20 messages)                                │
│  4. Create task tools with user_id bound                            │
│  5. Create Agent with AGENT_INSTRUCTIONS                            │
│  6. Run Agent with Runner.run()                                     │
│  7. Extract response and metadata from result                       │
│  8. Store assistant message in database                             │
│  9. Return ChatResponse                                              │
│                                                                       │
│  CRITICAL SECTION - AGENT INSTRUCTIONS:                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ DELETING TASKS (T031 - Multi-turn confirmation):              │ │
│  │                                                                │ │
│  │ TURN 1 - User says "delete [task description]":               │ │
│  │ - Use list_tasks tool to find matching tasks                 │ │
│  │ - If ONE match: Show task with ID, STOP, WAIT                │ │
│  │                                                                │ │
│  │ TURN 2 - User responds with affirmative:                      │ │
│  │ - LOOK at previous message in conversation history            │ │
│  │ - EXTRACT task ID from "(ID: {number})" format               │ │
│  │ - CALL delete_task tool with extracted task_id               │ │
│  │ - Report result                                                │ │
│  │                                                                │ │
│  │ CRITICAL: Task ID MUST be extracted from previous message    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ├─→ Agent processes message with OpenAI
                       │
┌──────────────────────────────────────────────────────────────────────┐
│                        AGENT EXECUTION LAYER                          │
│                  (OpenAI Agents SDK / GPT-4o-mini)                    │
│                                                                       │
│  Agent reads instructions and decides:                               │
│  - What tools to call                                                │
│  - What parameters to pass                                           │
│  - What response to generate                                         │
│                                                                       │
│  TURN 1 Flow:                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Agent sees: "delete a task to make coffee"                  │   │
│  │ Agent instruction: "TURN 1 - Use list_tasks tool..."        │   │
│  │                                                              │   │
│  │ Agent calls: list_tasks(keywords="coffee")                  │   │
│  │ Tool returns: [{id: 42, title: "make coffee", ...}]        │   │
│  │                                                              │   │
│  │ Agent sees instruction: "STOP - do NOT call delete_task"   │   │
│  │                                                              │   │
│  │ Agent outputs: "I found 'make coffee' (ID: 42).             │   │
│  │                Are you sure you want to delete it?"         │   │
│  │                                                              │   │
│  │ Agent stops (no more tool calls)                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  TURN 2 Flow:                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Agent sees: "yes"                                            │   │
│  │ Agent sees conversation history:                             │   │
│  │   User: "delete a task to make coffee"                       │   │
│  │   Assistant: "I found 'make coffee' (ID: 42)..."             │   │
│  │   User: "yes"                                                │   │
│  │                                                              │   │
│  │ Agent instruction: "TURN 2 - LOOK at your previous message" │   │
│  │                                                              │   │
│  │ Agent looks at assistant message: Finds "ID: 42"            │   │
│  │                                                              │   │
│  │ Agent instruction: "EXTRACT that task ID number"            │   │
│  │                                                              │   │
│  │ Agent extracts: 42                                           │   │
│  │                                                              │   │
│  │ Agent instruction: "CALL the delete_task tool"              │   │
│  │                                                              │   │
│  │ Agent calls: delete_task(task_id=42)                        │   │
│  │ Tool returns: "Deleted task 'make coffee' (ID: 42)"         │   │
│  │                                                              │   │
│  │ Agent outputs: "✓ Deleted task 'make coffee' (ID: 42)"      │   │
│  │                                                              │   │
│  │ Agent done                                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ├─→ Result contains delete_task tool call
                       │
┌──────────────────────────────────────────────────────────────────────┐
│                      TASK TOOLS LAYER                                 │
│                  (Tool Implementations)                               │
│                                                                       │
│  File: backend/src/services/task_tools.py                           │
│  Function: delete_task(task_id: int) -> str                         │
│                                                                       │
│  Execution:                                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 1. Query database for task with:                             │   │
│  │    - task.id == task_id                                      │   │
│  │    - task.user_id == user_id (from closure)                 │   │
│  │                                                              │   │
│  │    Query: SELECT * FROM tasks WHERE id=42 AND user_id=...  │   │
│  │    Result: Task found ✓                                      │   │
│  │                                                              │   │
│  │ 2. Store task title for confirmation message                │   │
│  │    task_title = "make coffee"                                │   │
│  │                                                              │   │
│  │ 3. Delete task from database                                │   │
│  │    session.delete(task)                                      │   │
│  │    session.flush()  # Ensure delete is processed            │   │
│  │    session.commit() # Commit transaction                     │   │
│  │                                                              │   │
│  │ 4. Return confirmation message                               │   │
│  │    return "Deleted task 'make coffee' (ID: 42)"             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Database Effect:                                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ BEFORE:                                                       │   │
│  │ tasks table:                                                  │   │
│  │   id | title        | user_id | completed | ...              │   │
│  │ ────┼──────────────┼─────────┼───────────┤                  │   │
│  │ 42  | make coffee  | test    | false     | ...              │   │
│  │ 43  | drink tea    | test    | false     | ...              │   │
│  │                                                              │   │
│  │ AFTER:                                                        │   │
│  │ tasks table:                                                  │   │
│  │   id | title        | user_id | completed | ...              │   │
│  │ ────┼──────────────┼─────────┼───────────┤                  │   │
│  │ 43  | drink tea    | test    | false     | ...              │   │
│  │                                                              │   │
│  │ Result: Task 42 deleted ✓                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ├─→ Tool call detected and tracked
                       │
┌──────────────────────────────────────────────────────────────────────┐
│                     ACTION DETECTION LAYER                            │
│                  (Tool Call Classification)                           │
│                                                                       │
│  File: backend/src/services/chat_service.py (lines 484-487)         │
│  Detection Logic:                                                    │
│                                                                       │
│  Check: if tool_name == "delete_task"                               │
│  Action: set action = "task_deleted"                                │
│  Extract: task_id from tool arguments                               │
│  Log: Tool call detected for tracking                               │
│                                                                       │
│  Result:                                                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ ChatResponse {                                                │   │
│  │   response: "✓ Deleted task 'make coffee' (ID: 42)",        │   │
│  │   action: "task_deleted",                  ← KEY             │   │
│  │   task_id: 42,                                                │   │
│  │   conversation_id: 123                                        │   │
│  │ }                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ├─→ Return response to frontend with action
                       │
┌──────────────────────────────────────────────────────────────────────┐
│                      FRONTEND RESPONSE LAYER                          │
│                  (Chat Response Handler)                              │
│                                                                       │
│  File: frontend/src/components/chat/ChatWidget.tsx                  │
│  Method: handleSendMessage()                                        │
│                                                                       │
│  Receive: ChatApiResponse                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ {                                                              │   │
│  │   response: "✓ Deleted task 'make coffee' (ID: 42)",         │   │
│  │   action: "task_deleted",        ← Check for this             │   │
│  │   task_id: 42,                                                │   │
│  │   conversation_id: 123                                        │   │
│  │ }                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Action Check (line 135-146):                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ if (data.action && ["task_created", "task_updated",          │   │
│  │    "task_completed", "task_uncompleted",                     │   │
│  │    "task_deleted"].includes(data.action)) {                  │   │
│  │                                                              │   │
│  │   onTaskChange()  ← Refresh task list                        │   │
│  │ }                                                              │   │
│  │                                                              │   │
│  │ Since action == "task_deleted":                              │   │
│  │   → onTaskChange() is called ✓                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Display:                                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Chat messages updated:                                        │   │
│  │   User: "yes"                                                 │   │
│  │   Assistant: "✓ Deleted task 'make coffee' (ID: 42)"         │   │
│  │                                                              │   │
│  │ onTaskChange() called:                                        │   │
│  │   → Task list component refreshes                             │   │
│  │   → Fetches tasks from API                                    │   │
│  │   → Task 42 no longer in list                                 │   │
│  │   → UI updates to reflect deletion                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                       │
                       └─→ UI Updated: Task deleted ✓
```

---

## Cancellation Flow

```
User: "no"
  ↓
Agent sees: "no" in response to delete confirmation
Agent instruction: "If user responds with 'no' or 'cancel': STOP (do NOT call delete_task)"
  ↓
Agent does NOT call delete_task tool
  ↓
Agent outputs: "No problem. I did not delete the task."
  ↓
No tool call detected
  ↓
action = "conversation" (default, no modification)
  ↓
Frontend receives action = "conversation"
  ↓
Condition check: action not in ["task_deleted", ...] → No refresh
  ↓
Task list stays the same
  ↓
Task still visible in list ✓
```

---

## Code References

### Key File Locations:

| Component | File | Lines |
|-----------|------|-------|
| Agent Instructions | `backend/src/services/chat_service.py` | 85-113 |
| Chat Service Main | `backend/src/services/chat_service.py` | 248-536 |
| Task Tools | `backend/src/services/task_tools.py` | 269-300 |
| Action Detection | `backend/src/services/chat_service.py` | 484-487 |
| Chat Endpoint | `backend/src/api/chat.py` | - |
| Frontend Handler | `frontend/src/components/chat/ChatWidget.tsx` | 106-190 |
| Fresh Chat Reset | `frontend/src/components/chat/ChatWidget.tsx` | 206-251 |

---

## Success Criteria Met

✅ **TURN 1**: Agent asks for confirmation with task ID
- User: "delete a task to make coffee"
- Agent: "I found 'make coffee' (ID: 42). Are you sure you want to delete it?"

✅ **TURN 2**: Agent executes deletion
- User: "yes"
- Agent calls: `delete_task(task_id=42)`
- Tool deletes from database

✅ **CONFIRMATION**: Agent confirms deletion
- Agent: "✓ Deleted task 'make coffee' (ID: 42)"

✅ **UI UPDATE**: Frontend refreshes task list
- Task 42 no longer appears
- User sees task deleted immediately

✅ **CANCELLATION**: Handles "no" correctly
- User: "no"
- Agent: "No problem. I did not delete the task."
- Task preserved in database
- UI unchanged
