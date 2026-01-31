# Research: Authentication & API Security

**Feature**: 002-phase2-fullstack | **Date**: 2026-01-25 | **Status**: Complete

## Research Questions

### 1. Better Auth JWT Token Issuance

**Decision**: Use Better Auth's JWT plugin with `definePayload` to customize token claims

**Rationale**:
- Better Auth handles JWT issuance automatically via the JWT plugin
- Tokens include configurable claims (user_id, email) in the payload
- Session stored in httpOnly cookie (secure by default in production)
- JWT available via `/api/auth/token` endpoint when using JWT plugin

**Alternatives Considered**:
- Manual JWT generation: Higher complexity, more security risk
- Bearer tokens only: Acceptable but loses cookie-based session benefits

**Configuration Pattern**:
```typescript
import { betterAuth } from "better-auth"
import { jwt } from "better-auth/plugins"

export const auth = betterAuth({
  secret: process.env.BETTER_AUTH_SECRET,
  plugins: [
    jwt({
      jwt: {
        definePayload: ({ user }) => ({
          id: user.id,
          email: user.email
        })
      }
    })
  ]
})
```

---

### 2. BETTER_AUTH_SECRET Configuration

**Decision**: Single environment variable for JWT signing and verification across frontend and backend

**Rationale**:
- Simplifies key management (one secret for both systems)
- Environment-based configuration prevents accidental secret leakage
- Minimum 32 characters, cryptographically random

**Security Requirements**:
- Never commit to version control
- Different secrets for dev/staging/production
- Generate using: `openssl rand -base64 32`

---

### 3. FastAPI JWT Verification

**Decision**: Use PyJWT library with HTTPBearer dependency injection

**Rationale**:
- PyJWT is simpler and focused specifically on JWT operations
- Better maintained for pure JWT use cases
- HTTPBearer + custom dependency is most flexible pattern
- Automatic OpenAPI/Swagger integration

**Alternatives Considered**:
- python-jose: More comprehensive but heavier for JWT-only operations
- FastAPI-JWT-Auth: Opinionated, less flexibility

**Verification Pattern**:
```python
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()
SECRET_KEY = os.getenv("BETTER_AUTH_SECRET")

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"user_id": payload.get("id"), "email": payload.get("email")}
```

---

### 4. User-Scoped Data Filtering

**Decision**: Filter all queries at database layer using authenticated user_id

**Rationale**:
- Filter at database layer for security and performance
- Return 404 (not 403) for unauthorized access to prevent info leakage
- Never load all data then filter in application code

**Pattern**:
```python
@app.get("/tasks")
async def list_tasks(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    tasks = await db.query(Task).where(Task.user_id == user_id).all()
    return tasks
```

---

### 5. Frontend Token Attachment

**Decision**: Use Better Auth's Bearer plugin for automatic token attachment

**Rationale**:
- Reduces boilerplate and human error
- Automatically includes `Authorization: Bearer <token>` header
- Works with Better Auth session management

**Alternative**: Manual attachment for custom fetch calls:
```typescript
const response = await fetch('/api/tasks', {
  headers: {
    'Authorization': `Bearer ${session?.token}`
  }
})
```

---

### 6. Session Management Strategy

**Decision**: Hybrid approach - Database sessions with cookie caching

**Rationale**:
- Cookie caching reduces database load
- Database sessions enable immediate revocation on logout
- 5-minute cache balances performance and security

**Configuration**:
```typescript
session: {
  expiresIn: 60 * 60 * 24 * 7,  // 7 days
  cookieCache: {
    enabled: true,
    maxAge: 60 * 5  // 5 minutes
  }
}
```

---

## Sources

- Better Auth Documentation: https://www.better-auth.com/docs
- FastAPI Security Tutorial: https://fastapi.tiangolo.com/tutorial/security/
- PyJWT Documentation: https://pyjwt.readthedocs.io
- JWT Best Practices: https://curity.io/resources/learn/jwt-best-practices/
