"""
Todo App - CLI Module

Public CLI interface for the todo application.
This interface MUST remain backward compatible.
"""

from . import __init__ as todo_module


def main():
    """Main CLI entry point."""
    import sys

    todos = []
    args = sys.argv[1:]

    if not args:
        print("Usage: todo [add|list|done|filter] [options]")
        return 1

    cmd = args[0]

    if cmd == 'add':
        title = ' '.join(args[1:]) if len(args) > 1 else 'New task'
        todo_module.add_todo(todos, title)
        print(f"Added: {title}")

    elif cmd == 'list':
        for t in todos:
            status = "[x]" if t.get('done') else "[ ]"
            print(f"{status} {t['title']}")

    elif cmd == 'done':
        if len(args) > 1:
            title = ' '.join(args[1:])
            todo_module.mark_complete(todos, title)
            print(f"Marked complete: {title}")

    elif cmd == 'filter':
        priority = args[1] if len(args) > 1 else None
        filtered = todo_module.filter_todos(todos, priority)
        for t in filtered:
            print(f"[ ] {t['title']}")

    return 0


def run_cli(args=None):
    """CLI runner for programmatic use."""
    return main()


if __name__ == '__main__':
    main()
