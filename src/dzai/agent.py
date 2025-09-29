from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

import click
import yaml
from pydantic import BaseModel, Field
from pydantic.types import SecretStr
from pydantic_ai import Agent, RunContext
from pydantic_ai.builtin_tools import AbstractBuiltinTool, WebSearchTool
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import RunUsage
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict

from dzai.logging_utils import logger
from dzai.retry_utils import create_retrying_client, google_retrying_client
from dzai.tools.registry import todo_toolset


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: SecretStr = SecretStr("some-secret")

    GEMINI_API_KEY: SecretStr = SecretStr("some-secret")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ModelSettingsSpec(BaseModel):
    """Configuration for model-specific settings"""

    # TODO: Use this setting to configure timeouts
    timeout: float | None = None


class AgentAsTool(BaseModel):
    agent: AgentSpec

    async def run_tool(self, ctx: RunContext[None], query: str) -> str:
        """
        Run the agent as tool.
        """
        result = await self.agent.run(
            query,
            usage=ctx.usage,  # This preserves token counting
        )
        return result.output


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

    # Agents as tools
    agent_tools: list[str] = []

    # Env variables
    anthropic_api_key: SecretStr | None = None

    gemini_api_key: SecretStr | None = None

    @staticmethod
    def from_config(
        config_file: Path, *, anthropic_api_key: SecretStr | None = None, gemini_api_key: SecretStr | None = None
    ) -> AgentSpec:
        """Load agent specification from YAML file"""
        with config_file.open() as cf:
            yaml_spec = yaml.safe_load(cf)
            return AgentSpec.model_validate(
                {**yaml_spec, "gemini_api_key": gemini_api_key, "anthropic_api_key": anthropic_api_key}
            )

    @property
    def provider_model(self) -> AnthropicModel | OpenAIChatModel | GoogleModel:
        provider = self.model.split(":")[0]
        model = self.model.split(":")[1]
        client = create_retrying_client()
        match provider:
            case "anthropic":
                return AnthropicModel(model, provider=AnthropicProvider(http_client=client))
            case "openai":
                return OpenAIChatModel(model, provider=OpenAIProvider(http_client=client))
            case "google":
                # This is not amazing right now. We can't do both user tools and built in tools!
                assert self.gemini_api_key is not None, "`GEMINI_API_KEY` is not set."
                client = google_retrying_client(api_key=self.gemini_api_key)
                return GoogleModel(model, provider=GoogleProvider(client=client))
            case _:
                raise ValueError(f"Unsupported model type: {self.model}")

    def as_tool_function(self) -> Callable:
        """Convert this agent spec into a tool function"""

        async def agent_tool(ctx: RunContext[None], query: str) -> str:
            agent = Agent(
                model=self.provider_model,
                instructions=self.instructions,
                name=self.name,
            )

            result = await agent.run(query, usage=ctx.usage)
            return result.output

        agent_tool.__name__ = f"{self.name.lower().replace('-', '_')}_agent"
        agent_tool.__doc__ = f"""
            Run the {self.name} agent.
            {self.instructions[:200]}...

            Args:
                query: Query to send to the agent
            """

        return agent_tool


async def main(agent_name: str, query: str) -> None:
    """Load and run agent from YAML configuration"""

    config_file_yml = Path(__file__).resolve().parent / "agents" / f"{agent_name}.yml"

    settings = Settings()

    assert config_file_yml.exists(), (
        f"Error: Agent configuration file '{agent_name}.yml'  not found in {config_file_yml.parent} directory."
    )
    agent_spec = AgentSpec.from_config(config_file_yml, gemini_api_key=settings.GEMINI_API_KEY)

    # Prepare builtin tools
    builtin_tools: Sequence[AbstractBuiltinTool] = []
    # ToDo: Make this an enum and the loading should be part of AgentSpec validation
    if "web_search" in agent_spec.builtin_tools:
        builtin_tools.append(WebSearchTool())

    agent = Agent(
        model=agent_spec.provider_model,
        instructions=agent_spec.instructions,
        name=agent_spec.name,
        # TODO: This should be from the registry
        toolsets=[todo_toolset()],
        # TODO: This should be from the registry
        builtin_tools=builtin_tools,
    )

    logger.info(f"Starting agent run for Agent: {agent_spec.name}.")
    usage = RunUsage()
    result = await agent.run(query, usage=usage)

    logger.info(
        f"Input tokens: {usage.input_tokens}, Output tokens: {usage.output_tokens}, "
        f"Total tokens: {usage.total_tokens}, Details: {usage.details}"
    )

    # Write output to file
    output_file = Path("outputs") / f"output_{datetime.now().isoformat(timespec='seconds')}.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as of:
        of.write(result.output)

    logger.info(f"Output written to {output_file}.")

    # Write message history to file
    messages_file = Path("outputs") / f"messages_{datetime.now().isoformat(timespec='seconds')}.json"
    with messages_file.open("wb") as mf:
        mf.write(result.all_messages_json())

    logger.info(f"Message history written to {messages_file}.")


@click.command(
    help="Run an AI agent.\n\nAgents available are:\n\n  api-research-agent: To research a lib/API on implementation.",
    no_args_is_help=True,
)
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
