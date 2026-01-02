"""Main entry point for the Todo console application."""
from services.task_manager import TaskManager
from cli.console_interface import ConsoleInterface


def main() -> None:
    """Main application entry point and event loop."""
    try:
        # Display welcome message
        print("\n" + "=" * 60)
        print("Welcome to the Todo Application!")
        print("=" * 60)
        print("ℹ Note: This is an in-memory application.")
        print("  All tasks will be lost when the application exits.")
        print("=" * 60)

        # Initialize dependencies
        task_manager = TaskManager()
        console_interface = ConsoleInterface(task_manager)

        # Main event loop
        while True:
            console_interface.display_menu()
            choice = console_interface.get_user_choice()

            if choice == "1":
                console_interface.run_view_tasks_workflow()
            elif choice == "2":
                console_interface.run_add_task_workflow()
            elif choice == "3":
                console_interface.run_update_task_workflow()
            elif choice == "4":
                console_interface.run_delete_task_workflow()
            elif choice == "5":
                console_interface.run_toggle_complete_workflow()
            elif choice == "6":
                print("\nThank you for using the Todo Application!")
                break

            print()  # Blank line for readability

    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        print("Application will now exit.")


if __name__ == "__main__":
    main()
