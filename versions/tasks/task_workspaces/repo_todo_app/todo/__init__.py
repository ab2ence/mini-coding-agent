"""
Todo App - Filtering Module
"""

def filter_todos(todos, priority=None):
    """
    Filter todos by optional priority.

    Args:
        todos: List of todo dicts with 'title', 'priority', 'done' keys
        priority: Optional priority level to filter by

    Returns:
        Filtered list of todos
    """
    result = []
    for todo in todos:
        if priority is None:
            result.append(todo)
        elif todo.get('priority') == priority:
            result.append(todo)
    return result


def get_todo_stats(todos):
    """Get statistics for todo list."""
    total = len(todos)
    completed = sum(1 for t in todos if t.get('done', False))
    pending = total - completed

    by_priority = {}
    for todo in todos:
        p = todo.get('priority', 'medium')
        by_priority[p] = by_priority.get(p, 0) + 1

    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'by_priority': by_priority
    }


def mark_complete(todos, title):
    """Mark a todo as complete by title."""
    for todo in todos:
        if todo.get('title') == title:
            todo['done'] = True
            return True
    return False


def add_todo(todos, title, priority='medium'):
    """Add a new todo."""
    todos.append({
        'title': title,
        'priority': priority,
        'done': False
    })
    return todos


__all__ = ['filter_todos', 'get_todo_stats', 'mark_complete', 'add_todo']
