from pydantic_ai.toolsets.function import FunctionToolset

from dzai.logging_utils import logger
from dzai.tools.todo import ToDoItem, ToDoList


def todo_toolset() -> FunctionToolset:
    """
    Toolset to maintain state.

    FIXME:
    This is not amazing, but we need to figure out how to create tools that need state.
    """
    state = ToDoList()  # private per-toolset instance

    def add_todo(task: str) -> str:
        state.todos.append(ToDoItem(task=task))
        logger.info(f"Added task: {task}")
        return f"Added: {task}"

    def complete_todo(task: str) -> str:
        for t in state.todos:
            if t.task == task:
                t.completed = True
                logger.info(f"Completed task: {task}")
                return f"Completed: {task}"
        return f"Not found: {task}"

    def add_notes_to_todo(task: str, notes: str) -> str:
        for t in state.todos:
            if t.task == task:
                t.notes = notes
                return f"Noted: {task}"
        return f"Not found: {task}"

    def list_todos() -> str:
        if not state.todos:
            return "No todos."
        lines = ["Todos:"]
        for i, t in enumerate(state.todos, 1):
            status = "✓" if t.completed else "○"
            lines.append(f"{i}. {status} {t.task}" + (f" — {t.notes}" if t.notes else ""))
        return "\n".join(lines)

    # expose as tools (no globals; each call to make_todo_toolset gets fresh state)
    return FunctionToolset(tools=[add_todo, complete_todo, add_notes_to_todo, list_todos])
