import logging


def _logger(log_level: int) -> logging.Logger:
    logging.basicConfig(level=log_level, format="%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s")
    return logging.getLogger()


def set_level(log_level: int, *, logger: logging.Logger) -> None:
    """Set level of the logger"""
    logger.setLevel(log_level)

    # HTTPX/HTTPCORE are used by Anthropic, OpenAI, and Google GenAI for HTTP requests
    # Enable debug logging to see HTTP request/response details including POST bodies
    logging.getLogger("httpx").setLevel(log_level)
    logging.getLogger("httpcore").setLevel(log_level)


logger = _logger(log_level=logging.INFO)
