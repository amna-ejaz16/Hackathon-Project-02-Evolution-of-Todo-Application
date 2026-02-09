# Data Model: MCP Server & Chat System

**Date**: 2026-02-09
**Scope**: Complete data model for Phase 3 (Chat Widget + MCP Server)
**Status**: Complete

---

## Overview

Phase 3 reuses the Task entity from Phase 2 and adds Chat-related entities (Conversation, Message). MCP tools operate on the same Task entity without requiring new database tables.

---

## Entities

### 1. Task (Existing from Phase 2 - REUSED)

**Purpose**: Core domain entity for all Todo operations
**Table**: `task`
**Ownership**: User-scoped (each task belongs to one user)

**Fields**:
```sql
CREATE TABLE task (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id INTEGER NOT NULL REFERENCES user(id),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
  category VARCHAR(100),
  due_date DATE,
  status ENUM('pending', 'completed') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  -- Indexes for common queries
  INDEX idx_user_id (user_id),
  INDEX idx_user_status (user_id, status),
  INDEX idx_due_date (user_id, due_date)
)
```

**Constraints**:
- `title` is required (non-null)
- `user_id` enforces ownership (no cross-user access)
- `priority` must be one of: 'low', 'medium', 'high'
- `status` must be one of: 'pending', 'completed'
- `category` is free-text (no constraints)
- `due_date` is optional ISO 8601 date

**Validation Rules**:
- Title: 1-255 characters, no leading/trailing whitespace
- Priority: Only 'low', 'medium', 'high'
- Due date: Valid ISO 8601 format (YYYY-MM-DD)
- Category: 0-100 characters

**Usage**:
- ✅ REST API: `/api/tasks` endpoints
- ✅ Chat: OpenAI Agents use task_tools.py functions
- ✅ MCP: All 5 MCP tools operate on this table

---

### 2. Conversation (New - Chat System)

**Purpose**: Groups chat messages for a user into logical conversations
**Table**: `conversation`
**Ownership**: One conversation per user (current design)

**Fields**:
```sql
CREATE TABLE conversation (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id INTEGER NOT NULL UNIQUE REFERENCES user(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

**Constraints**:
- `user_id` UNIQUE ensures one active conversation per user
- `user_id` enforces user ownership

**Notes**:
- No soft-delete needed (MVP)
- Timestamps for debugging and audit trails
- No "title" or "topic" field (single active conversation per user)

---

### 3. Message (New - Chat System)

**Purpose**: Individual chat messages (user or assistant) within a conversation
**Table**: `message`
**Ownership**: Scoped to conversation.user_id

**Fields**:
```sql
CREATE TABLE message (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  conversation_id INTEGER NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
  role ENUM('user', 'assistant') NOT NULL,
  content LONGTEXT NOT NULL,
  metadata_json JSON,  -- Stores tool calls, reasoning traces, etc.
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Indexes for efficient queries
  INDEX idx_conversation (conversation_id),
  INDEX idx_conversation_created (conversation_id, created_at)
)
```

**Constraints**:
- `conversation_id` NOT NULL (every message belongs to a conversation)
- `role` must be 'user' or 'assistant'
- `content` NOT NULL (non-empty message)
- `metadata_json` is optional (stores tool_calls, action, etc.)
- Cascade delete when conversation deleted

**Notes**:
- `metadata_json` fixed in Phase 3 (was `@property` conflict issue)
- Supports tool call tracking: `{tool_calls: [], action: "...", reasoning: "..."}`
- Auto-prune oldest messages when > 200 per conversation

**Metadata Schema** (examples):
```json
{
  "tool_calls": [
    {
      "tool_name": "add_task",
      "parameters": { "title": "Buy milk", "priority": "high" },
      "result": { "task_id": 42 }
    }
  ],
  "action": "task_created",
  "reasoning": "User asked to create a task"
}
```

---

### 4. User (Existing from Phase 2 - REUSED)

**Purpose**: User identity and authentication
**Table**: `user`
**Reference**: Owned by Better Auth

**Relevant Fields** (for Phase 3):
```sql
id INTEGER,                    -- PK
email VARCHAR(255) UNIQUE,     -- From Better Auth
name VARCHAR(255),             -- From Better Auth
created_at TIMESTAMP,          -- User creation time
```

**Phase 3 Usage**:
- Conversation scoped to user_id
- Message scoped through conversation.user_id
- Task already scoped to user_id (Phase 2)
- JWT token contains user_id for auth

---

## Relationships

```
User (1) ──┬─── (Many) Task
           └─── (1) Conversation ──┬─── (Many) Message
