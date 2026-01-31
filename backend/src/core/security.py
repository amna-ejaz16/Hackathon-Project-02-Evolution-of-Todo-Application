"""JWT verification and security utilities."""

import logging
import base64
import json
from typing import Optional
import jwt
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    DecodeError,
    InvalidAlgorithmError,
    InvalidSignatureError,
)

from .config import get_settings

logger = logging.getLogger(__name__)

# JWT algorithm - MUST match frontend token generation (jose library)
# The jose library uses "HS256" and PyJWT expects exactly "HS256" (case-sensitive)
ALGORITHM = "HS256"


def _decode_token_header(token: str) -> Optional[dict]:
    """
    Decode JWT header without verification for debugging.

    Args:
        token: The JWT token string

    Returns:
        Decoded header dict or None if malformed
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            logger.error(f"Token has {len(parts)} parts, expected 3")
            return None

        # Decode header (base64url)
        header_b64 = parts[0]
        # Add padding if needed
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding

        header_json = base64.urlsafe_b64decode(header_b64)
        header = json.loads(header_json)
        return header
    except Exception as e:
        logger.error(f"Failed to decode token header: {e}")
        return None


def verify_token(token: str) -> Optional[dict]:
    """
    Verify a JWT token and return the payload.

    Args:
        token: The JWT token string

    Returns:
        Decoded payload dict if valid, None if invalid

    The payload is expected to contain:
        - id: User UUID
        - email: User email
        - iat: Issued at timestamp
        - exp: Expiration timestamp
    """
    settings = get_settings()

    # Debug: Log token info (first 50 chars only for security)
    token_preview = token[:50] + "..." if len(token) > 50 else token
    logger.info(f"Verifying token: {token_preview}")

    # Debug: Decode header to see what algorithm the token claims to use
    header = _decode_token_header(token)
    if header:
        logger.info(f"Token header: alg={header.get('alg')}, typ={header.get('typ')}")
    else:
        logger.error("Could not decode token header - malformed token")
        return None

    # Check if token algorithm matches expected
    token_alg = header.get("alg")
    if token_alg != ALGORITHM:
        logger.error(f"Algorithm mismatch! Token uses '{token_alg}', expected '{ALGORITHM}'")
        return None

    try:
        # Decode and verify the token
        # CRITICAL: The secret must match exactly what frontend uses
        logger.info(f"Using secret (first 10 chars): {settings.better_auth_secret[:10]}...")

        payload = jwt.decode(
            token,
            settings.better_auth_secret,
            algorithms=[ALGORITHM],
        )
        logger.info(f"Token verified successfully for user: {payload.get('email')}")
        return payload

    except ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except InvalidAlgorithmError as e:
        logger.error(f"ALGORITHM ERROR: {e}")
        logger.error(f"  Token algorithm: {header.get('alg') if header else 'unknown'}")
        logger.error(f"  Allowed algorithm: {ALGORITHM}")
        return None
    except InvalidSignatureError as e:
        logger.error(f"SIGNATURE ERROR: {e}")
        logger.error(f"  Secret used (first 10 chars): {settings.better_auth_secret[:10]}...")
        return None
    except DecodeError as e:
        logger.error(f"DECODE ERROR: {e}")
        return None
    except InvalidTokenError as e:
        logger.error(f"INVALID TOKEN ERROR: {type(e).__name__}: {e}")
        return None
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return None


def extract_user_id(payload: dict) -> Optional[str]:
    """
    Extract user ID from a decoded JWT payload.

    Args:
        payload: Decoded JWT payload

    Returns:
        User ID string if present, None otherwise.

    Note:
        Better Auth uses TEXT-based IDs (not UUIDs), so we return
        the ID as-is without UUID conversion.
    """
    user_id = payload.get("id")
    if user_id is None:
        return None

    # Return as string - Better Auth uses text-based IDs
    return str(user_id)


def extract_email(payload: dict) -> Optional[str]:
    """
    Extract email from a decoded JWT payload.

    Args:
        payload: Decoded JWT payload

    Returns:
        Email string if present, None otherwise
    """
    return payload.get("email")
