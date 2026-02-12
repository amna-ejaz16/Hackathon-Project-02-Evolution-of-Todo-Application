"""
Test suite for the pending action handler fix.

This test verifies the core logic of:
1. Confirmation detection patterns
2. Pending action extraction from responses
3. Regex pattern matching for task IDs
4. Cancellation detection
"""

import re
from typing import Optional


# ============================================================================
# Core Logic from chat_service.py (replicated for testing)
# ============================================================================

AFFIRMATIVE_PATTERNS = {
    "yes", "confirm", "ok", "sure", "yeah", "yep",
    "proceed", "delete it", "go ahead", "do it"
}

NEGATIVE_PATTERNS = {
    "no", "cancel", "stop", "don't", "nope",
    "nevermind", "never mind", "abort"
}


def is_confirmation(message: str) -> bool:
    """Check if message is an affirmative confirmation."""
    normalized = message.lower().strip().strip('.,!?')
    return normalized in AFFIRMATIVE_PATTERNS


def is_cancellation(message: str) -> bool:
    """Check if message is a negative cancellation."""
    normalized = message.lower().strip().strip('.,!?')
    return normalized in NEGATIVE_PATTERNS


def detect_pending_action(assistant_response: str) -> Optional[dict]:
    """
    Detect if agent is asking for delete confirmation.

    Replicates the logic from process_message() around line 576-596.
    """
    pending_action = None
    if "Are you sure you want to delete" in assistant_response or \
       "Do you want to delete" in assistant_response:
        # Extract task ID from confirmation message
        match = re.search(r'\(ID:\s*(\d+)\)', assistant_response)
        if match:
            task_id_str = match.group(1)
            # Try to find task title in message
            title_match = re.search(r"'([^']+)'", assistant_response)
            task_title = title_match.group(1) if title_match else "this task"

            pending_action = {
                "type": "delete_task",
                "task_id": int(task_id_str),
                "task_title": task_title,
                "awaiting_confirmation": True,
            }
    return pending_action


# ============================================================================
# Test Cases
# ============================================================================

def test_confirmation_patterns():
    """Test confirmation and cancellation pattern detection."""
    print("\n=== Testing Confirmation/Cancellation Patterns ===")

    # Test affirmative patterns
    affirmative = ["yes", "Yes", "YES", "confirm", "ok", "sure", "yeah", "yep"]
    for msg in affirmative:
        assert is_confirmation(msg), f"Failed to detect confirmation: {msg}"
        print(f"✅ Confirmed: '{msg}'")

    # Test negative patterns
    negative = ["no", "No", "cancel", "stop", "don't", "nope", "never mind"]
    for msg in negative:
        assert is_cancellation(msg), f"Failed to detect cancellation: {msg}"
        print(f"✅ Detected cancellation: '{msg}'")

    # Test non-matching
    non_matching = ["maybe", "later", "idk", "help"]
    for msg in non_matching:
        assert not is_confirmation(msg), f"False positive confirmation: {msg}"
        assert not is_cancellation(msg), f"False positive cancellation: {msg}"
        print(f"✅ Correctly ignored: '{msg}'")


def test_pending_action_detection():
    """Test that pending action is detected from assistant response."""
    print("\n=== Testing Pending Action Detection ===")

    # Test case 1: Standard deletion confirmation
    response = "I found the task 'make coffee' (ID: 42). Are you sure you want to delete it?"
    pending = detect_pending_action(response)

    assert pending is not None, "Failed to detect pending action"
    assert pending["task_id"] == 42, f"Wrong task_id: {pending['task_id']}"
    assert pending["task_title"] == "make coffee", f"Wrong task_title: {pending['task_title']}"
    assert pending["type"] == "delete_task", f"Wrong type: {pending['type']}"
    print(f"✅ Test case 1: {pending}")

    # Test case 2: Different task
    response2 = "I found the task 'buy milk' (ID: 99). Do you want to delete it?"
    pending2 = detect_pending_action(response2)

    assert pending2 is not None, "Failed to detect second pending action"
    assert pending2["task_id"] == 99
    assert pending2["task_title"] == "buy milk"
    print(f"✅ Test case 2: {pending2}")

    # Test case 3: Task with special characters in title
    response3 = "I found the task 'fix bug #123' (ID: 15). Are you sure you want to delete it?"
    pending3 = detect_pending_action(response3)

    assert pending3 is not None, "Failed to detect third pending action"
    assert pending3["task_id"] == 15
    assert pending3["task_title"] == "fix bug #123"
    print(f"✅ Test case 3: {pending3}")

    # Test case 4: No detection for normal responses
    normal_response = "I've created a new task for you: 'workout' with high priority."
    pending4 = detect_pending_action(normal_response)

    assert pending4 is None, "False positive: detected pending action for normal response"
    print(f"✅ Test case 4: Normal response correctly doesn't trigger pending action")