```

**Scoping Rules**:
- All Task operations: WHERE user_id = {authenticated_user_id}
- All Conversation operations: WHERE user_id = {authenticated_user_id}
- All Message operations: Via conversation.user_id scoping

**No Direct Foreign Key Between Task and Message**:
- Reason: Messages describe task operations but don't directly reference tasks
- Tool call results stored in message.metadata_json
- Design allows flexibility for non-task chat messages

---

## Indexes for Performance

| Table | Index | Reason |
|-------|-------|--------|
| task | (user_id) | Filter by owner |
| task | (user_id, status) | List pending/completed |
| task | (user_id, due_date) | Find overdue tasks |
| conversation | (user_id) | Load user's conversation |
| message | (conversation_id) | Load messages for conversation |
| message | (conversation_id, created_at) | Paginate messages chronologically |

---

## Data Flow for Each MCP Tool

### MCP Tool: `add_task(user_id, title, description, priority, category, due_date)`

**Input Validation**:
- title: required, 1-255 chars
- priority: optional, must be 'low', 'medium', 'high'
- due_date: optional, ISO 8601 format
- user_id: extracted from JWT

**Database Operation**:
```sql
INSERT INTO task (user_id, title, description, priority, category, due_date, status)
VALUES (?, ?, ?, ?, ?, ?, 'pending')
RETURNING *
```

**Response**:
```json
{
  "id": 42,
  "title": "Buy milk",
  "description": null,
  "priority": "medium",
  "category": null,
  "due_date": null,
  "status": "pending",
  "created_at": "2026-02-09T10:30:00Z"
}
```

---

### MCP Tool: `list_tasks(user_id, status, priority, category, page=1, page_size=20)`

**Input Validation**:
- status: optional, must be 'pending' or 'completed'
- priority: optional, must be 'low', 'medium', 'high'
- category: optional, free text
- page, page_size: pagination (defaults: page=1, size=20)
- user_id: extracted from JWT

**Database Operation**:
```sql
SELECT * FROM task
WHERE user_id = ?
  AND (status = ? OR ? IS NULL)
  AND (priority = ? OR ? IS NULL)
  AND (category = ? OR ? IS NULL)
ORDER BY created_at DESC
LIMIT ? OFFSET ?
```

**Response**:
```json
{
  "tasks": [
    { "id": 42, "title": "...", ... },
    { "id": 41, "title": "...", ... }
  ],
  "total": 127,
  "page": 1,
  "page_size": 20,
  "total_pages": 7
}
```

---

### MCP Tool: `complete_task(user_id, task_id)`

**Input Validation**:
- task_id: required, integer
- user_id: extracted from JWT

**Database Operation**:
```sql
UPDATE task
SET status = 'completed', updated_at = CURRENT_TIMESTAMP
WHERE id = ? AND user_id = ?  -- user scoping
RETURNING *
```

**Response**:
```json
{
  "id": 42,
  "title": "Buy milk",
  "status": "completed",
  "updated_at": "2026-02-09T10:31:00Z",
  ...
}
```

---

### MCP Tool: `delete_task(user_id, task_id)`

**Input Validation**:
- task_id: required, integer
- user_id: extracted from JWT

**Database Operation** (soft delete):
```sql
DELETE FROM task
WHERE id = ? AND user_id = ?  -- user scoping
```

**Response**:
```json
{
  "success": true,
  "message": "Task deleted",
  "task_id": 42
}
```

---

### MCP Tool: `update_task(user_id, task_id, title, description, priority, category, due_date, status)`

**Input Validation**:
- task_id: required, integer
- At least one update field must be provided
- priority: if provided, must be 'low', 'medium', 'high'
- status: if provided, must be 'pending' or 'completed'
- user_id: extracted from JWT

**Database Operation**:
```sql
UPDATE task
SET 
  title = COALESCE(?, title),
  description = COALESCE(?, description),
  priority = COALESCE(?, priority),
  category = COALESCE(?, category),
  due_date = COALESCE(?, due_date),
  status = COALESCE(?, status),
  updated_at = CURRENT_TIMESTAMP
