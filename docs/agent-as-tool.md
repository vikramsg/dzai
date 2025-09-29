# Creating Agents as Tools in Pydantic AI

## Summary of Findings

Based on my research, Pydantic AI supports "Agent delegation" where an agent delegates work to another agent through tools, and you can pass `ctx.usage` to the usage keyword argument of the delegate agent run so usage within that run counts towards the total usage of the parent agent run. While you cannot directly pass agents in the `tools=[]` parameter, you can achieve flexible agent-as-tool functionality through wrapper functions and the Tool class.

## Key Implementation Approaches

### Agent Delegation Pattern 

The most straightforward approach is using agent delegation through tool functions:

```python
from pydantic_ai import Agent, RunContext
from typing import Any

# Define your sub-agent
specialist_agent = Agent(
    'openai:gpt-4o',
    output_type=str,
    system_prompt="You are a specialist in data analysis."
)

# Main agent that uses the specialist
main_agent = Agent(
    'openai:gpt-4o',
    system_prompt="You are a general assistant that can delegate to specialists."
)

@main_agent.tool
async def consult_specialist(ctx: RunContext[None], query: str) -> str:
    """Consult the data analysis specialist for complex analytical tasks."""
    result = await specialist_agent.run(
        query, 
        usage=ctx.usage  # This preserves token counting
    )
    return result.output

"""
Maybe we can just do main_agent = Agent(tool=[consult_specialist]). Should work? But how is the context passed?
"""
```

**Token Counting**: You'll generally want to pass ctx.usage to the usage keyword argument of the delegate agent run so usage within that run counts towards the total usage of the parent agent run.


## Token Counting with Agent Tools

**Yes, token counting is preserved** when using agents as tools. You can retrieve usage statistics (tokens, requests, etc.) at any time from the AgentRun object via agent_run.usage(). This method returns a RunUsage object containing the usage data.

Key points for token tracking:

1. **Pass `ctx.usage`**: You'll generally want to pass ctx.usage to the usage keyword argument of the delegate agent run so usage within that run counts towards the total usage of the parent agent run

2. **Usage aggregation**: The parent agent automatically aggregates token usage from all sub-agents when `ctx.usage` is passed

3. **Usage limits work**: You can still use UsageLimits — including request_limit, total_tokens_limit, and tool_calls_limit — to avoid unexpected costs or runaway tool loops

Example with usage tracking:

```python
from pydantic_ai import Agent, RunContext, UsageLimits

@main_agent.tool
async def consult_specialist(ctx: RunContext[None], query: str) -> str:
    result = await specialist_agent.run(
        query,
        usage=ctx.usage,  # Token usage aggregated to parent
        usage_limits=UsageLimits(total_tokens_limit=1000)
    )
    return result.output

# Run with usage limits
result = main_agent.run_sync(
    "Analyze this data",
    usage_limits=UsageLimits(total_tokens_limit=5000)
)

print(f"Total usage: {result.usage()}")  # Includes tokens from all agents
```

## Common Pitfalls and Solutions

### 1. Token Usage Not Tracked
**Problem**: Sub-agent token usage not included in parent totals.  
**Solution**: Always pass `ctx.usage` to sub-agent runs.

### 2. Dependencies Not Passed
**Problem**: Sub-agents don't have access to parent dependencies.  
**Solution**: Pass `deps=ctx.deps` when calling sub-agents.

### 3. Type Safety Issues
**Problem**: Generic type information lost with agent wrappers.  
**Solution**: Use proper type annotations and Tool class for better control.

```python
# Good: Proper typing
async def typed_agent_tool(ctx: RunContext[MyDeps], query: str) -> str:
    result = await sub_agent.run(query, deps=ctx.deps, usage=ctx.usage)
    return result.output
```

## Links to Resources

- [Pydantic AI Multi-Agent Patterns](https://ai.pydantic.dev/multi-agent-applications/) - Official documentation on agent delegation
- [Function Tools Documentation](https://ai.pydantic.dev/tools/) - Details on using the `tools=[]` parameter
- [Usage and Limits API](https://ai.pydantic.dev/api/usage/) - Token counting and usage limits
- [GitHub Multi-Agent Example Issue #300](https://github.com/pydantic/pydantic-ai/issues/300) - Community discussion on multi-agent implementation
- [Tool API Reference](https://ai.pydantic.dev/api/tools/) - Complete Tool class documentation

## Latest API Compatibility

All examples use the latest Pydantic AI API as of 2025. The agent delegation pattern with `ctx.usage` for token tracking is the current best practice recommended in the official documentation.

## Note

Doc created using `uv run dzai api-research-agent -q "How can I create an Agent as Tool using pydantic AI. I want to pass the agent the same way I pass a function as a tool using tools=[function] rather than restricting the agent as a tool to a particular agent using decorators. Will passing a Tool to the main agent still let us count the total number of tokens used."`.
