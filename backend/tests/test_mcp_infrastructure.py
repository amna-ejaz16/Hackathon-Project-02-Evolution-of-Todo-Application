"""
Integration tests for MCP infrastructure.

These tests verify that all BLOCKING Phase 2 dependencies are properly
established and functional.

Run with: pytest backend/tests/test_mcp_infrastructure.py -v
"""

import pytest
from datetime import date

# Test imports to verify all modules are accessible
def test_imports():
    """Verify all MCP infrastructure modules can be imported."""
    # Middleware
    from src.middleware.mcp_auth import (
        MCPAuthError,
        validate_mcp_token,
        require_mcp_auth,
        get_mcp_user_id
    )

    # Service layer
    from src.services.mcp_service import (
        TaskCreateInput,
        TaskUpdateInput,
        TaskListInput,
        TaskIdInput,
        MCPError,
        MCPToolBase,
        create_mcp_tools_manifest
    )

    # Models (should already exist)
    from src.models.chat import Conversation, Message
    from src.models.task import Task

    # Security (should already exist)
    from src.core.security import verify_token, extract_user_id

    # Config (should be updated)
    from src.core.config import get_settings

    settings = get_settings()
    assert hasattr(settings, 'mcp_host')
    assert hasattr(settings, 'mcp_port')
    assert hasattr(settings, 'mcp_debug')


def test_pydantic_validation_task_create():
    """Test TaskCreateInput validation and normalization."""
    from src.services.mcp_service import TaskCreateInput

    # Valid input
    input_data = TaskCreateInput(
        title="Test Task",
        description="Test description",
        priority="high",
        category="Work",
        due_date="2026-03-01"
    )

    assert input_data.title == "Test Task"
    assert input_data.priority == "high"
    assert input_data.due_date == "2026-03-01"

    # Priority normalization (uppercase to lowercase)
    input_data = TaskCreateInput(title="Test", priority="HIGH")
    assert input_data.priority == "high"

    # Invalid priority defaults to medium
    input_data = TaskCreateInput(title="Test", priority="invalid")
    assert input_data.priority == "medium"

    # Missing priority defaults to medium
    input_data = TaskCreateInput(title="Test")
    assert input_data.priority == "medium"


def test_pydantic_validation_task_create_invalid_date():
    """Test TaskCreateInput rejects invalid date formats."""
    from src.services.mcp_service import TaskCreateInput
    from pydantic import ValidationError

    # Invalid date format should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        TaskCreateInput(title="Test", due_date="invalid-date")

    assert "due_date" in str(exc_info.value)


def test_pydantic_validation_task_update():
    """Test TaskUpdateInput validation."""
    from src.services.mcp_service import TaskUpdateInput

    # All fields optional
    input_data = TaskUpdateInput()
    assert input_data.title is None
    assert input_data.priority is None

    # Partial update
    input_data = TaskUpdateInput(title="Updated Title", priority="low")
    assert input_data.title == "Updated Title"
    assert input_data.priority == "low"

    # Priority normalization
    input_data = TaskUpdateInput(priority="MEDIUM")
    assert input_data.priority == "medium"


def test_pydantic_validation_task_update_invalid_priority():
    """Test TaskUpdateInput rejects invalid priority."""
    from src.services.mcp_service import TaskUpdateInput
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        TaskUpdateInput(priority="invalid")

    assert "priority" in str(exc_info.value)


def test_pydantic_validation_task_list():
    """Test TaskListInput validation and defaults."""
    from src.services.mcp_service import TaskListInput

    # Default values
    input_data = TaskListInput()
    assert input_data.status == "all"
    assert input_data.priority is None
    assert input_data.category is None

    # Valid filters
    input_data = TaskListInput(status="pending", priority="high", category="Work")
    assert input_data.status == "pending"
    assert input_data.priority == "high"
    assert input_data.category == "Work"

    # Status normalization
    input_data = TaskListInput(status="COMPLETED")
    assert input_data.status == "completed"

    # Invalid status defaults to "all"
    input_data = TaskListInput(status="invalid")
    assert input_data.status == "all"


def test_pydantic_validation_task_id():
    """Test TaskIdInput validation."""
    from src.services.mcp_service import TaskIdInput
    from pydantic import ValidationError

    # Valid task_id
    input_data = TaskIdInput(task_id=42)
    assert input_data.task_id == 42

    # Invalid task_id (must be > 0)
    with pytest.raises(ValidationError):
        TaskIdInput(task_id=0)

    with pytest.raises(ValidationError):
        TaskIdInput(task_id=-1)


def test_mcp_error_structure():
    """Test MCPError exception and to_dict() method."""
    from src.services.mcp_service import MCPError

    error = MCPError(
        code="NOT_FOUND",
        message="Task not found",
        details={"task_id": 123}
    )

    assert error.code == "NOT_FOUND"
    assert error.message == "Task not found"
    assert error.details == {"task_id": 123}

    # Convert to dict
    error_dict = error.to_dict()
    assert error_dict == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Task not found",
            "details": {"task_id": 123}
        }
    }

    # Error without details
    error = MCPError(code="VALIDATION_ERROR", message="Invalid input")
    error_dict = error.to_dict()
    assert "details" not in error_dict["error"] or error_dict["error"]["details"] == {}


