from __future__ import annotations

from pydantic import BaseModel


class ToDoItem(BaseModel):
    task: str
    completed: bool = False
    notes: str = ""


class ToDoList(BaseModel):
    """Data structure for managing research tasks"""

    todos: list[ToDoItem] = []
