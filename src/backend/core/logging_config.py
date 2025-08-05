"""
Centralized logging configuration for SPOTS project
Replaces print statements with structured logging
"""

import logging
import structlog
from pathlib import Path
import sys
from typing import Optional

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (usually __name__ from the calling module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None, json_logs: bool = False) -> None:
    """
    Setup application-wide logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        json_logs: Whether to output logs in JSON format
    """
    # Configure Python's logging
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=getattr(logging, level.upper()))

    # Reconfigure structlog for the specified format
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.processors.CallsiteParameterAdder(
                    parameters=[
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.LINENO,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                    ]
                ),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        logging.getLogger().addHandler(file_handler)


# Convenience logger for quick migration from print statements
logger = get_logger("spots")


# Migration helpers to make replacement easier
def log_info(message: str, **kwargs) -> None:
    """Direct replacement for print() statements"""
    logger.info(message, **kwargs)


def log_error(message: str, **kwargs) -> None:
    """Log error messages"""
    logger.error(message, **kwargs)


def log_debug(message: str, **kwargs) -> None:
    """Log debug messages"""
    logger.debug(message, **kwargs)


def log_warning(message: str, **kwargs) -> None:
    """Log warning messages"""
    logger.warning(message, **kwargs)
