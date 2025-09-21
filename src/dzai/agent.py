import asyncio

from pydantic_ai import Agent


async def main() -> None:
    """Test main"""
    agent = Agent(
        "anthropic:claude-sonnet-4-0",
        instructions="Be concise, reply with one sentence.",
    )

    result = await agent.run('Where does "hello world" come from?')
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
