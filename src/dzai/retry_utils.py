from collections.abc import Callable

from google.genai import Client
from google.genai.types import HttpOptions
from httpx import AsyncClient, HTTPStatusError, Response
from pydantic.types import SecretStr
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential


def _retrying_transport() -> AsyncTenacityTransport:
    def should_retry_status(response: Response) -> None:
        """Raise exceptions for retryable HTTP status codes."""
        if response.status_code in (429, 529):
            """
            429: Rate limits.
            529: Server overloaded.
            """
            response.raise_for_status()  # This will raise HTTPStatusError

    return AsyncTenacityTransport(
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


def create_retrying_client(*, async_retrying_transport_callable: Callable = _retrying_transport) -> AsyncClient:
    """
    Create a client with smart retry handling for multiple error types.

    Copied from here - https://ai.pydantic.dev/retries/#usage-example
    """
    transport = async_retrying_transport_callable()

    return AsyncClient(transport=transport)


def google_retrying_client(*, api_key: SecretStr, async_retrying_transport: Callable = _retrying_transport) -> Client:
    """
    Configure Google Gen AI client with custom HttpOptions
    Note: The google-genai SDK supports passing custom client args
    """
    transport = async_retrying_transport()

    return Client(
        api_key=api_key.get_secret_value(),
        http_options=HttpOptions(
            async_client_args={"transport": transport}  # Pass transport through client args
        ),
    )
