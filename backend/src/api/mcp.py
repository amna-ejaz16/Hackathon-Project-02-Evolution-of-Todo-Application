"""
MCP (Model Context Protocol) API endpoint.

This module provides FastAPI endpoints for MCP server integration, exposing
task management operations as MCP tools that can be consumed by MCP-compatible
clients.

Architecture:
- REST endpoints for MCP tool invocation (HTTP transport)
- Tool discovery endpoint (tools/list)
- JWT authentication via Authorization header
- Structured error responses per MCP protocol

Note: This is a REST-based MCP implementation. WebSocket support can be added
if needed by Official MCP SDK integration.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlmodel import Session
from pydantic import BaseModel, Field

from ..core.database import get_session
from ..services.mcp_service import (
    MCPTaskTools,
    MCPError,
    create_mcp_tools_manifest,
)
from ..middleware.mcp_auth import validate_mcp_token, MCPAuthError

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Request/Response Models ---

class MCPToolCallRequest(BaseModel):
    """Generic request model for MCP tool invocation."""

    tool_name: str = Field(..., description="Name of the MCP tool to invoke")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class MCPToolCallResponse(BaseModel):
    """Generic response model for MCP tool results."""

    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[Dict[str, Any]] = None


# --- Helper Functions ---

async def get_mcp_user_context(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and validate user context from JWT.

    Args:
        authorization: Authorization header (format: "Bearer <token>")

    Returns:
        Context dict with user_id and token

    Raises:
        HTTPException 401: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = validate_mcp_token(authorization)
        return {
            "user_id": user_id,
            "token": authorization,
        }
    except MCPAuthError as e:
        raise HTTPException(
            status_code=e.code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- MCP Endpoints ---

@router.get("/tools/list", tags=["MCP"])
async def list_mcp_tools() -> Dict[str, Any]:
    """
    MCP tool discovery endpoint.

    Returns a manifest of all available MCP tools with their schemas,
    descriptions, and input requirements. This endpoint does NOT require
    authentication (tool discovery is public).

    Returns:
        MCP tools manifest with tool metadata and input schemas

    Example Response:
        {
            "tools": [
                {
                    "name": "add_task",
                    "description": "Create a new task...",
                    "input_schema": {...}
                },
                ...
            ]
        }
    """
    logger.info("[MCP_API] Tool discovery request received")
    return create_mcp_tools_manifest()


@router.post("/tools/add_task", tags=["MCP"], response_model=MCPToolCallResponse)
async def mcp_add_task(
    title: str = Query(..., min_length=1, max_length=200),
    description: Optional[str] = Query(None),
    priority: str = Query("medium"),
    category: Optional[str] = Query(None),
    due_date: Optional[str] = Query(None),
    context: Dict[str, Any] = Depends(get_mcp_user_context),
    session: Session = Depends(get_session),
) -> MCPToolCallResponse:
    """
    MCP Tool: add_task

    Create a new task for the authenticated user.

    Requires JWT authentication via Authorization header.

    Args:
        title: Task title (required, 1-200 characters)
        description: Optional task description
        priority: Priority level (low/medium/high), default medium
        category: Optional category/tag
        due_date: Optional due date in ISO format (YYYY-MM-DD)
        context: User context from JWT (injected)
        session: Database session (injected)

    Returns:
        MCP tool response with created task data

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 400: If validation fails
        HTTPException 500: If operation fails
    """
    try:
        tools = MCPTaskTools(session=session)
        result = await tools.add_task(
            context=context,
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
        )
        return MCPToolCallResponse(**result)

    except MCPError as e:
        logger.warning(f"[MCP_API] add_task MCP error: {e.code} - {e.message}")
        if e.code == "VALIDATION_ERROR":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.to_dict())
        elif e.code == "UNAUTHORIZED":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.to_dict())
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.to_dict())
    except Exception as e:
        logger.error(f"[MCP_API] add_task unexpected error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Operation failed"}}
        )


@router.get("/tools/list_tasks", tags=["MCP"], response_model=MCPToolCallResponse)
async def mcp_list_tasks(
    status_filter: str = Query("all"),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    context: Dict[str, Any] = Depends(get_mcp_user_context),
    session: Session = Depends(get_session),
) -> MCPToolCallResponse:
    """
    MCP Tool: list_tasks

    List tasks for the authenticated user with optional filtering.

    Requires JWT authentication via Authorization header.

    Args:
        status_filter: Filter by status (all/pending/completed), default all
        priority: Filter by priority (low/medium/high), optional
        category: Filter by category, optional
        page: Page number for pagination, default 1
        page_size: Results per page, default 20
        context: User context from JWT (injected)
        session: Database session (injected)

    Returns:
        MCP tool response with list of tasks

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 500: If operation fails
    """
    try:
        tools = MCPTaskTools(session=session)
        result = await tools.list_tasks(
            context=context,
            status=status_filter,
            priority=priority,
            category=category,
            page=page,
            page_size=page_size,
        )
        return MCPToolCallResponse(**result)

    except MCPError as e:
        logger.warning(f"[MCP_API] list_tasks MCP error: {e.code} - {e.message}")
        if e.code == "VALIDATION_ERROR":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.to_dict())
        elif e.code == "UNAUTHORIZED":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.to_dict())
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.to_dict())
    except Exception as e:
        logger.error(f"[MCP_API] list_tasks unexpected error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Operation failed"}}
        )


@router.post("/tools/complete_task", tags=["MCP"], response_model=MCPToolCallResponse)
async def mcp_complete_task(
    task_id: int = Query(..., gt=0),
    context: Dict[str, Any] = Depends(get_mcp_user_context),
    session: Session = Depends(get_session),
) -> MCPToolCallResponse:
    """
    MCP Tool: complete_task

    Mark a task as completed for the authenticated user.

    Requires JWT authentication via Authorization header.

    Args:
        task_id: ID of the task to mark as complete
        context: User context from JWT (injected)
        session: Database session (injected)

    Returns:
        MCP tool response with updated task data

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 404: If task not found
        HTTPException 500: If operation fails
    """
    try:
        tools = MCPTaskTools(session=session)
        result = await tools.complete_task(
            context=context,
            task_id=task_id,
        )
        return MCPToolCallResponse(**result)

    except MCPError as e:
        logger.warning(f"[MCP_API] complete_task MCP error: {e.code} - {e.message}")
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
        elif e.code == "VALIDATION_ERROR":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.to_dict())
        elif e.code == "UNAUTHORIZED":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.to_dict())
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.to_dict())
    except Exception as e:
        logger.error(f"[MCP_API] complete_task unexpected error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Operation failed"}}
        )


@router.delete("/tools/delete_task", tags=["MCP"], response_model=MCPToolCallResponse)
async def mcp_delete_task(
    task_id: int = Query(..., gt=0),
    context: Dict[str, Any] = Depends(get_mcp_user_context),
    session: Session = Depends(get_session),
) -> MCPToolCallResponse:
    """
    MCP Tool: delete_task

    Permanently delete a task for the authenticated user.

    Requires JWT authentication via Authorization header.

    Args:
        task_id: ID of the task to delete
        context: User context from JWT (injected)
        session: Database session (injected)

    Returns:
        MCP tool response with deletion confirmation

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 404: If task not found
        HTTPException 500: If operation fails
    """
    try:
        tools = MCPTaskTools(session=session)
        result = await tools.delete_task(
            context=context,
            task_id=task_id,
        )
        return MCPToolCallResponse(**result)

    except MCPError as e:
        logger.warning(f"[MCP_API] delete_task MCP error: {e.code} - {e.message}")
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
        elif e.code == "VALIDATION_ERROR":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.to_dict())
        elif e.code == "UNAUTHORIZED":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.to_dict())
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.to_dict())
    except Exception as e:
        logger.error(f"[MCP_API] delete_task unexpected error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Operation failed"}}
        )


@router.put("/tools/update_task", tags=["MCP"], response_model=MCPToolCallResponse)
async def mcp_update_task(
    task_id: int = Query(..., gt=0),
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    due_date: Optional[str] = Query(None),
    context: Dict[str, Any] = Depends(get_mcp_user_context),
    session: Session = Depends(get_session),
) -> MCPToolCallResponse:
    """
    MCP Tool: update_task

    Update task properties (partial update) for the authenticated user.

    Requires JWT authentication via Authorization header.

    Args:
        task_id: ID of the task to update (required)
        title: New title, optional
        description: New description, optional
        priority: New priority (low/medium/high), optional
        category: New category, optional
        due_date: New due date in ISO format (YYYY-MM-DD), optional
        context: User context from JWT (injected)
        session: Database session (injected)

    Returns:
        MCP tool response with updated task data

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 404: If task not found
        HTTPException 400: If validation fails
        HTTPException 500: If operation fails
    """
    try:
        tools = MCPTaskTools(session=session)
        result = await tools.update_task(
            context=context,
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
        )
        return MCPToolCallResponse(**result)

    except MCPError as e:
        logger.warning(f"[MCP_API] update_task MCP error: {e.code} - {e.message}")
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
        elif e.code == "VALIDATION_ERROR":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.to_dict())
        elif e.code == "UNAUTHORIZED":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.to_dict())
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.to_dict())
    except Exception as e:
        logger.error(f"[MCP_API] update_task unexpected error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Operation failed"}}
        )
