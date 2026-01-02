"""Manual test script to verify main.py functionality."""
import sys
from io import StringIO
from services.task_manager import TaskManager
from cli.console_interface import ConsoleInterface


def test_task_creation():
    """Test creating tasks."""
    print("\n=== Test 1: Task Creation ===")
    tm = TaskManager()

    # Test adding a task
    task1 = tm.add_task("Buy groceries", "Milk, eggs, bread")
    assert task1.id == 1, "First task should have ID 1"
    assert task1.title == "Buy groceries", "Title should match"
    assert task1.description == "Milk, eggs, bread", "Description should match"
    assert task1.completed == False, "New task should not be completed"

    task2 = tm.add_task("Complete homework", "")
    assert task2.id == 2, "Second task should have ID 2"
    assert task2.description == "", "Empty description should work"

    print("✓ Task creation works correctly")


def test_task_retrieval():
    """Test retrieving tasks."""
    print("\n=== Test 2: Task Retrieval ===")
    tm = TaskManager()

    tm.add_task("Task 1", "Description 1")
    tm.add_task("Task 2", "Description 2")
    tm.add_task("Task 3", "Description 3")

    # Get all tasks
    all_tasks = tm.get_all_tasks()
    assert len(all_tasks) == 3, "Should have 3 tasks"

    # Get specific task
    task = tm.get_task(2)
    assert task is not None, "Task 2 should exist"
    assert task.title == "Task 2", "Should retrieve correct task"

    # Get non-existent task
    task = tm.get_task(999)
    assert task is None, "Non-existent task should return None"

    print("✓ Task retrieval works correctly")


def test_task_completion():
    """Test toggling task completion."""
    print("\n=== Test 3: Task Completion Toggle ===")
    tm = TaskManager()

    task = tm.add_task("Complete report", "Q4 report")
    assert task.completed == False, "New task should not be completed"

    # Toggle to completed
    result = tm.toggle_complete(1)
    assert result == True, "Toggle should succeed"
    task = tm.get_task(1)
    assert task.completed == True, "Task should be completed"

    # Toggle back to incomplete
    result = tm.toggle_complete(1)
    assert result == True, "Toggle should succeed"
    task = tm.get_task(1)
    assert task.completed == False, "Task should be incomplete"

    # Toggle non-existent task
    result = tm.toggle_complete(999)
    assert result == False, "Toggle non-existent task should fail"

    print("✓ Task completion toggle works correctly")


def test_task_update():
    """Test updating tasks."""
    print("\n=== Test 4: Task Update ===")
    tm = TaskManager()

    task = tm.add_task("Original Title", "Original Description")

    # Update title only
    result = tm.update_task(1, title="Updated Title")
    assert result == True, "Update should succeed"
    task = tm.get_task(1)
    assert task.title == "Updated Title", "Title should be updated"
    assert task.description == "Original Description", "Description should be unchanged"

    # Update description only
    result = tm.update_task(1, description="Updated Description")
    assert result == True, "Update should succeed"
    task = tm.get_task(1)
    assert task.title == "Updated Title", "Title should be unchanged"
    assert task.description == "Updated Description", "Description should be updated"

    # Update both
    result = tm.update_task(1, title="New Title", description="New Description")
    assert result == True, "Update should succeed"
    task = tm.get_task(1)
    assert task.title == "New Title", "Title should be updated"
    assert task.description == "New Description", "Description should be updated"

    # Update non-existent task
    result = tm.update_task(999, title="Test")
    assert result == False, "Update non-existent task should fail"

    # Test empty title validation
    try:
        tm.update_task(1, title="")
        assert False, "Empty title should raise ValueError"
    except ValueError:
        print("  ✓ Empty title validation works")

    print("✓ Task update works correctly")


def test_task_deletion():
    """Test deleting tasks."""
    print("\n=== Test 5: Task Deletion ===")
    tm = TaskManager()

    tm.add_task("Task 1", "Description 1")
    tm.add_task("Task 2", "Description 2")
    tm.add_task("Task 3", "Description 3")

    # Delete middle task
    result = tm.delete_task(2)
    assert result == True, "Delete should succeed"

    all_tasks = tm.get_all_tasks()
    assert len(all_tasks) == 2, "Should have 2 tasks remaining"

    task_ids = [task.id for task in all_tasks]
    assert 2 not in task_ids, "Task 2 should be deleted"
    assert 1 in task_ids and 3 in task_ids, "Tasks 1 and 3 should remain"

    # Delete non-existent task
    result = tm.delete_task(999)
    assert result == False, "Delete non-existent task should fail"

    print("✓ Task deletion works correctly")


