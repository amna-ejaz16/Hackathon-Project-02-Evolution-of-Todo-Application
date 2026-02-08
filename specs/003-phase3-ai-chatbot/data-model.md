# Data Model: Phase 3 AI Chatbot

**Feature**: `003-phase3-ai-chatbot`
**Date**: 2026-02-08

## Entities

### Conversation (NEW)

Represents a single chat thread between a user and the AI assistant.

| Field        | Type         | Constraints                        | Description                        |
|--------------|--------------|------------------------------------|------------------------------------|
| id           | Integer (PK) | Auto-increment                     | Unique conversation identifier     |
| user_id      | Text (FK)    | NOT NULL, INDEX, references user.id| Owner of the conversation          |
| title        | Text         | Default: "Task Assistant"          | Display title for the conversation |
| created_at   | Timestamp    | Default: now()                     | When conversation was started      |
| updated_at   | Timestamp    | Default: now(), on update: now()   | Last activity timestamp            |

**Constraints**:
- One active conversation per user (enforced at application level; query for existing before creating new)
- user_id matches Better Auth user.id format (text, not integer)

**Relationships**:
- Conversation → User: Many-to-one (one user has one active conversation)
- Conversation → Message: One-to-many (one conversation has many messages)

---

### Message (NEW)

A single chat message within a conversation.

| Field           | Type         | Constraints                                | Description                                |
|-----------------|--------------|--------------------------------------------|--------------------------------------------|
| id              | Integer (PK) | Auto-increment                             | Unique message identifier                  |
| conversation_id | Integer (FK) | NOT NULL, INDEX, references conversation.id| Parent conversation                        |
| role            | Text         | NOT NULL, CHECK IN ('user', 'assistant')   | Message sender role                        |
| content         | Text         | NOT NULL                                   | Message text content                       |
| metadata        | JSON/Text    | NULLABLE                                   | Tool calls, reasoning traces, action type  |
| created_at      | Timestamp    | Default: now()                             | When message was created                   |

**Constraints**:
- Maximum 200 messages per conversation (FR-027); oldest pruned when cap reached
- AI context window uses last 20 messages (FR-026); applied at query time, not stored
- `metadata` stores structured data: `{"tool_calls": [...], "action": "create_task", "task_id": 5}`

**Relationships**:
- Message → Conversation: Many-to-one

---

### Task (EXISTING — No Changes)

The existing task entity. Referenced by AI tool functions but NOT modified.

| Field       | Type         | Constraints                    |
|-------------|--------------|--------------------------------|
| id          | Integer (PK) | Auto-increment                 |
| user_id     | Text (FK)    | NOT NULL, INDEX                |
| title       | Text         | NOT NULL, 1-200 chars          |
| description | Text         | NULLABLE                       |
| completed   | Boolean      | Default: false                 |
| priority    | Text         | Default: "medium" (low/medium/high) |
| category    | Text         | NULLABLE, max 50 chars         |
| due_date    | Date         | NULLABLE                       |
| created_at  | Timestamp    | Default: now()                 |
| updated_at  | Timestamp    | Default: now()                 |

---

## Entity Relationship Diagram

```
┌──────────┐       ┌──────────────┐       ┌──────────┐
│   User   │ 1───1 │ Conversation │ 1───* │ Message  │
│ (Better  │       │              │       │          │
│  Auth)   │       │ id           │       │ id       │
│          │       │ user_id (FK) │       │ conv_id  │
│ id (PK)  │       │ title        │       │ role     │
│ email    │       │ created_at   │       │ content  │
│ name     │       │ updated_at   │       │ metadata │
└──────┬───┘       └──────────────┘       │ created  │
       │                                   └──────────┘
       │ 1───*
       │
┌──────┴───┐
│   Task   │
│ (EXISTS) │
│          │
│ id (PK)  │
│ user_id  │
│ title    │
│ ...      │
└──────────┘
```

## State Transitions

### Conversation Lifecycle
```
[New User Opens Chat] → CREATE conversation (if none exists for user)
[User Sends Message] → ADD message (role: user), RUN agent, ADD message (role: assistant)
[Message Cap Reached] → PRUNE oldest messages (keep newest 200)
[User Closes Chat] → No state change (conversation persists)
[User Reopens Chat] → LOAD existing conversation + last N messages
```

### Message Processing Flow
```
[User Message Received]
    → Store as Message (role: user)
    → Fetch last 20 messages for context
    → Run OpenAI Agent with context + tools
    → Agent may call 0+ tools (task CRUD operations)
    → Store AI response as Message (role: assistant, metadata: tool_calls)
    → Return response to frontend
```

## Migration Notes

- New tables `conversation` and `message` are created alongside existing `tasks` table
- No modifications to existing `tasks`, `user`, `session`, `account`, `verification`, or `jwks` tables
- SQLModel `create_all(checkfirst=True)` ensures safe table creation
- Foreign key: `conversation.user_id` → `user.id`, `message.conversation_id` → `conversation.id`
