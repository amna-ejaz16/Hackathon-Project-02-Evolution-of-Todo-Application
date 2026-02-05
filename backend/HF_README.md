---
title: Todo API
emoji: ✅
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# Todo Application API

FastAPI backend for the multi-user Todo Application with JWT authentication.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger documentation |
| POST | `/api/tasks` | Create a new task |
| GET | `/api/tasks` | List all tasks for authenticated user |
| GET | `/api/tasks/{id}` | Get a specific task |
| PUT | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |

## Authentication

This API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `BETTER_AUTH_SECRET` | JWT secret key (32+ characters) |
| `PORT` | Server port (default: 7860) |
| `DEBUG` | Enable debug mode (default: false) |

## Technology Stack

- **Framework**: FastAPI
- **ORM**: SQLModel
- **Database**: Neon PostgreSQL
- **Authentication**: Better Auth (JWT)
