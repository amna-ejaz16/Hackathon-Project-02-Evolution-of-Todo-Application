"""FastAPI dependencies for authentication and authorization."""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.security import verify_token, extract_user_id, extract_email

logger = logging.getLogger(__name__)

# HTTPBearer extracts token from Authorization header
security = HTTPBearer()


class CurrentUser:
    """Authenticated user information extracted from JWT.

    Note: user_id is a string (TEXT) to match Better Auth's ID format.
    """

    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> CurrentUser:
    """
    Dependency to get the current authenticated user from JWT.

    Extracts the Bearer token from the Authorization header,
    verifies it, and returns user information.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    # Debug: Log received token info
    logger.info(f"[Auth] Received token (first 50 chars): {token[:50] if len(token) > 50 else token}...")
    logger.info(f"[Auth] Token length: {len(token)}")

    payload = verify_token(token)

    if payload is None:
        logger.error("[Auth] Token verification FAILED - returning 401")
        raise credentials_exception

    user_id = extract_user_id(payload)
    email = extract_email(payload)

    if user_id is None or email is None:
        logger.warning(f"[Auth] Token missing required claims - id: {user_id}, email: {email}")
        raise credentials_exception

    logger.info(f"[Auth] SUCCESS - Authenticated user: {email} (id: {user_id})")
    return CurrentUser(user_id=user_id, email=email)
