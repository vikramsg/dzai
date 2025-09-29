## Research Report: Creating Pydantic AI Agents with Tools and Context

### Summary of Findings

You can register tools via the tools argument to the Agent constructor, which is useful when you want to reuse tools and can give more fine-grained control over the tools. Dependencies are carried via the RunContext argument, which is parameterized with the deps_type from above. If the type annotation here is wrong, static type checkers will catch it.

The correct approach to create a Pydantic AI agent with both tools and context involves:

1. **Define your dependencies type** using `deps_type` in the Agent constructor
2. **Register tools** using the `tools` parameter that can access context via `RunContext`
3. **Use either function references or Tool instances** in the tools list
4. **Access context in tools** through the `RunContext[YourDepsType]` parameter

### Code Examples

#### Basic Agent with Tools and Context

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, Tool

@dataclass
class MyDependencies:
    api_key: str
    user_id: int
    database_connection: object

# Method 1: Using function references directly
def get_user_info(ctx: RunContext[MyDependencies], user_query: str) -> str:
    """Get user information from the database."""
    # Access dependencies through ctx.deps
    user_id = ctx.deps.user_id
    db = ctx.deps.database_connection
    # Your tool logic here
    return f"User {user_id} info for query: {user_query}"

def external_api_call(ctx: RunContext[MyDependencies], endpoint: str) -> str:
    """Make an external API call."""
    api_key = ctx.deps.api_key
    # Your API call logic here
    return f"API response from {endpoint}"

# Create agent with tools and context
agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDependencies,
    tools=[get_user_info, external_api_call],
    instructions="You are a helpful assistant with access to user data and external APIs."
)
```

#### Using Tool Class for Fine-Grained Control

You can use Tool to reuse tool definitions and give more fine-grained control over how tools are defined, e.g. setting their name or description, or using a custom prepare method.

```python
from pydantic_ai import Agent, RunContext, Tool

@dataclass
class MyDependencies:
    api_key: str
    user_role: str

def role_specific_tool(ctx: RunContext[MyDependencies], action: str) -> str:
    """Perform role-specific actions."""
    role = ctx.deps.user_role
    return f"Executing {action} for role {role}"

# Method 2: Using Tool instances for more control
def prepare_tool(ctx: RunContext[MyDependencies], tool_def) -> object:
    """Only include this tool for admin users."""
    if ctx.deps.user_role == 'admin':
        return tool_def
    return None

admin_tool = Tool(
    role_specific_tool,
    name="admin_action",
    description="Administrative actions (admin only)",
    prepare=prepare_tool
)

agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDependencies,
    tools=[admin_tool],
    instructions="You are an assistant with role-based capabilities."
)
```

#### Running the Agent with Dependencies

```python
async def main():
    # Create dependency instance
    deps = MyDependencies(
        api_key="your-api-key",
        user_id=123,
        database_connection=your_db_connection
    )
    
    # Run the agent with dependencies
    result = await agent.run(
        "Get my user information and check external status",
        deps=deps
    )
    print(result.output)

# For synchronous usage
def main_sync():
    deps = MyDependencies(
        api_key="your-api-key", 
        user_id=123,
        database_connection=your_db_connection
    )
    
    result = agent.run_sync(
        "Get my user information",
        deps=deps
    )
    print(result.output)
```

#### Advanced Example: Bank Support Agent

Here's a comprehensive example from the Pydantic AI documentation showing a bank support agent:

```python
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn

class SupportOutput(BaseModel):
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description='Risk level of query', ge=0, le=10)

async def customer_balance(
    ctx: RunContext[SupportDependencies], 
    include_pending: bool
) -> float:
    """Returns the customer's current account balance."""
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id, 
        include_pending=include_pending
    )
    return balance

support_agent = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    tools=[customer_balance],
    instructions=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)
```

### Key Concepts and Best Practices

#### 1. Dependencies and Context
Pass the dataclass type to the deps_type argument of the Agent constructor. Note: we're passing the type here, NOT an instance, this parameter is not actually used at runtime, it's here so we can get full type checking of the agent. When running the agent, pass an instance of the dataclass to the deps parameter.

#### 2. Tool Registration Methods
There are multiple ways to register tools: via the @agent.tool decorator, via the @agent.tool_plain decorator, or via the tools keyword argument to Agent which can take either plain functions, or instances of Tool.

#### 3. Function Signature Inspection
The simplest way to register tools via the Agent constructor is to pass a list of functions, the function signature is inspected to determine if the tool takes RunContext.

### Common Pitfalls and Solutions

#### 1. **Pitfall**: Forgetting to specify `deps_type`
**Solution**: Always specify `deps_type` in the Agent constructor when your tools need context.

```python
# ❌ Wrong - tools won't have access to context
agent = Agent('openai:gpt-4o', tools=[my_tool])

# ✅ Correct - specify deps_type for context access
agent = Agent('openai:gpt-4o', deps_type=MyDependencies, tools=[my_tool])
```

#### 2. **Pitfall**: Incorrect RunContext typing
Dependencies are carried via the RunContext argument, which is parameterized with the deps_type from above. If the type annotation here is wrong, static type checkers will catch it.

```python
# ❌ Wrong - mismatched types
def my_tool(ctx: RunContext[str], param: int) -> str:  # But deps_type=MyDependencies
    return str(ctx.deps.user_id)  # This will cause type errors

# ✅ Correct - matching types  
def my_tool(ctx: RunContext[MyDependencies], param: int) -> str:
    return str(ctx.deps.user_id)
```

#### 3. **Pitfall**: Not handling tool prepare methods correctly
The prepare method should return that ToolDefinition with or without modifying it, return a new ToolDefinition, or return None to indicate this tools should not be registered for that step.

#### 4. **Pitfall**: Issues with streaming and tools
Based on a GitHub issue, there can be problems with tools working in agent.run() but not agent.run_stream(). Make sure to test both execution modes if you plan to use streaming.

### Advanced Features

#### Tool Preparation and Dynamic Registration
You can use prepare functions to conditionally include tools based on context:

```python
async def conditional_prepare(
    ctx: RunContext[MyDependencies], 
    tool_def: ToolDefinition
) -> ToolDefinition | None:
    # Only include tool if user has admin role
    if ctx.deps.user_role == 'admin':
        return tool_def
    return None

admin_tool = Tool(admin_function, prepare=conditional_prepare)
```

#### Agent-wide Tool Preparation
You can define an agent-wide prepare_tools function that is called at each step of a run and allows you to filter or modify the list of all tool definitions available to the agent for that step:

```python
async def prepare_all_tools(
    ctx: RunContext[MyDependencies], 
    tool_defs: list[ToolDefinition]
) -> list[ToolDefinition]:
    # Filter tools based on user permissions
    if ctx.deps.user_role == 'admin':
        return tool_defs  # All tools available
    else:
        # Filter out admin-only tools
        return [t for t in tool_defs if not t.name.startswith('admin_')]

agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDependencies,
    tools=[tool1, tool2, admin_tool],
    prepare_tools=prepare_all_tools
)
```

### References

- [Pydantic AI Official Documentation](https://ai.pydantic.dev/)
- [Function Tools Documentation](https://ai.pydantic.dev/tools/)
- [Agent API Reference](https://ai.pydantic.dev/api/agent/)
- [Dependencies Documentation](https://ai.pydantic.dev/dependencies/)
- [Tool API Reference](https://ai.pydantic.dev/api/tools/)
- [GitHub Repository](https://github.com/pydantic/pydantic-ai)

This approach provides type safety, reusability, and clean separation of concerns while allowing your tools to access shared context and dependencies through the RunContext parameter.
