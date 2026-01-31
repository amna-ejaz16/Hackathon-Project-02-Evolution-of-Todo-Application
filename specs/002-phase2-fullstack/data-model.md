# Data Model: Authentication & API Security

**Feature**: 002-phase2-fullstack | **Date**: 2026-01-25

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA MODEL                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────┐         ┌───────────────────┐            │
│  │       User        │         │      Session      │            │
│  ├───────────────────┤         ├───────────────────┤            │
│  │ id (PK, UUID)     │◀────────│ user_id (FK)      │            │
│  │ email (UNIQUE)    │    1:N  │ id (PK, UUID)     │            │
│  │ password_hash     │         │ token             │            │
│  │ name              │         │ expires_at        │            │
│  │ created_at        │         │ ip_address        │            │
│  │ updated_at        │         │ user_agent        │            │
│  └───────────────────┘         │ created_at        │            │
│           │                    └───────────────────┘            │
│           │ 1:N                                                  │
│           ▼                                                      │
│  ┌───────────────────┐                                          │
│  │       Task        │                                          │
│  ├───────────────────┤                                          │
│  │ id (PK, INT)      │                                          │
│  │ user_id (FK)      │◀── Every task belongs to one user        │
│  │ title             │                                          │
│  │ description       │                                          │
│  │ completed         │                                          │
│  │ priority          │                                          │
│  │ category          │                                          │
│  │ due_date          │                                          │
│  │ created_at        │                                          │
│  │ updated_at        │                                          │
│  └───────────────────┘                                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Entities

### User

Represents a registered user account.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address (login identifier) |
| password_hash | VARCHAR(255) | NOT NULL | Scrypt-hashed password (never plaintext) |
| name | VARCHAR(100) | NULL | Optional display name |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Account creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Last modification time |

**Validation Rules**:
- email: Valid RFC 5322 format, case-insensitive (stored lowercase)
- password: Minimum 8 characters (validated before hashing)
- name: Maximum 100 characters

**Indexes**:
- PRIMARY KEY (id)
- UNIQUE INDEX (email)

---

### Session (Managed by Better Auth)

Represents an active authentication session.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Session identifier |
| user_id | UUID | FOREIGN KEY → User(id) | Owning user |
| token | VARCHAR(500) | NOT NULL | Encrypted session token |
| expires_at | TIMESTAMP | NOT NULL | Session expiration time |
| ip_address | VARCHAR(45) | NULL | Client IP (IPv4/IPv6) |
| user_agent | VARCHAR(255) | NULL | Client user agent |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Session creation time |

**Note**: This table is managed by Better Auth. Schema may vary based on Better Auth version.

**Indexes**:
- PRIMARY KEY (id)
- INDEX (user_id)
- INDEX (expires_at) - for cleanup jobs

---

### Task

Represents a todo item owned by a user.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-incrementing task ID |
| user_id | UUID | FOREIGN KEY → User(id), NOT NULL | Owning user (for data isolation) |
| title | VARCHAR(200) | NOT NULL | Task title |
| description | TEXT | NULL | Optional detailed description |
| completed | BOOLEAN | NOT NULL, DEFAULT FALSE | Completion status |
| priority | VARCHAR(10) | NOT NULL, DEFAULT 'medium' | Priority: low, medium, high |
| category | VARCHAR(50) | NULL | Optional category/tag |
| due_date | DATE | NULL | Optional due date |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Task creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Last modification time |

**Validation Rules**:
- title: 1-200 characters, required
- priority: Enum ['low', 'medium', 'high']
- category: Maximum 50 characters
- user_id: Must reference existing user

**Indexes**:
- PRIMARY KEY (id)
- INDEX (user_id) - for user-scoped queries
- INDEX (user_id, completed) - for filtered lists
- INDEX (user_id, due_date) - for sorted lists

---

## JWT Token Structure

The JWT token payload (not stored in database, derived from User):

```json
{
  "id": "user-uuid-string",
  "email": "user@example.com",
  "iat": 1706187600,
  "exp": 1706274000
}
```

| Claim | Type | Description |
|-------|------|-------------|
| id | string (UUID) | User identifier for API authorization |
| email | string | User email for logging/display |
| iat | number | Issued-at timestamp (Unix epoch) |
| exp | number | Expiration timestamp (Unix epoch, default +24h) |

---

## State Transitions

### User Account States

```
┌─────────────┐
│   Created   │ ← signUp.email() success
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Active    │ ← Can sign in, create tasks
└──────┬──────┘
       │ (account deletion - out of scope)
       ▼
┌─────────────┐
│   Deleted   │ ← Sessions invalidated, tasks orphaned
└─────────────┘
```

### Task States

```
┌─────────────┐
│   Created   │ ← POST /tasks (completed=false)
└──────┬──────┘
       │
       ▼
┌─────────────┐      PATCH /tasks/{id}
│   Pending   │◀────────────────────────┐
│ (completed  │                         │
│   =false)   │                         │
└──────┬──────┘                         │
       │ PATCH /tasks/{id}              │
       │ completed=true                 │
       ▼                                │
┌─────────────┐                         │
│  Completed  │─────────────────────────┘
│ (completed  │      completed=false
│   =true)    │
└──────┬──────┘
       │ DELETE /tasks/{id}
       ▼
┌─────────────┐
│   Deleted   │
└─────────────┘
```

---

## Data Isolation Rules

1. **Query Filtering**: All task queries MUST include `WHERE user_id = :authenticated_user_id`

2. **Creation**: New tasks MUST have `user_id` set to the authenticated user's ID

3. **Updates**: Update operations MUST verify `user_id` matches authenticated user before modifying

4. **Deletes**: Delete operations MUST verify `user_id` matches authenticated user before removing

5. **Not Found Response**: If task exists but belongs to different user, return 404 (not 403) to prevent information disclosure
