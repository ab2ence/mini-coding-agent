"""
Tests for todo filtering functionality.
"""

import pytest
from todo import filter_todos, get_todo_stats, add_todo


@pytest.fixture
def sample_todos():
    """Sample todo list for testing."""
    return [
        {'title': 'Task 1', 'priority': 'high', 'done': False},
        {'title': 'Task 2', 'priority': 'medium', 'done': False},
        {'title': 'Task 3', 'priority': 'low', 'done': True},
        {'title': 'Task 4', 'priority': 'high', 'done': False},
        {'title': 'Task 5', 'priority': 'medium', 'done': True},
    ]


class TestFilterTodos:
    """Test filter_todos function."""

    def test_filter_by_high_priority(self, sample_todos):
        """Test filtering by high priority."""
        result = filter_todos(sample_todos, 'high')
        assert len(result) == 2
        assert all(t['priority'] == 'high' for t in result)

    def test_filter_by_medium_priority(self, sample_todos):
        """Test filtering by medium priority."""
        result = filter_todos(sample_todos, 'medium')
        assert len(result) == 2
        assert all(t['priority'] == 'medium' for t in result)

    def test_filter_by_low_priority(self, sample_todos):
        """Test filtering by low priority."""
        result = filter_todos(sample_todos, 'low')
        assert len(result) == 1
        assert result[0]['priority'] == 'low'

    def test_filter_no_priority_returns_all(self, sample_todos):
        """Test that None priority returns all todos."""
        result = filter_todos(sample_todos, None)
        assert len(result) == len(sample_todos)

    def test_filter_nonexistent_priority(self, sample_todos):
        """Test filtering by nonexistent priority returns empty."""
        result = filter_todos(sample_todos, 'urgent')
        assert len(result) == 0

    def test_filter_empty_list(self):
        """Test filtering empty list."""
        result = filter_todos([], 'high')
        assert len(result) == 0

    def test_filter_preserves_original(self, sample_todos):
        """Test that filtering doesn't modify original list."""
        original_len = len(sample_todos)
        filter_todos(sample_todos, 'high')
        assert len(sample_todos) == original_len


class TestGetTodoStats:
    """Test get_todo_stats function."""

    def test_stats_calculation(self, sample_todos):
        """Test statistics calculation."""
        stats = get_todo_stats(sample_todos)
        assert stats['total'] == 5
        assert stats['completed'] == 2
        assert stats['pending'] == 3

    def test_stats_by_priority(self, sample_todos):
        """Test priority breakdown in stats."""
        stats = get_todo_stats(sample_todos)
        assert stats['by_priority']['high'] == 2
        assert stats['by_priority']['medium'] == 2
        assert stats['by_priority']['low'] == 1

    def test_stats_empty_list(self):
        """Test stats for empty list."""
        stats = get_todo_stats([])
        assert stats['total'] == 0
        assert stats['completed'] == 0
        assert stats['pending'] == 0


class TestAddTodo:
    """Test add_todo function."""

    def test_add_todo(self):
        """Test adding a todo."""
        todos = []
        add_todo(todos, 'New task', 'high')
        assert len(todos) == 1
        assert todos[0]['title'] == 'New task'
        assert todos[0]['priority'] == 'high'
        assert todos[0]['done'] is False

    def test_add_todo_default_priority(self):
        """Test adding todo with default priority."""
        todos = []
        add_todo(todos, 'New task')
        assert todos[0]['priority'] == 'medium'