def test_mcp_auth_error_structure():
    """Test MCPAuthError exception."""
    from src.middleware.mcp_auth import MCPAuthError

    error = MCPAuthError("Invalid token", code=401)
    assert error.message == "Invalid token"
    assert error.code == 401
    assert str(error) == "Invalid token"


def test_mcp_tools_manifest():
    """Test MCP tools manifest generation."""
    from src.services.mcp_service import create_mcp_tools_manifest

    manifest = create_mcp_tools_manifest()

    assert "tools" in manifest
    assert len(manifest["tools"]) == 6  # 6 tools defined

    # Verify tool names
    tool_names = [tool["name"] for tool in manifest["tools"]]
    expected_tools = [
        "add_task",
        "list_tasks",
        "complete_task",
        "uncomplete_task",
        "delete_task",
        "update_task"
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Tool '{expected_tool}' missing from manifest"

    # Verify add_task schema
    add_task_tool = next(t for t in manifest["tools"] if t["name"] == "add_task")
    assert "input_schema" in add_task_tool
    assert "properties" in add_task_tool["input_schema"]
    assert "title" in add_task_tool["input_schema"]["properties"]
    assert "required" in add_task_tool["input_schema"]
    assert "title" in add_task_tool["input_schema"]["required"]


def test_validate_mcp_token_missing_token():
    """Test validate_mcp_token with missing token."""
    from src.middleware.mcp_auth import validate_mcp_token, MCPAuthError

    # Empty token
    with pytest.raises(MCPAuthError) as exc_info:
        validate_mcp_token("")

    assert exc_info.value.code == 401
    assert "required" in exc_info.value.message.lower()

    # None token
    with pytest.raises(MCPAuthError):
        validate_mcp_token(None)


def test_validate_mcp_token_bearer_prefix_handling():
    """Test validate_mcp_token strips Bearer prefix."""
    from src.middleware.mcp_auth import validate_mcp_token, MCPAuthError

    # "Bearer " with empty token should fail
    with pytest.raises(MCPAuthError) as exc_info:
        validate_mcp_token("Bearer ")

    assert exc_info.value.code == 401


def test_mcp_tool_base_format_success_response():
    """Test MCPToolBase success response formatting."""
    from src.services.mcp_service import MCPToolBase
    from unittest.mock import MagicMock

    # Create instance with mocked session
    tool = MCPToolBase(session=MagicMock())

    # Format success response
    response = tool._format_success_response(
        data={"task_id": 123, "title": "Test Task"},
        message="Task created successfully"
    )

    assert response["success"] is True
    assert response["data"] == {"task_id": 123, "title": "Test Task"}
    assert response["message"] == "Task created successfully"

    # Without message
    response = tool._format_success_response(data=[1, 2, 3])
    assert response["success"] is True
    assert response["data"] == [1, 2, 3]
    assert "message" not in response


def test_mcp_tool_base_format_error_response():
    """Test MCPToolBase error response formatting."""
    from src.services.mcp_service import MCPToolBase, MCPError
    from src.middleware.mcp_auth import MCPAuthError
    from unittest.mock import MagicMock

    tool = MCPToolBase(session=MagicMock())

    # MCPError
    error = MCPError(code="NOT_FOUND", message="Task not found", details={"task_id": 123})
    response = tool._format_error_response(error)
    assert response["error"]["code"] == "NOT_FOUND"
    assert response["error"]["message"] == "Task not found"
    assert response["error"]["details"] == {"task_id": 123}

    # MCPAuthError
    error = MCPAuthError("Invalid token", code=401)
    response = tool._format_error_response(error)
    assert response["error"]["code"] == "UNAUTHORIZED"
    assert response["error"]["message"] == "Invalid token"

    # Generic exception
    error = ValueError("Something went wrong")
    response = tool._format_error_response(error)
    assert response["error"]["code"] == "INTERNAL_ERROR"
    assert "unexpected error" in response["error"]["message"].lower()


def test_mcp_tool_base_validate_user_context():
    """Test MCPToolBase user context validation."""
    from src.services.mcp_service import MCPToolBase, MCPError
    from unittest.mock import MagicMock

    tool = MCPToolBase(session=MagicMock())

    # Valid context
    context = {"user_id": "user_123"}
    user_id = tool._validate_user_context(context)
    assert user_id == "user_123"

    # Missing user_id
    context = {"some_other_key": "value"}
    with pytest.raises(MCPError) as exc_info:
        tool._validate_user_context(context)

    assert exc_info.value.code == "UNAUTHORIZED"
    assert "authentication required" in exc_info.value.message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
