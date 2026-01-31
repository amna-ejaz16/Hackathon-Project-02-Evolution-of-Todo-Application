---
name: backend-skill
description: Handle backend development including route generation, request/response handling, and database connectivity.
---

# Backend Skill – Routes, Requests, and Database

## Instructions

1. **Route Generation**
   - Define clear, RESTful or RPC routes
   - Group related routes logically (e.g., /tasks, /auth)
   - Use route versioning when necessary (e.g., /v1/tasks)
   - Include route documentation for clarity

2. **Request & Response Handling**
   - Validate incoming request data
   - Sanitize inputs to prevent security vulnerabilities
   - Return structured responses (status codes, JSON payloads)
   - Handle errors gracefully with meaningful messages
   - Apply middleware for logging, authentication, or rate-limiting

3. **Database Connectivity**
   - Connect backend routes to database queries
   - Use ORM or query builders for consistency
   - Handle transactions for multi-step operations
   - Ensure efficient and secure data access

4. **Security & Validation**
   - Validate inputs and outputs rigorously
   - Protect sensitive data (passwords, tokens)
   - Apply Auth Skill where applicable
   - Ensure routes are secured and access-controlled

## Best Practices

- Keep route handlers small and modular
- Follow consistent naming conventions
- Separate business logic from controller/routes
- Document all API endpoints clearly
- Handle edge cases and exceptions gracefully

## Example Route (FastAPI)

```python
from fastapi import APIRouter, HTTPException
from services.task_manager import TaskManager

router = APIRouter()

@router.post("/tasks")
def create_task(title: str, description: str = ""):
    task = TaskManager().add_task(title, description)
    return {"status": "success", "task": task}
