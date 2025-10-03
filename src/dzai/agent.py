from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import ClassVar

import click
import yaml
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator
from pydantic.types import SecretStr
from pydantic_ai import Agent, PartDeltaEvent, PartStartEvent, RunContext
from pydantic_ai.builtin_tools import AbstractBuiltinTool, WebSearchTool
from pydantic_ai.messages import TextPartDelta, ThinkingPartDelta, ToolCallPartDelta
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


class AgentSpec(BaseModel):
    """Specification for pydantic-ai Agent"""

    # Class variable - NOT a Pydantic field
    # This allows us to use this variable within a class method without creating an instance first.
    agent_root_dir: ClassVar[Path] = Path(__file__).resolve().parent / "agents"

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
    agent_tools: list[Callable] = []

    # Env variables
    anthropic_api_key: SecretStr | None = None

    gemini_api_key: SecretStr | None = None

    @classmethod
    def from_agent(
        cls, agent_name: str, *, anthropic_api_key: SecretStr | None = None, gemini_api_key: SecretStr | None = None
    ) -> AgentSpec:
        """Load agent specification from YAML file"""
        config_path = cls.agent_root_dir / f"{agent_name}.yml"
        assert config_path.exists(), f"Config file does not exist at {config_path}."

        with config_path.open() as cf:
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

    @property
    def all_tools(self) -> list[Callable]:
        return self.agent_tools

    @field_validator("agent_tools", mode="before")
    @classmethod
    def _agent_tool(cls, agent_tools: list[str]) -> list[Callable]:
        """
        We want to take agent name as input in the YML file but convert
        to a callable that can be input into the Pydantic Agent(...)
        """
        tools = []
        for tool in agent_tools:
            assert Path(cls.agent_root_dir / f"{tool}.yml").exists(), (
                f"Agent tool {tool} does not exist in dir: {cls.agent_root_dir}."
            )
            tools.append(AgentSpec.from_agent(tool)._as_tool())
        return tools

    def _as_tool(self) -> Callable:
        """
        Convert this agent spec into a tool function
        All the metaprogramming is required to send the correct function annotations.
        """

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

    settings = Settings()
    agent_spec = AgentSpec.from_agent(agent_name, gemini_api_key=settings.GEMINI_API_KEY)

    # Prepare builtin tools
    builtin_tools: Sequence[AbstractBuiltinTool] = []
    # ToDo: Make this an enum and the loading should be part of AgentSpec validation
    if "web_search" in agent_spec.builtin_tools:
        builtin_tools.append(WebSearchTool())

    toolsets = []
    # ToDo: Should be an enum and should come from agent validation
    if "todo" in agent_spec.tools:
        toolsets.append(todo_toolset())

    agent = Agent(
        model=agent_spec.provider_model,
        instructions=agent_spec.instructions,
        name=agent_spec.name,
        tools=agent_spec.all_tools,
        # TODO: This should be from the registry
        toolsets=toolsets,
        # TODO: This should be from the registry
        builtin_tools=builtin_tools,
    )

    logger.info(f"Starting agent run for Agent: {agent_spec.name}.")
    usage = RunUsage()

    logger.info("🚀 Starting detailed agent execution...")

    async with agent.iter(query, usage=usage) as run:
        step_count = 0
        async for node in run:
            step_count += 1
            logger.info(f"--- Step {step_count} ---")

            if agent.is_user_prompt_node(node):
                logger.info(f"👤 User Prompt: {node.user_prompt}")

            elif agent.is_model_request_node(node):
                logger.info("🤖 Model Request Node")

                async with node.stream(run.ctx) as stream:
                    current_response = ""
                    async for event in stream:
                        if isinstance(event, PartStartEvent):
                            logger.info(f"📝 Starting part {event.index}: {type(event.part).__name__}")

                        elif isinstance(event, PartDeltaEvent):
                            if isinstance(event.delta, ThinkingPartDelta):
                                logger.info(f"🤔 Thinking: {event.delta.content_delta}")
                            elif isinstance(event.delta, TextPartDelta):
                                current_response += event.delta.content_delta
                                logger.info(f"💬 Response chunk: {event.delta.content_delta}")
                            elif isinstance(event.delta, ToolCallPartDelta):
                                logger.info(f"🔧 Tool call delta: {event.delta}")

            elif agent.is_call_tools_node(node):
                logger.info("⚙️ Calling Tools Node")
                logger.info(f"   Tools to call: {[call.tool_name for call in node.tool_calls]}")

                for tool_call in node.tool_calls:
                    logger.info(f"   🔧 Executing {tool_call.tool_name}")
                    logger.info(f"      Args: {tool_call.args}")

            else:
                logger.info(f"❓ Unknown node type: {type(node).__name__}")

    logger.info(f"🎯 Agent execution completed in {step_count} steps")
    logger.info(f"📊 Final result type: {type(run.result)}")

    logger.info(
        f"Input tokens: {usage.input_tokens}, Output tokens: {usage.output_tokens}, "
        f"Total tokens: {usage.total_tokens}, Details: {usage.details}"
    )

    # Write output to file
    output_file = Path("outputs") / f"output_{datetime.now().isoformat(timespec='seconds')}.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as of:
        of.write(run.result.output)

    logger.info(f"Output written to {output_file}.")

    # Write message history to file
    messages_file = Path("outputs") / f"messages_{datetime.now().isoformat(timespec='seconds')}.json"
    with messages_file.open("wb") as mf:
        mf.write(run.result.all_messages_json())

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
        uv run agent api-research-agent -q "hello"

        LOG_LEVEL=debug uv run agent api-research-agent -q "hello" # Enable debug logging
    """
    asyncio.run(main(agent_name, query))


if __name__ == "__main__":
    cli()