def test_console_interface():
    """Test console interface display methods."""
    print("\n=== Test 6: Console Interface ===")
    tm = TaskManager()
    ci = ConsoleInterface(tm)

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    # Test menu display
    ci.display_menu()
    menu_output = sys.stdout.getvalue()
    assert "Todo Application" in menu_output, "Menu should show title"
    assert "1. View all tasks" in menu_output, "Menu should show all options"

    # Test empty task list display
    sys.stdout = StringIO()
    ci.display_tasks([])
    output = sys.stdout.getvalue()
    assert "empty" in output.lower(), "Should indicate empty list"

    # Test task list display
    task1 = tm.add_task("Task 1", "Description 1")
    task2 = tm.add_task("Task 2", "Description 2")
    task2.completed = True

    sys.stdout = StringIO()
    ci.display_tasks([task1, task2])
    output = sys.stdout.getvalue()
    assert "Task 1" in output, "Should show task 1"
    assert "Task 2" in output, "Should show task 2"
    assert "☐" in output, "Should show unchecked symbol"
    assert "☑" in output, "Should show checked symbol"

    # Test message display
    sys.stdout = StringIO()
    ci.display_message("Success!", "success")
    output = sys.stdout.getvalue()
    assert "Success!" in output, "Should show message"
    assert "✓" in output, "Should show success symbol"

    sys.stdout = StringIO()
    ci.display_message("Error occurred", "error")
    output = sys.stdout.getvalue()
    assert "Error occurred" in output, "Should show message"
    assert "✗" in output, "Should show error symbol"

    # Restore stdout
    sys.stdout = old_stdout

    print("✓ Console interface display methods work correctly")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Test 7: Edge Cases ===")
    tm = TaskManager()

    # Test empty title validation in add_task
    try:
        tm.add_task("", "Description")
        assert False, "Empty title should raise ValueError"
    except ValueError:
        print("  ✓ Empty title validation in add_task works")

    try:
        tm.add_task("   ", "Description")
        assert False, "Whitespace-only title should raise ValueError"
    except ValueError:
        print("  ✓ Whitespace-only title validation works")

    # Test title stripping
    task = tm.add_task("  Title with spaces  ", "  Description with spaces  ")
    assert task.title == "Title with spaces", "Title should be stripped"
    assert task.description == "Description with spaces", "Description should be stripped"
    print("  ✓ Title and description stripping works")

    # Test operations on empty task list
    empty_tm = TaskManager()
    assert empty_tm.get_all_tasks() == [], "Empty list should return empty array"
    assert empty_tm.get_task(1) is None, "Get task on empty list should return None"
    assert empty_tm.toggle_complete(1) == False, "Toggle on empty list should return False"
    assert empty_tm.update_task(1, "Test") == False, "Update on empty list should return False"
    assert empty_tm.delete_task(1) == False, "Delete on empty list should return False"
    print("  ✓ Operations on empty list handled gracefully")

    print("✓ All edge cases handled correctly")


def test_full_workflow():
    """Test complete user workflow."""
    print("\n=== Test 8: Full Workflow ===")
    tm = TaskManager()

    # Create tasks
    task1 = tm.add_task("Buy groceries", "Milk, eggs, bread")
    task2 = tm.add_task("Complete homework", "Math assignment")
    task3 = tm.add_task("Call dentist", "Schedule appointment")

    # View all tasks
    tasks = tm.get_all_tasks()
    assert len(tasks) == 3, "Should have 3 tasks"

    # Mark one as complete
    tm.toggle_complete(2)
    task = tm.get_task(2)
    assert task.completed == True, "Task 2 should be completed"

    # Update one
    tm.update_task(1, title="Buy groceries and snacks", description="Milk, eggs, bread, chips")
    task = tm.get_task(1)
    assert task.title == "Buy groceries and snacks", "Task 1 should be updated"

    # Delete one
    tm.delete_task(3)
    tasks = tm.get_all_tasks()
    assert len(tasks) == 2, "Should have 2 tasks remaining"

    # Verify final state
    task_ids = [task.id for task in tasks]
    assert 1 in task_ids and 2 in task_ids, "Tasks 1 and 2 should remain"
    assert 3 not in task_ids, "Task 3 should be deleted"

    print("✓ Full workflow completed successfully")


def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 60)
    print("Running Automated Tests for Todo Application")
    print("=" * 60)

    try:
        test_task_creation()
        test_task_retrieval()
        test_task_completion()
        test_task_update()
        test_task_deletion()
        test_console_interface()
        test_edge_cases()
        test_full_workflow()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("  - Task creation: ✓")
        print("  - Task retrieval: ✓")
        print("  - Task completion toggle: ✓")
        print("  - Task update: ✓")
        print("  - Task deletion: ✓")
        print("  - Console interface: ✓")
        print("  - Edge cases: ✓")
        print("  - Full workflow: ✓")
        print("\nThe application is ready for use!")
        return True
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
