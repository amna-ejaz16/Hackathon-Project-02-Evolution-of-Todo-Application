# Quickstart Guide: Authentication & API Security

**Feature**: 002-phase2-fullstack | **Date**: 2026-01-25

## Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm (or npm/yarn)
- PostgreSQL access (Neon account recommended)

## Environment Setup

### 1. Generate Shared Secret

The `BETTER_AUTH_SECRET` must be identical for both frontend and backend:

```bash
# Generate a secure 32-byte random string
openssl rand -base64 32
# Example output: K7mP9xQzR3nV8yW1hT6gJ4dL2sA5fB0cE8iU7oY3kX4=
```

### 2. Backend Environment (.env)

Create `backend/.env`:

```env
# Authentication
BETTER_AUTH_SECRET=your-generated-secret-here

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 3. Frontend Environment (.env.local)

Create `frontend/.env.local`:

```env
# Authentication (must match backend!)
BETTER_AUTH_SECRET=your-generated-secret-here
BETTER_AUTH_URL=http://localhost:3000

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn sqlmodel pyjwt python-dotenv psycopg2-binary
```

Or create `requirements.txt`:

```text
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlmodel>=0.0.14
pyjwt>=2.8.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.9
```

### 3. Run Backend

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
pnpm install
# Or: npm install
```

Required packages:

```bash
pnpm add better-auth @better-auth/react
```

### 2. Run Frontend

```bash
pnpm dev
# Or: npm run dev
```

Frontend will be available at: http://localhost:3000

## Database Setup

### 1. Connect to Neon

1. Create a Neon project at https://neon.tech
2. Copy the connection string
3. Add to `DATABASE_URL` in backend `.env`

### 2. Create Tables

Run migrations or execute directly:

```sql
-- Users table (managed by Better Auth, but for reference)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Sessions table (managed by Better Auth)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    priority VARCHAR(10) NOT NULL DEFAULT 'medium',
    category VARCHAR(50),
    due_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_completed ON tasks(user_id, completed);
CREATE INDEX IF NOT EXISTS idx_tasks_user_due_date ON tasks(user_id, due_date);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
```

## Verification Steps

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}
```

### 2. Test Auth Flow

1. Open http://localhost:3000/signup
2. Create an account with email and password
3. You should be redirected to dashboard
4. Check browser DevTools > Application > Cookies for auth session

### 3. Test Protected API

```bash
# Without token (should fail)
curl http://localhost:8000/tasks
# Expected: 401 Unauthorized

# With valid token
curl -H "Authorization: Bearer <your-jwt-token>" http://localhost:8000/tasks
# Expected: {"tasks":[],"total":0}
```

## Project Structure After Setup

```
The-Evolution-of-Todo-Application/
├── backend/
│   ├── .env                    # Backend environment
│   ├── requirements.txt        # Python dependencies
│   ├── src/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── core/
│   │   │   ├── config.py      # Environment config
│   │   │   └── security.py    # JWT verification
│   │   ├── models/
│   │   │   ├── user.py        # User model
│   │   │   └── task.py        # Task model
│   │   ├── api/
│   │   │   ├── deps.py        # Auth dependency
│   │   │   ├── tasks.py       # Task endpoints
│   │   │   └── health.py      # Health endpoint
│   │   └── services/
│   │       └── auth.py        # Auth service
│   └── tests/
│       └── ...
├── frontend/
│   ├── .env.local             # Frontend environment
│   ├── package.json           # Node dependencies
│   ├── src/
│   │   ├── lib/
│   │   │   └── auth.ts        # Better Auth config
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── signin/
│   │   │   │   └── signup/
│   │   │   ├── api/auth/
│   │   │   └── dashboard/
│   │   └── middleware.ts      # Route protection
│   └── tests/
│       └── ...
└── specs/
    └── 002-phase2-fullstack/
        ├── spec.md
        ├── plan.md
        ├── research.md
        ├── data-model.md
        ├── quickstart.md       # This file
        └── contracts/
            └── auth-api.yaml
```

## Troubleshooting

### "Could not validate credentials" on all requests

1. Verify `BETTER_AUTH_SECRET` is identical in both `.env` files
2. Check token hasn't expired (default 24h)
3. Ensure Authorization header format: `Bearer <token>` (note the space)

### Database connection errors

1. Check `DATABASE_URL` format includes `?sslmode=require` for Neon
2. Verify Neon project is active (not paused)
3. Check IP allowlist if using Neon's security features

### CORS errors in browser

Add CORS middleware to FastAPI:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks
2. Follow TDD: Write failing tests first
3. Implement backend auth middleware
4. Implement frontend auth pages
5. Connect and test end-to-end
