"""
MCP Authentication Middleware.

Provides JWT validation for MCP server tool calls, ensuring all operations
are scoped to the authenticated user. This is a critical security boundary
for the MCP protocol layer.

Architecture:
- Reuses existing JWT verification from core.security
- Extracts user_id from token for data scoping
- Raises 401 Unauthorized for invalid/missing/expired tokens
- Designed for MCP context (not HTTP middleware)
"""

from typing import Optional, Callable, Any
from functools import wraps
import logging

from ..core.security import verify_token, extract_user_id

logger = logging.getLogger(__name__)


class MCPAuthError(Exception):
    """Raised when MCP authentication fails.

    Attributes:
        message: Error description
        code: HTTP-style error code (401, 403, etc.)
    """

    def __init__(self, message: str, code: int = 401):
        self.message = message
        self.code = code
        super().__init__(self.message)


def validate_mcp_token(token: str) -> str:
    """
    Validate a JWT token for MCP operations and extract user_id.

    This is the core authentication gate for all MCP tool calls.
    Every tool invocation MUST pass through this validation to ensure
    proper data isolation and security.

    Args:
        token: JWT token string (format: "Bearer <token>" or just "<token>")

    Returns:
        User ID string if token is valid

    Raises:
        MCPAuthError: If token is missing, malformed, expired, or invalid

    Security guarantees:
        - Token signature verified against BETTER_AUTH_SECRET
        - Token expiration checked
        - User ID extracted from payload
        - All errors logged with context

    Example:
        ```python
        try:
            user_id = validate_mcp_token(request.headers["Authorization"])
            # Proceed with user-scoped operation
        except MCPAuthError as e:
            # Return 401 error to MCP client
            raise
        ```
    """
    # Normalize token format (strip "Bearer " prefix if present)
    if not token:
        logger.warning("[MCP_AUTH] No token provided in request")
        raise MCPAuthError("Authentication token is required", code=401)

    # Handle "Bearer <token>" format
    if token.startswith("Bearer "):
        token = token[7:].strip()

    if not token:
        logger.warning("[MCP_AUTH] Empty token after Bearer prefix removal")
        raise MCPAuthError("Authentication token is empty", code=401)

    # Verify token using existing security module
    try:
        payload = verify_token(token)
    except Exception as e:
        logger.error(f"[MCP_AUTH] Token verification failed: {type(e).__name__}: {e}")
        raise MCPAuthError("Invalid or expired authentication token", code=401)

    if payload is None:
        logger.warning("[MCP_AUTH] Token verification returned None (invalid token)")
        raise MCPAuthError("Invalid or expired authentication token", code=401)

    # Extract user_id from payload
    user_id = extract_user_id(payload)

    if not user_id:
        logger.error(f"[MCP_AUTH] Token payload missing 'id' field: {payload.keys()}")
        raise MCPAuthError("Token does not contain user identification", code=401)

    logger.info(f"[MCP_AUTH] Successfully authenticated user_id={user_id}")
    return user_id


def require_mcp_auth(func: Callable) -> Callable:
    """
    Decorator to enforce JWT authentication on MCP tool functions.

    This decorator extracts the JWT token from function arguments,
    validates it, and injects the authenticated user_id into the
    function's context.

    Usage:
        ```python
        @require_mcp_auth
        async def add_task(context: dict, title: str, priority: str) -> dict:
            user_id = context["user_id"]  # Injected by decorator
            # Create task for this user
            ...
        ```

    The decorator expects:
        - First argument is a context dict with "token" key
        - Returns modified context with "user_id" added

    Args:
        func: Async function to wrap (must accept context as first arg)

    Returns:
        Wrapped function with authentication enforcement

    Raises:
        MCPAuthError: If authentication fails
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        """Wrapper that validates token and injects user_id."""
        # Extract context (assumed to be first argument)
        if not args or not isinstance(args[0], dict):
            logger.error(f"[MCP_AUTH] Decorator used on function without context dict: {func.__name__}")
            raise MCPAuthError("Internal error: MCP authentication configuration error", code=500)

        context = args[0]

        # Extract token from context
        token = context.get("token")
        if not token:
            logger.warning(f"[MCP_AUTH] No token in context for {func.__name__}")
            raise MCPAuthError("Authentication token is required", code=401)

        # Validate token and get user_id
        user_id = validate_mcp_token(token)

        # Inject user_id into context
        context["user_id"] = user_id

        # Call original function
        return await func(*args, **kwargs)

    return wrapper


# Convenience function for FastAPI dependency injection (if needed)
async def get_mcp_user_id(authorization: Optional[str] = None) -> str:
    """
    FastAPI dependency for extracting user_id from Authorization header.

    This can be used in FastAPI endpoints that serve MCP protocol requests.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")

    Returns:
        Authenticated user_id

    Raises:
        MCPAuthError: If authentication fails

    Example:
        ```python
        @app.post("/mcp/tools/add_task")
        async def mcp_add_task(
            user_id: str = Depends(get_mcp_user_id),
            request: TaskCreateInput
        ):
            # user_id is authenticated and ready to use
            ...
        ```
    """
    if not authorization:
        raise MCPAuthError("Authorization header is required", code=401)

    return validate_mcp_token(authorization)
