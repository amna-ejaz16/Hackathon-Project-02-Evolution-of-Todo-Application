#!/usr/bin/env python3
"""
Test script for chatbot deletion flow.

This script tests:
1. Task creation
2. Deletion intent recognition (agent asks for confirmation)
3. Confirmation handling (agent calls delete_task tool)
4. Task deletion verification
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from src.main import create_app
from src.models.task import Task
from src.models.chat import Conversation, Message
from sqlmodel import Session, create_engine, SQLModel
from src.services.chat_service import ChatService


async def test_deletion_flow():
    """Test the complete deletion flow."""

    print("=" * 80)
    print("CHATBOT DELETION FLOW TEST")
    print("=" * 80)

    # Initialize app
    print("\n[SETUP] Initializing application...")
    app = create_app()
    print("✓ App initialized")

    # Create test user
    test_user_id = "test_user_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"✓ Test user ID: {test_user_id}")

    # Get database session
    from src.core.database import get_session
    session = next(get_session())

    try:
        print("\n" + "=" * 80)
        print("STEP 1: CREATE A TASK")
        print("=" * 80)

        # Create a test task
        task = Task(
            user_id=test_user_id,
            title="make coffee",
            description="Make a cup of coffee",
            priority="medium",
            category="Daily",
            completed=False
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        print(f"\n✓ Task created:")
        print(f"  - ID: {task.id}")
        print(f"  - Title: {task.title}")
        print(f"  - User: {test_user_id}")

        # Verify task exists
        from sqlmodel import select
        verify_task = session.exec(
            select(Task).where(Task.id == task.id, Task.user_id == test_user_id)
        ).first()
        assert verify_task is not None, "Task creation verification failed"
        print(f"✓ Task verified in database")

        print("\n" + "=" * 80)
        print("STEP 2: TEST DELETION INTENT RECOGNITION")
        print("=" * 80)

        user_message_1 = "delete a task to make coffee"
        print(f"\nUser message: '{user_message_1}'")

        # Process first message (should ask for confirmation)
        response_1 = await ChatService.process_message(
            user_message=user_message_1,
            user_id=test_user_id,
            session=session
        )

        print(f"\nAgent response (Turn 1):")
        print(f"  {response_1.response}")
        print(f"\nAction detected: {response_1.action}")
        print(f"Conversation ID: {response_1.conversation_id}")

        # Verify agent asked for confirmation
        assert "sure" in response_1.response.lower() or "confirm" in response_1.response.lower(), \
            f"Agent should ask for confirmation, but said: {response_1.response}"
        assert f"(ID: {task.id})" in response_1.response or f"ID: {task.id}" in response_1.response, \
            f"Agent should mention task ID in confirmation. Response: {response_1.response}"
        assert response_1.action == "conversation", \
            f"Action should be 'conversation' on confirmation turn, got: {response_1.action}"
        print("\n✓ Agent correctly asked for confirmation with task ID")

        print("\n" + "=" * 80)
        print("STEP 3: TEST CONFIRMATION HANDLING")
        print("=" * 80)

        user_message_2 = "yes"
        print(f"\nUser message: '{user_message_2}'")

        # Process second message (should delete the task)
        response_2 = await ChatService.process_message(
            user_message=user_message_2,
            user_id=test_user_id,
            session=session
        )

        print(f"\nAgent response (Turn 2):")
        print(f"  {response_2.response}")
        print(f"\nAction detected: {response_2.action}")

        # Verify agent called delete_task
        assert response_2.action == "task_deleted", \
            f"Action should be 'task_deleted', got: {response_2.action}"
        print("\n✓ Agent recognized confirmation and triggered deletion")

        # Verify deletion confirmation in response
        assert "delet" in response_2.response.lower(), \
            f"Agent should confirm deletion in response. Got: {response_2.response}"
        print(f"✓ Agent confirmed deletion in response")

        print("\n" + "=" * 80)
        print("STEP 4: VERIFY TASK DELETION")
        print("=" * 80)

        # Check if task is actually deleted
        deleted_task = session.exec(
            select(Task).where(Task.id == task.id, Task.user_id == test_user_id)
        ).first()

        if deleted_task is None:
            print(f"\n✓ Task {task.id} successfully deleted from database")
        else:
            print(f"\n✗ FAILED: Task {task.id} still exists in database!")
            print(f"  Task: {deleted_task.title}")
            return False

        print("\n" + "=" * 80)
        print("STEP 5: TEST CANCELLATION FLOW")
        print("=" * 80)

        # Create another task for cancellation test
        task_2 = Task(
            user_id=test_user_id,
            title="drink tea",
            description="Make a cup of tea",
            priority="low",
            category="Daily",
            completed=False
        )
        session.add(task_2)
        session.commit()
        session.refresh(task_2)
        print(f"\n✓ Created second task: {task_2.title} (ID: {task_2.id})")

        # Trigger deletion
        response_cancel_1 = await ChatService.process_message(
            user_message="delete drink tea",
            user_id=test_user_id,
            session=session
        )

        print(f"\nAgent asks for confirmation: {response_cancel_1.response[:80]}...")

        # User cancels
        response_cancel_2 = await ChatService.process_message(
            user_message="no",
            user_id=test_user_id,
            session=session
        )

        print(f"User cancels with 'no'")
        print(f"Agent response: {response_cancel_2.response}")

        # Verify task still exists
        cancel_task = session.exec(
            select(Task).where(Task.id == task_2.id, Task.user_id == test_user_id)
        ).first()

        assert cancel_task is not None, "Task should NOT be deleted when user says no"
        assert response_cancel_2.action != "task_deleted", "Action should NOT be task_deleted"
        print(f"\n✓ Task correctly preserved when user cancelled deletion")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nDeletion Flow Summary:")
        print("  1. ✓ Task creation works")
        print("  2. ✓ Agent recognizes delete intent")
        print("  3. ✓ Agent asks for confirmation with task ID")
        print("  4. ✓ Agent processes confirmation and calls delete_task")
        print("  5. ✓ Task is successfully deleted from database")
        print("  6. ✓ Agent confirms deletion to user")
        print("  7. ✓ Cancellation flow preserves task")

        return True

    except AssertionError as e:
        print(f"\n✗ ASSERTION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("Starting deletion flow test...\n")

    try:
        success = asyncio.run(test_deletion_flow())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
