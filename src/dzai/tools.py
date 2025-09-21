from __future__ import annotations

from pydantic import BaseModel


class ToDoItem(BaseModel):
    task: str
    completed: bool = False
    notes: str = ""


class ToDoList(BaseModel):
    """Data structure for managing research tasks"""

    todos: list[ToDoItem] = []


def add_todo(todo_list: ToDoList, task: str) -> str:
    """Add a new todo item"""
    todo_list.todos.append(ToDoItem(task=task))
    return f"Added todo: {task}"


def complete_todo(todo_list: ToDoList, task: str) -> str:
    """Mark a todo as completed"""
    for todo in todo_list.todos:
        if todo.task == task:
            todo.completed = True
            return f"Completed todo: {task}"
    return f"Todo not found: {task}"


def list_todos(todo_list: ToDoList) -> str:
    """List all todos with their status"""
    if not todo_list.todos:
        return "No todos found"

    result = "Current todos:\n"
    for i, todo in enumerate(todo_list.todos, 1):
        status = "✓" if todo.completed else "○"
        result += f"{i}. {status} {todo.task}\n"
        if todo.notes:
            result += f"   Notes: {todo.notes}\n"
    return result


def add_notes_to_todo(todo_list: ToDoList, task: str, notes: str) -> str:
    """Add notes to a specific todo item"""
    for todo in todo_list.todos:
        if todo.task == task:
            todo.notes = notes
            return f"Added notes to todo: {task}"
    return f"Todo not found: {task}"
