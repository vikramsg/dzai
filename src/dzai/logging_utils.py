import logging
import os


def _logger(log_level: int) -> logging.Logger:
    logging.basicConfig(level=log_level, format="%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s")
    return logging.getLogger()


logger = (
    _logger(log_level=logging.DEBUG) if os.getenv("LOG_LEVEL", None) == "debug" else _logger(log_level=logging.INFO)
)
