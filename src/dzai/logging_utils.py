import logging


def _logger(log_level: int) -> logging.Logger:
    logging.basicConfig(level=log_level, format="%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s")
    return logging.getLogger()


def set_level(log_level: int, *, logger: logging.Logger) -> None:
    """Set level of the logger"""
    logger.setLevel(log_level)

    # Enable our own retry_utils logger which contains request/response hooks
    logging.getLogger("dzai.retry_utils").setLevel(log_level)

    # HTTPX is used by both Anthropic/OpenAI and Google GenAI for HTTP requests
    # Enable debug logging for httpx and httpcore to see HTTP request/response details
    logging.getLogger("httpx").setLevel(log_level)
    logging.getLogger("httpcore").setLevel(log_level)

    # Other HTTP/Transport loggers
    logging.getLogger("requests").setLevel(log_level)
    logging.getLogger("urllib3").setLevel(log_level)

    # Core Google Client and GenAI loggers
    logging.getLogger("google").setLevel(log_level)
    logging.getLogger("google.genai").setLevel(log_level)

    # These libraries are often used for transport and API calls within the Google ecosystem
    logging.getLogger("google.cloud").setLevel(log_level)
    logging.getLogger("google.api_core").setLevel(log_level)

    # Another common one for Google's API clients
    logging.getLogger("googleapiclient").setLevel(log_level)


logger = _logger(log_level=logging.INFO)
