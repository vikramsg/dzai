from httpx import AsyncClient, HTTPStatusError, Response
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential


def create_retrying_client() -> AsyncClient:
    """
    Create a client with smart retry handling for multiple error types.

    Copied from here - https://ai.pydantic.dev/retries/#usage-example
    """

    def should_retry_status(response: Response) -> None:
        """Raise exceptions for retryable HTTP status codes."""
        if response.status_code in (429, 529):
            """
            429: Rate limits.
            529: Server overloaded.
            """
            response.raise_for_status()  # This will raise HTTPStatusError

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            # Retry on HTTP errors and connection issues
            retry=retry_if_exception_type((HTTPStatusError, ConnectionError)),
            # Smart waiting: respects Retry-After headers, falls back to exponential backoff
            wait=wait_retry_after(fallback_strategy=wait_exponential(multiplier=1, max=60), max_wait=300),
            # Stop after 5 attempts
            stop=stop_after_attempt(5),
            # Re-raise the last exception if all retries fail
            reraise=True,
        ),
        validate_response=should_retry_status,
    )
    return AsyncClient(transport=transport)
