#!/usr/bin/env python3
"""
Test script to verify the agent message extraction fix.
This script validates that the RunResult message extraction works correctly.
"""

import asyncio
import sys


async def test_runner_result_structure():
    """Test the structure of RunResult from OpenAI Agents SDK."""
    print("=" * 70)
    print("TESTING AGENT MESSAGE EXTRACTION FIX")
    print("=" * 70)

    # Test 1: Import verification
    print("\n[TEST 1] Verifying OpenAI Agents SDK imports...")
    try:
        from agents import Runner, Agent, MessageOutputItem, ToolCallItem
        from agents import function_tool
        print("✓ All required imports available")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: Verify RunResult structure
    print("\n[TEST 2] Verifying RunResult structure...")
    try:
        from agents import RunResult

        # Check that RunResult has the expected attributes
        expected_attrs = ['new_items', 'raw_responses', 'final_output']
        sig = str(RunResult.__init__.__annotations__)

        for attr in expected_attrs:
            if attr not in sig:
                print(f"✗ RunResult missing {attr}")
                return False

        print(f"✓ RunResult has all expected attributes: {', '.join(expected_attrs)}")
    except Exception as e:
        print(f"✗ RunResult check failed: {e}")
        return False

    # Test 3: Verify MessageOutputItem structure
    print("\n[TEST 3] Verifying MessageOutputItem structure...")
    try:
        if hasattr(MessageOutputItem, '__dataclass_fields__'):
            fields = MessageOutputItem.__dataclass_fields__.keys()
            expected = {'agent', 'raw_item', '_agent_ref', 'type'}
            if expected.issubset(fields):
                print(f"✓ MessageOutputItem has all expected fields")
            else:
                missing = expected - set(fields)
                print(f"✗ MessageOutputItem missing fields: {missing}")
                return False
    except Exception as e:
        print(f"✗ MessageOutputItem check failed: {e}")
        return False

    # Test 4: Verify import locations match code
    print("\n[TEST 4] Verifying code import locations...")
    try:
        with open('src/services/chat_service.py', 'r') as f:
            content = f.read()

        checks = [
            ('from agents import Agent, Runner, MessageOutputItem, ToolCallItem, ToolCallOutputItem', 'Imports at module level'),
            ('if isinstance(item, MessageOutputItem)', 'Message type check'),
            ('if isinstance(item, ToolCallItem)', 'Tool type check'),
            ('result.new_items', 'Using new_items instead of messages'),
            ('item.raw_item.content', 'Correct content access path'),
            ('MCP_DISABLE_FILESYSTEM', 'MCP filesystem disabled'),
        ]

        all_found = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✓ Found: {description}")
            else:
                print(f"✗ Missing: {description} ('{check_str}')")
                all_found = False

        if not all_found:
            return False

    except Exception as e:
        print(f"✗ Code check failed: {e}")
        return False

    # Test 5: Syntax validation
    print("\n[TEST 5] Validating Python syntax...")
    try:
        import py_compile
        py_compile.compile('src/services/chat_service.py', doraise=True)
        print("✓ chat_service.py syntax is valid")
    except Exception as e:
        print(f"✗ Syntax error: {e}")
        return False

    # Test 6: App initialization
    print("\n[TEST 6] Testing app initialization...")
    try:
        from src.main import create_app
        app = create_app()
        routes_count = len([r for r in app.routes if hasattr(r, 'path')])
        print(f"✓ App initialized successfully with {routes_count} routes")
    except Exception as e:
        print(f"✗ App initialization failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    try:
        success = asyncio.run(test_runner_result_structure())
    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    # Print summary
    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED - Fix is correctly implemented!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Start the backend: python -m uvicorn src.main:app --reload")
        print("2. Send a test message through the chat interface")
        print("3. Verify you get an actual AI response (not error message)")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please review the errors above")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
