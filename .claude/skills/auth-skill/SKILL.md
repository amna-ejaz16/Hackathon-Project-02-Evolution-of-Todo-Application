---
name: auth-skill
description: Handle secure user authentication including signup, signin, password hashing, JWT tokens, and Better Auth integration.
---

# Auth Skill – Secure Authentication

## Instructions

1. **Signup Flow**
   - Collect user credentials securely
   - Validate input (email format, password strength)
   - Hash passwords before storage
   - Prevent duplicate accounts

2. **Signin Flow**
   - Verify user credentials
   - Compare hashed passwords securely
   - Handle invalid login attempts gracefully

3. **Password Security**
   - Use industry-standard hashing (bcrypt, argon2)
   - Apply salting and proper cost factors
   - Never store or log plain-text passwords

4. **JWT Authentication**
   - Generate access tokens securely
   - Include minimal, non-sensitive claims
   - Set expiration and refresh strategies
   - Verify tokens on protected routes

5. **Better Auth Integration**
   - Follow Better Auth recommended patterns
   - Integrate with existing backend and frontend auth flows
   - Ensure compatibility with session or token-based auth

## Validation Rules

- Validate all inputs server-side
- Enforce strong password policies
- Sanitize user-provided data
- Return clear, safe error messages (no sensitive leaks)

## Best Practices

- Use HTTPS-only authentication flows
- Separate auth logic from business logic
- Centralize token verification middleware
- Rotate secrets and keys securely
- Follow OWASP authentication guidelines

## Example Flow (Backend Pseudocode)

```python
# Signup
hashed_password = hash_password(user_password)
save_user(email, hashed_password)

# Signin
if verify_password(input_password, stored_hash):
    token = generate_jwt(user_id)
    return token
