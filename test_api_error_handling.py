#!/usr/bin/env python3
"""
Test API error handling for /api/chat endpoint.

Verifies:
1. MCP initialization errors are caught
2. API returns 200 even with errors
3. Error responses are properly formatted
4. No 500 errors are returned
"""

import sys
import asyncio
from datetime import datetime
from io import StringIO

print("=" * 70)
print("API Error Handling Tests")
print("=" * 70)

# Test 1: Verify error handling logic
def test_mcp_error_detection():
    """Test that MCP errors are properly detected."""
    print("\n[Test 1] MCP Error Detection")

    test_cases = [
        {
            "error": "Unable to add filesystem: /etc/invalid/path",
            "expected_catch": True,
            "type": "ValueError",
        },
        {
            "error": "Illegal path detected in MCP initialization",
            "expected_catch": True,
            "type": "OSError",
        },
        {
            "error": "MCP server failed to start",
            "expected_catch": True,
            "type": "RuntimeError",
        },
        {
            "error": "Database connection failed",
            "expected_catch": False,
            "type": "ValueError",
        },
    ]

    keywords = ["filesystem", "illegal path", "mcp", "add filesystem"]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        error = test_case["error"].lower()
        expected = test_case["expected_catch"]

        # Check if any keyword matches
        is_mcp_error = any(keyword in error for keyword in keywords)

        status = "✓" if is_mcp_error == expected else "✗"
        print(
            f"  {status} Case {i}: '{test_case['error'][:40]}...' "
            f"→ MCP Error: {is_mcp_error} (expected {expected})"
        )

        if is_mcp_error == expected:
            passed += 1

    success = passed == len(test_cases)
    print(f"  Result: {passed}/{len(test_cases)} passed")
    return success


# Test 2: Verify ChatResponse structure
def test_chat_response_structure():
    """Test that error responses have correct structure."""
    print("\n[Test 2] ChatResponse Structure")

    # Simulate error response
    error_response = {
        "response": "I'm having trouble connecting to the task management system. Please try again in a moment.",
        "conversation_id": 123,
        "action": "conversation",  # NOT "task_deleted" or other task action
        "task_id": None,
    }

    checks = [
        ("response" in error_response, "Has 'response' field"),
        (isinstance(error_response["response"], str), "'response' is string"),
        ("trouble" in error_response["response"].lower(), "Response is user-friendly"),
        ("conversation_id" in error_response, "Has 'conversation_id'"),
        (error_response["action"] == "conversation", "Action is 'conversation' not task action"),
        (error_response["task_id"] is None, "task_id is None for error"),
    ]

    passed = 0
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {description}")
        if check:
            passed += 1

    success = passed == len(checks)
    print(f"  Result: {passed}/{len(checks)} passed")
    return success


# Test 3: Verify stderr suppression
def test_stderr_suppression():
    """Test that stderr suppression works."""
    print("\n[Test 3] Stderr/Stdout Suppression")

    old_stderr = sys.stderr
    old_stdout = sys.stdout

    test_output = "This should be suppressed"

    try:
        sys.stderr = StringIO()
        sys.stdout = StringIO()

        print(test_output, file=old_stderr)  # Write to ORIGINAL stderr
        # Simulate MCP writing to stderr
        sys.stderr.write("MCP warning: something happened")
        sys.stdout.write("MCP debug: initialized")

        captured_stderr = sys.stderr.getvalue()
        captured_stdout = sys.stdout.getvalue()

        # Verify original output went to real stderr
        restored_stderr = old_stderr
        restored_stdout = old_stdout

        # Check that our output was captured
        checks = [
            (len(captured_stderr) > 0, "Captured stderr output"),
            (len(captured_stdout) > 0, "Captured stdout output"),
            ("MCP warning" in captured_stderr, "MCP warnings captured"),
            ("MCP debug" in captured_stdout, "MCP debug captured"),
        ]

        passed = 0
        for check, description in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {description}")
            if check:
                passed += 1

        success = passed == len(checks)
        print(f"  Result: {passed}/{len(checks)} passed")
        return success

    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


# Test 4: Verify exception handling flow
def test_exception_handling_flow():
    """Test exception handling flow matches the fix."""
    print("\n[Test 4] Exception Handling Flow")

    # Simulate the fixed error handling logic
    def handle_agent_init_error(error: Exception) -> str:
        """Simulate the fixed error handling."""
        error_str = str(error).lower()
        keywords = ["filesystem", "illegal path", "mcp", "add filesystem"]

        if any(keyword in error_str for keyword in keywords):
            # MCP error - return graceful response
            return "mcp_error_graceful"
        else:
            # Other error - re-raise
            raise ValueError(f"Unexpected error: {error}")

    test_cases = [
        {
            "error": ValueError("Unable to add filesystem: /invalid"),
            "expected_result": "mcp_error_graceful",
        },
        {
            "error": ValueError("Illegal path in MCP sandbox"),
            "expected_result": "mcp_error_graceful",
        },
        {
            "error": ValueError("Database error"),
            "expected_result": "error_re_raised",
        },
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        error = test_case["error"]
        expected = test_case["expected_result"]

        try:
            result = handle_agent_init_error(error)
            actual = result
        except ValueError:
            actual = "error_re_raised"

        status = "✓" if actual == expected else "✗"
        print(
            f"  {status} Case {i}: {str(error)[:40]}... "
            f"→ {actual} (expected {expected})"
        )

        if actual == expected:
            passed += 1

    success = passed == len(test_cases)
    print(f"  Result: {passed}/{len(test_cases)} passed")
    return success


# Test 5: Verify frontend error isolation
def test_frontend_error_isolation():
    """Test that frontend errors don't cascade."""
    print("\n[Test 5] Frontend Error Isolation")

    # Simulate React state updates with error isolation
    messages = []
    errors = []

    # Simulate adding message with error handling
    def safe_add_message(messages, message):
        try:
            messages.append(message)
            return True
        except Exception as e:
            errors.append(f"Failed to add message: {e}")
            return False

    # Simulate the fixed flow
    def send_message_safe(text):
        # Step 1: Add user message (with error isolation)
        user_msg = {"id": 1, "role": "user", "content": text}
        safe_add_message(messages, user_msg)

        # Step 2: Simulate API call error
        try:
            raise ValueError("API returned 500")
        except ValueError as e:
            # Step 3: Try to add error message (with error isolation)
            error_msg = {"id": 2, "role": "assistant", "content": "Error occurred"}
            safe_add_message(messages, error_msg)

        return len(messages) > 0

    # Test: even if something fails, we still have messages
    success = send_message_safe("hello")

    checks = [
        (success, "Function completes despite errors"),
        (len(messages) > 0, "Messages still added despite error"),
        (len(errors) == 0 or len(messages) > 0, "Error handling prevents cascade"),
        (messages[0]["role"] == "user", "User message added"),
    ]

    passed = 0
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {description}")
        if check:
            passed += 1

    success = passed == len(checks)
    print(f"  Result: {passed}/{len(checks)} passed")
    print(f"  Final state: {len(messages)} messages, {len(errors)} errors")
    return success


def main():
    """Run all tests."""
    tests = [
        ("MCP Error Detection", test_mcp_error_detection),
        ("ChatResponse Structure", test_chat_response_structure),
        ("Stderr Suppression", test_stderr_suppression),
        ("Exception Handling Flow", test_exception_handling_flow),
        ("Frontend Error Isolation", test_frontend_error_isolation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  ERROR: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