WHERE id = ? AND user_id = ?  -- user scoping
RETURNING *
```

**Response**:
```json
{
  "id": 42,
  "title": "Buy milk and bread",
  "priority": "high",
  "updated_at": "2026-02-09T10:32:00Z",
  ...
}
```

---

## Consistency & Data Integrity

### Bi-Directional Consistency (REST ↔ MCP)

**Scenario 1: REST creates task, MCP lists tasks**
```
1. REST POST /api/tasks with {title: "Buy milk"}
2. FastAPI creates task in database
3. MCP client calls list_tasks()
4. SQLModel queries same database
5. Created task appears in list ✅ (same connection pool, immediate)
```

**Scenario 2: MCP creates task, REST lists tasks**
```
1. MCP tool add_task() inserts into database
2. REST GET /api/tasks queries same database
3. Created task appears in response ✅ (same ACID transactions)
```

**Mechanism**: 
- Both use same SQLModel ORM + PostgreSQL
- ACID transactions ensure consistency
- No caching layer (immediate consistency)
- Same connection pool + user scoping

### User Scoping Enforcement

**Principle**: No task visible outside its owner's context

**Implementation**:
- Every query includes: `WHERE user_id = ?`
- user_id extracted from JWT token (same for REST and MCP)
- Database foreign key: `task.user_id REFERENCES user(id)`
- Application-level validation in each tool

**Enforcement Points**:
1. FastAPI middleware: Extracts user_id from JWT
2. Tool layer: All queries add `user_id` filter
3. Database: Foreign key constraints
4. ORM (SQLModel): Automatic filtering via ORM patterns

---

## Message Auto-Pruning

**Rule**: When conversation.messages.count > 200, delete oldest messages

**Implementation**:
```python
# In chat_service.py, after inserting new message:
def prune_old_messages(conversation_id: int, max_messages: int = 200):
    count = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).count()
    
    if count > max_messages:
        excess = count - max_messages
        oldest_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).limit(excess).all()
        
        for msg in oldest_messages:
            db.delete(msg)
```

**Trigger**: After every message insertion
**Scope**: Per conversation (prevents one user blocking others)

---

## SQL Scripts (Creation)

### Create Conversation Table
```sql
CREATE TABLE conversation (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
```

### Create Message Table
```sql
CREATE TABLE message (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  conversation_id INTEGER NOT NULL,
  role ENUM('user', 'assistant') NOT NULL,
  content LONGTEXT NOT NULL,
  metadata_json JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (conversation_id) REFERENCES conversation(id) ON DELETE CASCADE,
  INDEX idx_conversation (conversation_id),
  INDEX idx_conversation_created (conversation_id, created_at)
);
```

---

## Pydantic Models for Validation

### TaskCreate (Input)
```python
class TaskCreate(BaseModel):
    title: str  # Required, 1-255 chars
    description: Optional[str] = None
    priority: Literal["low", "medium", "high"] = "medium"
    category: Optional[str] = None
    due_date: Optional[date] = None
```

### TaskUpdate (Input)
```python
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    category: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[Literal["pending", "completed"]] = None
```

### TaskResponse (Output)
```python
class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    category: Optional[str]
    due_date: Optional[date]
    status: str
    created_at: datetime
    updated_at: datetime
```

---

**Status**: ✅ COMPLETE

Data model reuses Task entity from Phase 2 and adds Chat-specific entities. All MCP tools operate on existing Task table. No new database schema required beyond what already exists.

Ready for contract generation (Phase 1 - Contracts).
