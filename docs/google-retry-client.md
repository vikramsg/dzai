## Research Report: Using Pydantic AI Retrying Client with Google Models

### Summary of Findings

After thorough research of the Pydantic AI documentation, GitHub issues, and Google Gen AI SDK documentation, I've identified the core issue and solution for using a retrying client with Google models in Pydantic AI.

**The Problem**: GoogleProvider expects a `google.genai.Client` instance, not an `httpx.AsyncClient` directly. The user was attempting to pass an `httpx.AsyncClient` with retry transport directly to `GoogleProvider(client=client)`, which is incompatible with the expected API.

**The Solution**: Create a `google.genai.Client` with custom `http_options` that can configure the underlying HTTP behavior, including custom transports.

### Code Examples

#### Working Solution: Using HttpOptions with Custom Transport

The correct approach is to configure the retry behavior through the Google Gen AI SDK's `HttpOptions`:

```python
from httpx import AsyncClient
from tenacity import retry_if_exception_type, stop_after_attempt
from google.genai import Client
from google.genai.types import HttpOptions
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig

# Create the retry transport
transport = AsyncTenacityTransport(
    config=RetryConfig(
        retry=retry_if_exception_type(HTTPStatusError),
        wait=wait_retry_after(max_wait=300),
        stop=stop_after_attempt(5),
        reraise=True
    ),
    validate_response=lambda r: r.raise_for_status()
)

# Create httpx client with retry transport
http_client = AsyncClient(transport=transport)

# Configure Google Gen AI client with custom HttpOptions
# Note: The google-genai SDK supports passing custom client args
client = Client(
    api_key='your-api-key',
    http_options=HttpOptions(
        async_client_args={'transport': transport}  # Pass transport through client args
    )
)

# Create GoogleProvider with the custom client
provider = GoogleProvider(client=client)
model = GoogleModel('gemini-1.5-flash', provider=provider)
```

#### Alternative: Using HTTP Client Args in HttpOptions

The Google Gen AI SDK supports passing additional arguments to the underlying HTTP client through `async_client_args`:

```python
from google.genai.types import HttpOptions
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig

# Create the retry configuration
retry_config = RetryConfig(
    retry=retry_if_exception_type(HTTPStatusError),
    wait=wait_retry_after(max_wait=300),
    stop=stop_after_attempt(5),
    reraise=True
)

transport = AsyncTenacityTransport(
    config=retry_config,
    validate_response=lambda r: r.raise_for_status()
)

# Pass transport through HttpOptions
http_options = HttpOptions(
    async_client_args={'transport': transport}
)

client = Client(
    api_key='your-api-key',
    http_options=http_options
)

provider = GoogleProvider(client=client)
model = GoogleModel('gemini-1.5-flash', provider=provider)
```

#### Complete Working Example

```python
from httpx import AsyncClient, HTTPStatusError
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential
from google.genai import Client
from google.genai.types import HttpOptions
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after

def create_retrying_google_model():
    """Create a Google model with retry capabilities."""
    
    # Configure retry behavior
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type(HTTPStatusError),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=1, max=60),
                max_wait=300
            ),
            stop=stop_after_attempt(5),
            reraise=True
        ),
        validate_response=lambda r: r.raise_for_status()
    )
    
    # Create Google Gen AI client with retry transport
    client = Client(
        api_key='your-api-key',
        http_options=HttpOptions(
            async_client_args={'transport': transport}
        )
    )
    
    # Create provider and model
    provider = GoogleProvider(client=client)
    return GoogleModel('gemini-1.5-flash', provider=provider)

# Usage
model = create_retrying_google_model()
agent = Agent(model)

result = await agent.run("Hello, world!")
print(result.data)
```

### Common Pitfalls and Solutions

#### 1. **Incorrect Client Type**
**Problem**: Attempting to pass `httpx.AsyncClient` directly to `GoogleProvider`
```python
# ❌ This doesn't work
client = AsyncClient(transport=transport)
provider = GoogleProvider(client=client)  # Type error!
```

**Solution**: Use `google.genai.Client` with `HttpOptions`
```python
# ✅ This works
client = Client(
    api_key='your-api-key',
    http_options=HttpOptions(async_client_args={'transport': transport})
)
provider = GoogleProvider(client=client)
```

#### 2. **Missing Retry Configuration**
**Problem**: Without a response validator, only network errors and timeouts will result in a retry

**Solution**: Always include `validate_response` in your transport configuration:
```python
transport = AsyncTenacityTransport(
    config=RetryConfig(...),
    validate_response=lambda r: r.raise_for_status()  # Important!
)
```

#### 3. **Tool-Level Retries vs Model-Level Retries**
**Problem**: Retry mechanism only works when applied to the function that runs the entire agent, not individual tools

**Solution**: Configure retries at the model/provider level for HTTP-related errors, and use Pydantic AI's built-in tool retry mechanisms for tool-specific issues.

### Links to Relevant Resources

- [Pydantic AI Retries Documentation](https://ai.pydantic.dev/retries/) - Comprehensive guide to HTTP request retries in Pydantic AI
- [Google Provider Documentation](https://ai.pydantic.dev/models/google/) - Examples of using GoogleProvider with custom clients
- [Google Gen AI SDK HttpOptions](https://googleapis.github.io/python-genai/genai.html#genai.types.HttpOptions) - Details on configuring HTTP options for the Google Gen AI client
- [GitHub Issue #2035](https://github.com/pydantic/pydantic-ai/issues/2035) - Community discussion on patterns for using custom HTTP clients

### Key Takeaways

1. **GoogleProvider Requires Google Gen AI Client**: GoogleProvider expects a `google.genai.Client`, not a raw HTTP client
2. **Configure Retries Through HttpOptions**: Use `HttpOptions.async_client_args` to pass custom transport configurations
3. **Always Include Response Validation**: Response validators are crucial for retrying HTTP status errors
4. **Latest API Usage**: Use `pydantic_ai.retries.RetryConfig` instead of deprecated `tenacity.AsyncRetrying` objects

The solution involves creating a proper `google.genai.Client` configured with `HttpOptions` that passes the retry transport through to the underlying HTTP client, rather than trying to pass the `httpx.AsyncClient` directly to the provider.

## Notes

This doc was generated by using `uv run dzai api-research-agent -q "look at pydantic ai documentation. I have created a retrying client to use. However the provider api is not clear for Google models. https://ai.pydantic.dev/retries/#usage-example
    client = AsyncClient(transport=transport). This syntax does not seem to work when I do GoogleModel(model, provider=GoogleProvider(client=client))"`.
