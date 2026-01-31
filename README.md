# Todo Application - Phase II: Full-Stack Web Application

A secure, multi-user todo application with authentication built using Next.js, FastAPI, Better Auth, and Neon PostgreSQL.

## Features

- **User Authentication**: Secure signup/signin with Better Auth and JWT tokens
- **Multi-User Support**: Complete user isolation - each user sees only their own tasks
- **Full CRUD Operations**: Create, read, update, and delete tasks
- **Task Management**: Mark tasks complete/incomplete, add descriptions
- **Responsive UI**: Modern interface built with Next.js and Tailwind CSS
- **Secure API**: JWT-protected endpoints with stateless authentication

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15+ (App Router), React 19, Tailwind CSS |
| Backend | Python FastAPI, SQLModel ORM |
| Database | Neon Serverless PostgreSQL |
| Authentication | Better Auth (frontend) + JWT verification (backend) |
| ORM (Frontend) | Drizzle ORM |

## Prerequisites

- Node.js 20+
- Python 3.11+
- Neon PostgreSQL account (https://neon.tech)

## Project Structure

```
.
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/       # Auth pages (signin, signup)
│   │   │   ├── api/          # API routes (Better Auth)
│   │   │   ├── dashboard/    # Task dashboard
│   │   │   └── layout.tsx
│   │   ├── lib/
│   │   │   ├── auth.ts       # Better Auth server config
│   │   │   ├── auth-client.ts # Better Auth client
│   │   │   ├── api.ts        # Backend API client
│   │   │   └── db/           # Drizzle schema
│   │   └── middleware.ts     # Route protection
│   └── package.json
│
├── backend/                  # FastAPI backend application
│   ├── src/
│   │   ├── api/
│   │   │   ├── deps.py       # JWT auth dependency
│   │   │   ├── tasks.py      # Task CRUD endpoints
│   │   │   └── health.py     # Health check
│   │   ├── core/
│   │   │   ├── config.py     # Environment config
│   │   │   ├── database.py   # Neon DB connection
│   │   │   └── security.py   # JWT verification
│   │   ├── models/
│   │   │   ├── task.py       # Task SQLModel
│   │   │   └── user.py       # User model
│   │   └── main.py           # FastAPI app
│   └── requirements.txt
│
└── specs/                    # Spec-Driven Development artifacts
    └── 002-phase2-fullstack/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Setup Instructions

### 1. Clone and Checkout Phase 2 Branch

```bash
git clone <repository-url>
cd The-Evolution-of-Todo-Application
git checkout 002-phase2-fullstack
```

### 2. Set Up Neon Database

1. Create a Neon account at https://neon.tech
2. Create a new project and database
3. Copy the connection string

### 3. Configure Environment Variables

**Frontend** (`frontend/.env.local`):
```env
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
BETTER_AUTH_SECRET=your-secret-key-min-32-characters
BETTER_AUTH_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Backend** (`backend/.env`):
```env
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
BETTER_AUTH_SECRET=your-secret-key-min-32-characters
CORS_ORIGINS=http://localhost:3000
```

> **Important**: Use the same `BETTER_AUTH_SECRET` in both frontend and backend for JWT verification.

### 4. Install and Run Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn src.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

### 5. Install and Run Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## API Endpoints

### Authentication (Better Auth - Frontend)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/sign-up` | Register new user |
| POST | `/api/auth/sign-in` | Sign in user |
| POST | `/api/auth/sign-out` | Sign out user |
| GET | `/api/auth/session` | Get current session |

### Tasks (FastAPI - Backend)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all tasks (user-scoped) |
| POST | `/api/tasks` | Create new task |
| GET | `/api/tasks/{id}` | Get task by ID |
| PUT | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |
| GET | `/health` | Health check |

All `/api/tasks` endpoints require `Authorization: Bearer <token>` header.

## Authentication Flow

```
1. User signs up/in → Better Auth creates session + issues JWT
2. Frontend stores JWT → Attaches to API requests
3. Backend receives request → Extracts JWT from Authorization header
4. Backend verifies JWT → Uses shared BETTER_AUTH_SECRET
5. Backend identifies user → Filters tasks by user_id from token
6. Response returned → Only user's own data
```

## Usage

1. **Register**: Visit http://localhost:3000/signup
2. **Sign In**: Visit http://localhost:3000/signin
3. **Dashboard**: After login, manage your tasks at /dashboard
4. **Sign Out**: Click sign out button to end session

## Security Features

- Passwords hashed with bcrypt (via Better Auth)
- JWT tokens with expiration
- User data isolation at database query level
- CORS configuration for allowed origins
- Environment-based secret management

## Success Criteria

- ✅ **SC-001**: Users can complete registration in under 30 seconds
- ✅ **SC-002**: Users can sign in successfully in under 10 seconds
- ✅ **SC-003**: 100% of unauthenticated API requests receive 401 Unauthorized
- ✅ **SC-004**: 100% of users can only access their own tasks
- ✅ **SC-005**: Stateless authentication (no server-side session storage for API)
- ✅ **SC-006**: Generic error messages for invalid credentials
- ✅ **SC-007**: Secure password hashing (never stored in plaintext)

## Phase Evolution

| Phase | Description | Status |
|-------|-------------|--------|
| Phase I | In-memory console application | ✅ Complete (main branch) |
| Phase II | Full-stack web application | ✅ Complete (this branch) |
| Phase III | AI-powered chatbot | Planned |
| Phase IV | Kubernetes deployment | Planned |
| Phase V | Event-driven cloud architecture | Planned |

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| JWT verification fails | Ensure `BETTER_AUTH_SECRET` is identical in frontend and backend |
| Database connection error | Verify `DATABASE_URL` format and Neon project is active |
| CORS errors | Add frontend URL to `CORS_ORIGINS` in backend |
| 401 on all requests | Check token is being sent in Authorization header |

## License

This project is part of "The Evolution of Todo" educational series demonstrating Spec-Driven Development from console to cloud-native AI.