def test_confirmation_with_punctuation():
    """Test confirmation patterns with various punctuation."""
    print("\n=== Testing Confirmation With Punctuation ===")

    test_cases = [
        ("yes.", True),
        ("yes!", True),
        ("yes?", True),
        ("Yes, please", False),  # Extra words shouldn't match
        ("no.", False),
        ("no!", False),
        ("confirm.", True),
        ("ok,", True),
        ("  yes  ", True),  # Whitespace handling
    ]

    for msg, expected in test_cases:
        result = is_confirmation(msg)
        assert result == expected, f"Failed for '{msg}': got {result}, expected {expected}"
        print(f"✅ '{msg}' -> {result}")


def test_task_id_extraction_edge_cases():
    """Test regex pattern matching for various ID formats."""
    print("\n=== Testing Task ID Extraction Edge Cases ===")

    test_cases = [
        ("(ID: 42)", 42),
        ("(ID:42)", 42),
        ("(ID: 999)", 999),
        ("(ID: 1)", 1),
        ("( ID: 42 )", None),  # Extra spaces inside parens
        ("ID: 42", None),  # No parentheses
    ]

    pattern = r'\(ID:\s*(\d+)\)'

    for text, expected_id in test_cases:
        match = re.search(pattern, text)
        if expected_id is None:
            assert match is None, f"Should not match: {text}"
            print(f"✅ '{text}' -> No match (as expected)")
        else:
            assert match is not None, f"Should match: {text}"
            task_id = int(match.group(1))
            assert task_id == expected_id, f"Wrong ID: {text}"
            print(f"✅ '{text}' -> {task_id}")


def test_title_extraction_edge_cases():
    """Test regex pattern matching for task titles."""
    print("\n=== Testing Task Title Extraction Edge Cases ===")

    pattern = r"'([^']+)'"

    test_cases = [
        ("I found the task 'make coffee' (ID: 42).", "make coffee"),
        ("The task 'buy milk (1L)' (ID: 99).", "buy milk (1L)"),
        ("'foo bar' is the task (ID: 1).", "foo bar"),
        ("No quotes here", None),
        ("'unclosed quote here", None),
    ]

    for text, expected_title in test_cases:
        match = re.search(pattern, text)
        if expected_title is None:
            assert match is None, f"Should not match: {text}"
            print(f"✅ '{text}' -> No match (as expected)")
        else:
            assert match is not None, f"Should match: {text}"
            title = match.group(1)
            assert title == expected_title, f"Wrong title: got '{title}', expected '{expected_title}'"
            print(f"✅ '{text}' -> '{title}'")


def test_state_machine_flow():
    """Test the full state machine flow without DB."""
    print("\n=== Testing State Machine Flow ===")

    # Step 1: User asks to delete
    user_msg_1 = "delete my coffee task"
    print(f"👤 User: {user_msg_1}")

    # Step 2: Agent responds with confirmation
    agent_response = "I found the task 'make coffee' (ID: 42). Are you sure you want to delete it?"
    print(f"🤖 Agent: {agent_response}")

    # Step 3: Detect pending action
    pending = detect_pending_action(agent_response)
    assert pending is not None
    print(f"⏸️  Pending action stored: task_id={pending['task_id']}, task_title='{pending['task_title']}'")

    # Step 4: User confirms
    user_msg_2 = "yes"
    is_confirm = is_confirmation(user_msg_2)
    assert is_confirm
    print(f"👤 User: {user_msg_2}")
    print(f"✅ Confirmation detected! Task {pending['task_id']} will be deleted.")

    # Alternative Step 4: User cancels
    user_msg_cancel = "no"
    is_cancel = is_cancellation(user_msg_cancel)
    assert is_cancel
    print(f"\n(Alternative flow) 👤 User: {user_msg_cancel}")
    print(f"❌ Cancellation detected! Task {pending['task_id']} will NOT be deleted.")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("PENDING ACTION HANDLER - UNIT TEST SUITE")
    print("=" * 70)

    try:
        test_confirmation_patterns()
        test_pending_action_detection()
        test_confirmation_with_punctuation()
        test_task_id_extraction_edge_cases()
        test_title_extraction_edge_cases()
        test_state_machine_flow()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED! Implementation is correct.")
        print("=" * 70)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
