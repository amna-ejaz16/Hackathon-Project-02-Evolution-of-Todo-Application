# Implementation Plan: Authentication & API Security

**Branch**: `002-phase2-fullstack` | **Date**: 2026-01-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-phase2-fullstack/spec.md`

## Summary

Implement secure multi-user authentication using Better Auth on the Next.js frontend and JWT-based authorization on the FastAPI backend. The system will use a shared secret (BETTER_AUTH_SECRET) for token signing/verification, enabling stateless API authorization with user-scoped data filtering for all task operations.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/Node.js 20+ (frontend)
**Primary Dependencies**:
- Frontend: better-auth, @better-auth/react, next 16+
- Backend: FastAPI, SQLModel, PyJWT, python-dotenv
**Storage**: Neon PostgreSQL (users table, sessions table via Better Auth, tasks table)
**Testing**: pytest (backend), vitest/jest (frontend)
**Target Platform**: Web application (Linux server for backend, Vercel/Node for frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Token verification < 50ms latency, sign-in < 10 seconds
**Constraints**: Stateless API authorization, no server-side session storage for API auth
**Scale/Scope**: Multi-user application, 100+ concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Notes |
|-----------|--------|----------------|
| I. Specification First | PASS | Spec completed before this plan |
| II. Deterministic Behavior | PASS | JWT verification is deterministic (same token + secret = same result) |
| III. Incremental Evolution | PASS | Builds on Phase 1 console app concepts, adds auth layer |
| IV. Separation of Concerns | PASS | Auth (Better Auth) separate from API (FastAPI) separate from data (Neon) |
| V. Testability | PASS | All auth flows testable: token generation, verification, rejection |
| VI. Observability | PASS | Logging for auth events (sign-in, sign-out, failures) planned |
| VII. AI Constraint | N/A | No AI components in auth feature |
| VIII. Simplicity (YAGNI) | PASS | No OAuth, RBAC, refresh tokens (explicitly out of scope) |

**Phase II Compliance**:
- REST-based API contracts specified before implementation
- Schema-first design (User, Session, Task models defined)
- Frontend/backend/database layers independently testable

## Project Structure

### Documentation (this feature)

```text
specs/002-phase2-fullstack/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model design
├── quickstart.md        # Phase 1 developer setup guide
├── contracts/           # Phase 1 API contracts
│   └── auth-api.yaml    # OpenAPI spec for auth endpoints
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── user.py          # User SQLModel
│   │   └── task.py          # Task SQLModel with user_id FK
│   ├── services/
│   │   └── auth.py          # JWT verification service
│   ├── api/
│   │   ├── deps.py          # FastAPI dependencies (get_current_user)
│   │   ├── tasks.py         # Task CRUD endpoints (protected)
│   │   └── health.py        # Health check (unprotected)
│   └── core/
│       ├── config.py        # Environment config (BETTER_AUTH_SECRET)
│       └── security.py      # JWT decode/verify functions
└── tests/
    ├── unit/
    │   └── test_jwt.py      # JWT verification tests
    └── integration/
        └── test_auth.py     # End-to-end auth flow tests

frontend/
├── src/
│   ├── lib/
│   │   └── auth.ts          # Better Auth client configuration
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── signin/
│   │   │   │   └── page.tsx # Sign-in page
│   │   │   └── signup/
│   │   │       └── page.tsx # Sign-up page
│   │   ├── api/
│   │   │   └── auth/
│   │   │       └── [...all]/
│   │   │           └── route.ts # Better Auth API routes
│   │   └── dashboard/
│   │       └── page.tsx     # Protected task dashboard
│   └── middleware.ts        # Route protection middleware
└── tests/
    └── auth.test.ts         # Auth flow tests
