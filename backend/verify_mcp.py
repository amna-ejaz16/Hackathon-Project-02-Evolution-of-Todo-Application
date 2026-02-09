#!/usr/bin/env python3
"""
MCP Implementation Verification Script

Verifies that all MCP components are correctly installed and configured.
Run this script to validate the MCP server implementation.

Usage:
    python verify_mcp.py
"""

import sys


def check_imports():
    """Verify all required modules can be imported."""
    print("=" * 60)
    print("1. Checking Module Imports...")
    print("=" * 60)

    modules = [
        ("FastAPI", "fastapi"),
        ("SQLModel", "sqlmodel"),
        ("Pydantic", "pydantic"),
        ("JWT", "jwt"),
    ]

    all_good = True
    for name, module in modules:
        try:
            __import__(module)
            print(f"  ✓ {name:15} imported successfully")
        except ImportError as e:
            print(f"  ✗ {name:15} FAILED: {e}")
            all_good = False

    return all_good


def check_mcp_service():
    """Verify MCP service module loads correctly."""
    print("\n" + "=" * 60)
    print("2. Checking MCP Service Layer...")
    print("=" * 60)

    try:
        from src.services.mcp_service import (
            MCPTaskTools,
            MCPError,
            TaskCreateInput,
            TaskListInput,
            TaskUpdateInput,
            TaskIdInput,
            create_mcp_tools_manifest,
        )
        print("  ✓ MCPTaskTools class imported")
        print("  ✓ MCPError exception imported")
        print("  ✓ Pydantic validation models imported")
        print("  ✓ create_mcp_tools_manifest function imported")

        # Verify tool manifest
        manifest = create_mcp_tools_manifest()
        tools = manifest.get("tools", [])
        print(f"  ✓ Tool manifest contains {len(tools)} tools")

        tool_names = [t["name"] for t in tools]
        expected_tools = ["add_task", "list_tasks", "complete_task", "delete_task", "update_task"]

        for tool in expected_tools:
            if tool in tool_names:
                print(f"  ✓ Tool '{tool}' is registered")
            else:
                print(f"  ✗ Tool '{tool}' is MISSING")
                return False

        return True

    except Exception as e:
        print(f"  ✗ FAILED to load MCP service: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_mcp_api():
    """Verify MCP API module loads correctly."""
    print("\n" + "=" * 60)
    print("3. Checking MCP API Layer...")
    print("=" * 60)

    try:
        from src.api.mcp import router
        print("  ✓ MCP router imported")

        # Check routes
        routes = [route for route in router.routes if hasattr(route, "path")]
        print(f"  ✓ MCP router has {len(routes)} endpoints")

        expected_paths = [
            "/tools/list",
            "/tools/add_task",
            "/tools/list_tasks",
            "/tools/complete_task",
            "/tools/delete_task",
            "/tools/update_task",
        ]

        for path in expected_paths:
            route = next((r for r in routes if r.path == path), None)
            if route:
                methods = list(route.methods) if hasattr(route, "methods") else ["?"]
                print(f"  ✓ Endpoint {methods[0]:6} {path}")
            else:
                print(f"  ✗ Endpoint {path} is MISSING")
                return False

        return True

    except Exception as e:
        print(f"  ✗ FAILED to load MCP API: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_main_app():
    """Verify MCP router is registered in main app."""
    print("\n" + "=" * 60)
    print("4. Checking Main App Integration...")
    print("=" * 60)

    try:
        from src.main import create_app
        print("  ✓ Main app imported")

        app = create_app()
        print("  ✓ App created successfully")

        # Check MCP routes are registered
        mcp_routes = [r for r in app.routes if hasattr(r, "path") and "/mcp" in r.path]
        print(f"  ✓ Found {len(mcp_routes)} MCP routes in main app")

        if len(mcp_routes) != 6:
            print(f"  ✗ Expected 6 MCP routes, found {len(mcp_routes)}")
            return False

        for route in mcp_routes:
            if hasattr(route, "methods"):
                method = list(route.methods)[0]
                print(f"  ✓ Route registered: {method:6} {route.path}")

        return True

    except Exception as e:
        print(f"  ✗ FAILED to load main app: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_middleware():
    """Verify MCP authentication middleware loads correctly."""
    print("\n" + "=" * 60)
    print("5. Checking Authentication Middleware...")
    print("=" * 60)

    try:
        from src.middleware.mcp_auth import (
            validate_mcp_token,
            require_mcp_auth,
            MCPAuthError,
        )
        print("  ✓ validate_mcp_token function imported")
        print("  ✓ require_mcp_auth decorator imported")
        print("  ✓ MCPAuthError exception imported")
        return True

    except Exception as e:
        print(f"  ✗ FAILED to load middleware: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_models():
    """Verify task models are available."""
    print("\n" + "=" * 60)
    print("6. Checking Data Models...")
    print("=" * 60)

    try:
        from src.models.task import Task, TaskCreate, TaskUpdate, TaskRead
        print("  ✓ Task model imported")
        print("  ✓ TaskCreate schema imported")
        print("  ✓ TaskUpdate schema imported")
        print("  ✓ TaskRead schema imported")
        return True

    except Exception as e:
        print(f"  ✗ FAILED to load models: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print verification summary."""
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    checks = [
        ("Module Imports", results["imports"]),
        ("MCP Service Layer", results["service"]),
        ("MCP API Layer", results["api"]),
        ("Main App Integration", results["main"]),
        ("Auth Middleware", results["middleware"]),
        ("Data Models", results["models"]),
    ]

    all_passed = True
    for name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:8} {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - MCP Implementation Ready!")
        print("\nNext Steps:")
        print("  1. Start the server: uvicorn src.main:app --reload")
        print("  2. Test tool discovery: curl http://localhost:8001/api/mcp/tools/list")
        print("  3. View API docs: http://localhost:8001/docs")
    else:
        print("❌ SOME CHECKS FAILED - Review errors above")
        print("\nTroubleshooting:")
        print("  1. Ensure all dependencies installed: pip install -r requirements.txt")
        print("  2. Check Python version: python --version (need 3.11+)")
        print("  3. Verify working directory is backend/")

    print("=" * 60)

    return all_passed


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("MCP IMPLEMENTATION VERIFICATION")
    print("=" * 60)
    print("This script verifies that all MCP components are correctly installed.\n")

    results = {
        "imports": check_imports(),
        "service": check_mcp_service(),
        "api": check_mcp_api(),
        "main": check_main_app(),
        "middleware": check_middleware(),
        "models": check_models(),
    }

    all_passed = print_summary(results)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
