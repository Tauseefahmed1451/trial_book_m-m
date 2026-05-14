"""Logging configuration."""

import sys

from loguru import logger


def configure_logging(environment: str) -> None:
    """Configure console logging with a compact structured format."""
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG" if environment == "development" else "INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