```

**Structure Decision**: Web application structure with separate frontend and backend directories. Backend handles JWT verification and user-scoped data; frontend handles authentication UI and token attachment.

## Complexity Tracking

> No violations requiring justification. Design follows YAGNI principle by excluding OAuth, RBAC, refresh tokens per spec scope.

## Architecture Overview

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AUTHENTICATION FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. SIGN UP / SIGN IN                                                 │
│     ┌──────────────┐       ┌──────────────┐       ┌──────────────┐   │
│     │   Browser    │──────▶│  Next.js     │──────▶│  Better Auth │   │
│     │   (User)     │       │  Frontend    │       │  (Session)   │   │
│     └──────────────┘       └──────────────┘       └──────┬───────┘   │
│                                                           │           │
│                                    Issues JWT token ◀─────┘           │
│                                    (includes user_id, email)          │
│                                                                       │
│  2. API REQUEST WITH JWT                                              │
│     ┌──────────────┐       ┌──────────────┐       ┌──────────────┐   │
│     │   Browser    │──────▶│  Next.js     │──────▶│   FastAPI    │   │
│     │   (User)     │       │  (attach     │       │   Backend    │   │
│     │              │       │   Bearer)    │       │              │   │
│     └──────────────┘       └──────────────┘       └──────┬───────┘   │
│                                                           │           │
│                            Verify JWT signature ◀─────────┘           │
│                            (using BETTER_AUTH_SECRET)                 │
│                                                                       │
│  3. USER-SCOPED DATA ACCESS                                           │
│     ┌──────────────┐       ┌──────────────┐       ┌──────────────┐   │
│     │   FastAPI    │──────▶│   SQLModel   │──────▶│ Neon        │   │
│     │   (user_id   │       │   Query      │       │ PostgreSQL  │   │
│     │    from JWT) │       │   (WHERE     │       │             │   │
│     │              │       │    user_id=) │       │             │   │
│     └──────────────┘       └──────────────┘       └──────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Security Model

| Layer | Responsibility | Technology |
|-------|---------------|------------|
| Authentication | Verify user identity (email/password) | Better Auth |
| Token Issuance | Create signed JWT with user claims | Better Auth |
| Token Transport | Attach JWT to Authorization header | Next.js fetch |
| Token Verification | Verify signature, extract user_id | PyJWT |
| Authorization | Filter data by authenticated user_id | SQLModel queries |

### Key Design Decisions

1. **Stateless API Authorization**: JWT tokens are self-contained; backend verifies signature without database lookup for basic auth (SC-005)

2. **Shared Secret**: BETTER_AUTH_SECRET environment variable used by both Better Auth (signing) and FastAPI (verification)

3. **User Isolation**: All task queries include `WHERE user_id = <authenticated_user_id>` (FR-012, FR-013)

4. **Generic Error Messages**: All auth failures return "Could not validate credentials" to prevent user enumeration (SC-006)

5. **Password Hashing**: Better Auth uses scrypt by default (secure, no plaintext storage) (FR-004, SC-007)

## Implementation Phases

### Phase 0: Research (COMPLETED)
- [x] Better Auth JWT configuration patterns
- [x] FastAPI JWT verification with PyJWT
- [x] User-scoped data filtering patterns

### Phase 1: Design (THIS PLAN)
- [ ] Data model design (users, sessions, tasks)
- [ ] API contracts (auth endpoints)
- [ ] Developer quickstart guide

### Phase 2: Tasks (via /sp.tasks)
- [ ] Generate implementation tasks from this plan
- [ ] TDD: Write failing tests first
- [ ] Implement auth components
- [ ] Integration testing

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Secret key exposure | Low | Critical | Environment variables, .gitignore |
| Token expiration confusion | Medium | Medium | Clear error messages, 24h default |
| Cross-user data leakage | Low | Critical | Mandatory user_id filtering on all queries |

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks
2. Set up environment variables (BETTER_AUTH_SECRET, DATABASE_URL)
3. Implement backend JWT verification first (can test independently)
4. Implement frontend Better Auth integration
5. Connect frontend to backend with protected endpoints
