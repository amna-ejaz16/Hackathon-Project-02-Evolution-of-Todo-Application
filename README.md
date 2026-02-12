# Todo Application - Phase III: AI-Powered Chatbot

A secure, multi-user todo application with AI-powered chatbot assistance, built using Next.js, FastAPI, Better Auth, OpenAI Agents SDK, and Neon PostgreSQL.

## Features

- **User Authentication**: Secure signup/signin with Better Auth and JWT tokens
- **Multi-User Support**: Complete user isolation - each user sees only their own tasks
- **Full CRUD Operations**: Create, read, update, and delete tasks
- **Task Management**: Mark tasks complete/incomplete, add descriptions
- **AI Chatbot Assistant**: Context-aware AI chatbot powered by OpenAI Agents SDK
- **Conversation History**: Persistent conversation storage per user
- **Responsive UI**: Modern interface built with Next.js and Tailwind CSS
- **Secure API**: JWT-protected endpoints with stateless authentication

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16+ (App Router), React 19, Tailwind CSS, Framer Motion |
| Backend | Python 3.11+ FastAPI, SQLModel ORM |
| AI Engine | OpenAI Agents SDK (>= 0.8.0) |
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
│   │   │   ├── chat.py       # Chat/Chatbot endpoints
│   │   │   └── health.py     # Health check
│   │   ├── core/
│   │   │   ├── config.py     # Environment config
│   │   │   ├── database.py   # Neon DB connection
│   │   │   └── security.py   # JWT verification
│   │   ├── models/
│   │   │   ├── task.py       # Task SQLModel
│   │   │   ├── user.py       # User model
│   │   │   ├── conversation.py # Conversation model
│   │   │   └── message.py     # Message model
│   │   ├── services/
│   │   │   └── chat_service.py # AI Chatbot service with OpenAI Agents SDK
│   │   └── main.py            # FastAPI app
│   └── requirements.txt
│
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatBot/      # AI Chatbot UI components
│   │   └── ...
│   └── ...
│
└── specs/                    # Spec-Driven Development artifacts
    ├── 001-phase1-console-todo/
    │   ├── spec.md
    │   ├── plan.md
    │   └── tasks.md
    ├── 002-phase2-fullstack/
    │   ├── spec.md
    │   ├── plan.md
    │   └── tasks.md
    └── 003-phase3-ai-chatbot/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Setup Instructions

### 1. Clone and Checkout Phase 3 Branch

```bash
git clone <repository-url>
cd The-Evolution-of-Todo-Application
git checkout 003-phase3-ai-chatbot
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
OPENAI_API_KEY=your-openai-api-key
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

### Chatbot (FastAPI - Backend)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/message` | Send message to chatbot |
| GET | `/api/chat/conversations` | Get all conversations (user-scoped) |
| GET | `/api/chat/conversations/{id}` | Get conversation history |
| GET | `/health` | Health check |

All `/api/*` endpoints require `Authorization: Bearer <token>` header.

## Authentication Flow

```
1. User signs up/in → Better Auth creates session + issues JWT
2. Frontend stores JWT → Attaches to API requests
3. Backend receives request → Extracts JWT from Authorization header
4. Backend verifies JWT → Uses shared BETTER_AUTH_SECRET
5. Backend identifies user → Filters tasks by user_id from token
6. Response returned → Only user's own data
```

## AI Chatbot Features (Phase III)

### Capabilities
- **Context-Aware Assistance**: The chatbot understands your tasks and can help with task management
- **Natural Language Interaction**: Ask questions and get AI-powered responses
- **Task Context**: The AI has access to your current tasks for better assistance
- **Conversation History**: All conversations are saved per user
- **Persistent Storage**: Conversations stored in Neon PostgreSQL for future reference

### Database Schema (Phase III)
- **conversation** table: Stores conversation metadata (user_id, created_at, updated_at)
- **message** table: Stores individual messages (conversation_id, role, content, created_at)

## Usage

1. **Register**: Visit http://localhost:3000/signup
2. **Sign In**: Visit http://localhost:3000/signin
3. **Dashboard**: After login, manage your tasks at /dashboard
4. **Chat with AI**: Open the chatbot window (bottom-right corner) to interact with the AI assistant
5. **Sign Out**: Click sign out button to end session

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

| Phase | Description | Status | Branch |
|-------|-------------|--------|--------|
| Phase I | In-memory console application | ✅ Complete | `001-phase1-console-todo` |
| Phase II | Full-stack web application | ✅ Complete | `002-phase2-fullstack` |
| Phase III | AI-powered chatbot with OpenAI Agents | 🚀 In Progress | `003-phase3-ai-chatbot` |
| Phase IV | Kubernetes deployment | Planned | TBD |
| Phase V | Event-driven cloud architecture | Planned | TBD |

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| JWT verification fails | Ensure `BETTER_AUTH_SECRET` is identical in frontend and backend |
| Database connection error | Verify `DATABASE_URL` format and Neon project is active |
| CORS errors | Add frontend URL to `CORS_ORIGINS` in backend |
| 401 on all requests | Check token is being sent in Authorization header |
| Chatbot not responding | Verify `OPENAI_API_KEY` is set in backend `.env` |
| Chat service error | Check that conversation and message tables exist in Neon database |
| Chatbot window not visible | Ensure frontend is running and check browser console for errors |

## License

This project is part of "The Evolution of Todo" educational series demonstrating Spec-Driven Development from console to cloud-native AI.
