from __future__ import annotations

import asyncio
from pathlib import Path

import click
import yaml
from pydantic import BaseModel, Field
from pydantic.types import SecretStr
from pydantic_ai import Agent
from pydantic_ai.builtin_tools import WebSearchTool
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict

from dzai.tools import ToDoList, add_notes_to_todo, add_todo, complete_todo, list_todos


def create_todo_tools(todo_list: ToDoList) -> list:
    """Create tool functions that work with the shared todo list"""

    def add_task(task: str) -> str:
        """Add a new research task to the todo list"""
        return add_todo(todo_list, task)

    def complete_task(task: str) -> str:
        """Mark a research task as completed"""
        return complete_todo(todo_list, task)

    def show_tasks() -> str:
        """Show all current research tasks and their status"""
        return list_todos(todo_list)

    def add_task_notes(task: str, notes: str) -> str:
        """Add notes to a specific research task"""
        return add_notes_to_todo(todo_list, task, notes)

    return [add_task, complete_task, show_tasks, add_task_notes]


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: SecretStr = SecretStr("some-secret")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ModelSettingsSpec(BaseModel):
    """Configuration for model-specific settings"""

    # TODO: Use this setting to configure timeouts
    timeout: float | None = None


class AgentSpec(BaseModel):
    """Enhanced specification for pydantic-ai Agent configuration"""

    # Core parameters
    model: str = Field(..., description="LLM model identifier")
    instructions: str

    # Advanced configuration
    name: str | None = None
    output_type: str = "str"  # Could be expanded to support complex types

    # Model settings
    model_settings: ModelSettingsSpec | None = None

    # Tools configuration
    tools: list[str] = []
    builtin_tools: list[str] = []

    @staticmethod
    def from_config(config_file: Path) -> AgentSpec:
        """Load agent specification from YAML file"""
        with config_file.open() as cf:
            yaml_spec = yaml.safe_load(cf)
            return AgentSpec.model_validate(yaml_spec)


async def main(agent_name: str, query: str) -> None:
    """Load and run agent from YAML configuration"""
    import datetime

    agents_dir = Path("agents")
    config_file_yml = agents_dir / f"{agent_name}.yml"

    assert config_file_yml.exists(), (
        f"Error: Agent configuration file '{agent_name}.yml'  not found in agents/ directory."
    )
    agent_spec = AgentSpec.from_config(config_file_yml)

    # Create shared todo list for the agent
    todo_list = ToDoList()

    # Prepare tools
    tools = []
    if "todo" in agent_spec.tools:
        tools.extend(create_todo_tools(todo_list))

    # Prepare builtin tools
    builtin_tools = []
    if "web_search" in agent_spec.builtin_tools:
        builtin_tools.append(WebSearchTool())

    agent = Agent(
        model=agent_spec.model,
        instructions=agent_spec.instructions,
        name=agent_spec.name,
        # FIXME: Tools are not working yet
        #     tools=tools if tools else None,
        #     builtin_tools=builtin_tools if builtin_tools else None,
    )

    result = await agent.run(query)
    print(result.output)

    # Create markdown output file for API research agent
    if agent_name == "api-research-agent":
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)

        filename = f"research-{timestamp}.md"
        filepath = outputs_dir / filename

        # Create markdown content
        markdown_content = f"""# API Research Report

Query: {query}

Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Research Results

{result.output}

## Research Tasks

{list_todos(todo_list)}
"""

        with filepath.open("w") as f:
            f.write(markdown_content)

        print(f"\nMarkdown report created: {filepath}")


@click.command()
@click.argument("agent_name", required=True)
@click.option("-q", "--query", help="Query to send to the agent", required=True)
def cli(agent_name: str, query: str) -> None:
    """
    Run an agent from the agents folder

    Usage:
        # Note that name after agent is the name of the yml file in the agents folder.
        uv run agent test_agent_config -q "hello"
    """
    asyncio.run(main(agent_name, query))


if __name__ == "__main__":
    cli()
