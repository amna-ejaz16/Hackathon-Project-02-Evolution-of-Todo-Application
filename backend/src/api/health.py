"""Health check and debug endpoints."""

import base64
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.security import verify_token, ALGORITHM

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    timestamp: datetime


class AuthDebugResponse(BaseModel):
    """Auth debug response schema."""

    token_received: bool
    token_preview: Optional[str] = None
    token_length: Optional[int] = None
    token_header: Optional[dict] = None
    token_valid: bool
    error: Optional[str] = None
    expected_algorithm: str
    secret_preview: str
    secret_length: int


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the API health status and current timestamp.
    No authentication required.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
    )


@router.get("/debug/auth", response_model=AuthDebugResponse)
async def auth_debug(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> AuthDebugResponse:
    """
    Debug endpoint to test JWT token verification.

    Send a request with Authorization: Bearer <token> header to test.
    Returns detailed information about the token and verification result.
    """
    settings = get_settings()

    # Check if token was received
    if not authorization:
        return AuthDebugResponse(
            token_received=False,
            token_valid=False,
            error="No Authorization header received",
            expected_algorithm=ALGORITHM,
            secret_preview=settings.better_auth_secret[:10] + "...",
            secret_length=len(settings.better_auth_secret),
        )

    # Parse Bearer token
    if not authorization.startswith("Bearer "):
        return AuthDebugResponse(
            token_received=True,
            token_preview=authorization[:30] + "..." if len(authorization) > 30 else authorization,
            token_length=len(authorization),
            token_valid=False,
            error="Authorization header must start with 'Bearer '",
            expected_algorithm=ALGORITHM,
            secret_preview=settings.better_auth_secret[:10] + "...",
            secret_length=len(settings.better_auth_secret),
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    logger.info(f"[Debug Auth] Token received (first 50 chars): {token[:50]}...")

    # Try to decode header
    token_header = None
    try:
        parts = token.split(".")
        if len(parts) == 3:
            header_b64 = parts[0]
            # Add padding if needed
            padding = 4 - len(header_b64) % 4
            if padding != 4:
                header_b64 += "=" * padding
            header_json = base64.urlsafe_b64decode(header_b64)
            token_header = json.loads(header_json)
            logger.info(f"[Debug Auth] Token header: {token_header}")
    except Exception as e:
        logger.error(f"[Debug Auth] Failed to decode header: {e}")

    # Try to verify token
    try:
        payload = verify_token(token)
        if payload:
            return AuthDebugResponse(
                token_received=True,
                token_preview=token[:50] + "...",
                token_length=len(token),
                token_header=token_header,
                token_valid=True,
                expected_algorithm=ALGORITHM,
                secret_preview=settings.better_auth_secret[:10] + "...",
                secret_length=len(settings.better_auth_secret),
            )
        else:
            return AuthDebugResponse(
                token_received=True,
                token_preview=token[:50] + "...",
                token_length=len(token),
                token_header=token_header,
                token_valid=False,
                error="Token verification failed (check backend logs for details)",
                expected_algorithm=ALGORITHM,
                secret_preview=settings.better_auth_secret[:10] + "...",
                secret_length=len(settings.better_auth_secret),
            )
    except Exception as e:
        logger.error(f"[Debug Auth] Exception during verification: {e}")
        return AuthDebugResponse(
            token_received=True,
            token_preview=token[:50] + "...",
            token_length=len(token),
            token_header=token_header,
            token_valid=False,
            error=f"{type(e).__name__}: {str(e)}",
            expected_algorithm=ALGORITHM,
            secret_preview=settings.better_auth_secret[:10] + "...",
            secret_length=len(settings.better_auth_secret),
        )
