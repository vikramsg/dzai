from __future__ import annotations

import asyncio
from pathlib import Path

import click
import yaml
from pydantic import BaseModel, Field
from pydantic.types import SecretStr
from pydantic_ai import Agent
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: SecretStr = SecretStr("some-secret")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ModelSettingsSpec(BaseModel):
    """Configuration for model-specific settings"""

    timeout: float | None = None


class AgentSpec(BaseModel):
    """Enhanced specification for pydantic-ai Agent configuration"""

    # Core parameters
    model: str = Field(..., description="LLM model identifier")
    instructions: str | list[str] | None = None

    # Advanced configuration
    name: str | None = None
    output_type: str = "str"  # Could be expanded to support complex types

    # Model settings
    model_settings: ModelSettingsSpec | None = None

    @staticmethod
    def from_config(config_file: Path) -> AgentSpec:
        """Load agent specification from YAML file"""
        with config_file.open() as cf:
            yaml_spec = yaml.safe_load(cf)
            return AgentSpec.model_validate(yaml_spec)


async def main(agent_name: str, query: str) -> None:
    """Load and run agent from YAML configuration"""
    agents_dir = Path("agents")
    config_file_yml = agents_dir / f"{agent_name}.yml"

    assert config_file_yml.exists(), (
        f"Error: Agent configuration file '{agent_name}.yml'  not found in agents/ directory."
    )
    agent_spec = AgentSpec.from_config(config_file_yml)

    # Convert instructions list to string if needed
    instructions = agent_spec.instructions
    if isinstance(instructions, list):
        instructions = "\n".join(instructions)

    agent = Agent(
        model=agent_spec.model,
        instructions=instructions,
        name=agent_spec.name,
    )

    result = await agent.run(query)
    print(result.output)


@click.command()
@click.argument("agent_name", required=True)
@click.option("-q", "--query", help="Query to send to the agent", required=True)
def cli(agent_name: str, query: str) -> None:
    """Run an agent from the agents folder or execute test mode"""
    asyncio.run(main(agent_name, query))


if __name__ == "__main__":
    cli()
