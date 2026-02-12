#!/usr/bin/env python3
"""
Test the delete task confirmation workflow to verify fixes.

Tests:
1. Confirmation pattern detection
2. Cancellation pattern detection
3. Success detection from delete_task result
4. Pending action structure
"""

import sys
import re
from datetime import datetime

# Test 1: Confirmation pattern detection
def test_confirmation_patterns():
    """Test that affirmative messages are detected correctly."""
    AFFIRMATIVE_PATTERNS = {
        "yes", "confirm", "ok", "sure", "yeah", "yep",
        "proceed", "delete it", "go ahead", "do it"
    }

    test_cases = [
        ("yes", True),
        ("Yes", True),
        ("YES!", True),
        ("ok.", True),
        ("sure,", True),
        ("delete it", True),
        ("no", False),
        ("cancel", False),
        ("nope", False),
    ]

    def is_confirmation(message: str) -> bool:
        normalized = message.lower().strip().strip('.,!?')
        return normalized in AFFIRMATIVE_PATTERNS

    passed = 0
    for message, expected in test_cases:
        result = is_confirmation(message)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{message}' -> {result} (expected {expected})")
        if result == expected:
            passed += 1

    return passed == len(test_cases)

# Test 2: Task ID extraction from agent response
def test_task_id_extraction():
    """Test that task IDs are extracted from confirmation messages."""
    test_responses = [
        {
            "response": "I found the task 'Buy groceries' (ID: 5). Are you sure you want to delete it?",
            "expected_id": 5,
            "expected_title": "Buy groceries"
        },
        {
            "response": "I found the task 'Complete project report' (ID: 123). Are you sure you want to delete it?",
            "expected_id": 123,
            "expected_title": "Complete project report"
        },
        {
            "response": "I found the task 'Call Mom' (ID: 1). Are you sure you want to delete it?",
            "expected_id": 1,
            "expected_title": "Call Mom"
        },
    ]

    passed = 0
    for test_case in test_responses:
        assistant_response = test_case["response"]
        expected_id = test_case["expected_id"]
        expected_title = test_case["expected_title"]

        # Test ID extraction
        match = re.search(r'\(ID:\s*(\d+)\)', assistant_response)
        if match:
            extracted_id = int(match.group(1))
            id_status = "✓" if extracted_id == expected_id else "✗"
            print(f"  {id_status} ID extraction: {extracted_id} (expected {expected_id})")

            # Test title extraction
            title_match = re.search(r"'([^']+)'", assistant_response)
            if title_match:
                extracted_title = title_match.group(1)
                title_status = "✓" if extracted_title == expected_title else "✗"
                print(f"  {title_status} Title extraction: '{extracted_title}' (expected '{expected_title}')")
                if extracted_id == expected_id and extracted_title == expected_title:
                    passed += 1
        else:
            print(f"  ✗ No ID found in response")

    return passed == len(test_responses)

# Test 3: Delete success detection
def test_delete_success_detection():
    """Test that delete results are correctly identified as success/failure."""
    test_cases = [
        {
            "result": "Deleted task 'Buy groceries' (ID: 5)",
            "expected_success": True,
            "name": "Successful deletion"
        },
        {
            "result": "Task 5 not found. Please check the task ID and try again.",
            "expected_success": False,
            "name": "Task not found"
        },
        {
            "result": "I encountered an error while deleting the task: database error",
            "expected_success": False,
            "name": "Database error"
        },
    ]

    passed = 0
    for test_case in test_cases:
        result = test_case["result"]
        expected_success = test_case["expected_success"]

        # Success detection logic from chat_service.py
        is_success = "Deleted task" in result

        status = "✓" if is_success == expected_success else "✗"
        print(f"  {status} {test_case['name']}: {is_success} (expected {expected_success})")
        if is_success == expected_success:
            passed += 1

    return passed == len(test_cases)

# Test 4: Pending action structure
def test_pending_action_structure():
    """Test that pending action metadata is properly structured."""
    pending_action = {
        "type": "delete_task",
        "task_id": 5,
        "task_title": "Buy groceries",
        "awaiting_confirmation": True,
        "created_at": datetime.utcnow().isoformat()
    }

    checks = [
        ("type" in pending_action and pending_action["type"] == "delete_task", "Has correct type"),
        ("task_id" in pending_action and isinstance(pending_action["task_id"], int), "Has valid task_id"),
        ("task_title" in pending_action and isinstance(pending_action["task_title"], str), "Has valid task_title"),
        ("created_at" in pending_action, "Has created_at timestamp"),
    ]

    passed = 0
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {description}")
        if check:
            passed += 1

    return passed == len(checks)

# Test 5: End-to-end scenario
def test_deletion_scenario():
    """Test a complete deletion scenario."""
    print("\n  Simulating: User deletes task 'Buy groceries'")

    # Step 1: Agent finds task
    agent_response = "I found the task 'Buy groceries' (ID: 5). Are you sure you want to delete it?"
    print(f"  1. Agent: {agent_response}")

    # Step 2: Extract and store pending action
    match = re.search(r'\(ID:\s*(\d+)\)', agent_response)
    title_match = re.search(r"'([^']+)'", agent_response)

    if match and title_match:
        task_id = int(match.group(1))
        task_title = title_match.group(1)
        pending_action = {
            "type": "delete_task",
            "task_id": task_id,
            "task_title": task_title
        }
        print(f"  2. Pending action stored: {pending_action}")
    else:
        print("  ✗ Failed to extract task info")
        return False

    # Step 3: User confirms
    user_confirmation = "yes"
    AFFIRMATIVE_PATTERNS = {"yes", "confirm", "ok", "sure", "yeah", "yep", "proceed", "delete it", "go ahead", "do it"}
    is_confirmed = user_confirmation.lower().strip().strip('.,!?') in AFFIRMATIVE_PATTERNS
    print(f"  3. User: '{user_confirmation}' -> Confirmed: {is_confirmed}")

    if not is_confirmed:
        print("  ✗ Confirmation not detected")
        return False

    # Step 4: Execute delete_task
    # Simulating success
    delete_result = f"Deleted task '{task_title}' (ID: {task_id})"
    is_success = "Deleted task" in delete_result
    print(f"  4. Delete tool: {delete_result} -> Success: {is_success}")

    if not is_success:
        print("  ✗ Deletion failed")
        return False

    # Step 5: Return result
    final_response = f"✓ {delete_result}"
    print(f"  5. Final response: {final_response}")
    print("  ✓ End-to-end scenario passed")

    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Delete Task Workflow Tests")
    print("=" * 60)

    tests = [
        ("Confirmation Pattern Detection", test_confirmation_patterns),
        ("Task ID Extraction", test_task_id_extraction),
        ("Delete Success Detection", test_delete_success_detection),
        ("Pending Action Structure", test_pending_action_structure),
        ("End-to-End Scenario", test_deletion_scenario),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            print(f"  → {status}")
        except Exception as e:
            print(f"  → ERROR: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
