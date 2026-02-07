"""
Structured logging infrastructure for AURORA-DEV.

This module provides a centralized logging system with JSON formatting,
contextual fields, and support for both console and file handlers.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from aurora_dev.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging output."""

    def __init__(self, include_timestamp: bool = True) -> None:
        """
        Initialize the JSON formatter.

        Args:
            include_timestamp: Whether to include timestamp in output.
        """
        super().__init__()
        self.include_timestamp = include_timestamp

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON string representation of the log record.
        """
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if self.include_timestamp:
            log_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add extra fields from the record
        if hasattr(record, "agent_id"):
            log_data["agent_id"] = record.agent_id
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "project_id"):
            log_data["project_id"] = record.project_id

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development."""

    def __init__(self, include_timestamp: bool = True) -> None:
        """
        Initialize the text formatter.

        Args:
            include_timestamp: Whether to include timestamp in output.
        """
        fmt = ""
        if include_timestamp:
            fmt += "%(asctime)s "
        fmt += "[%(levelname)s] %(name)s - %(message)s"
        super().__init__(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")


class ContextualAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual fields to log records."""

    def process(
        self, msg: str, kwargs: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """
        Process the logging message and keyword arguments.

        Args:
            msg: The log message.
            kwargs: Keyword arguments for logging.

        Returns:
            Tuple of processed message and kwargs.
        """
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    include_timestamp: bool = True,
) -> None:
    """
    Configure the logging infrastructure.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional file path for file logging.
        log_format: Log format (json or text).
        include_timestamp: Whether to include timestamps.
    """
    settings = get_settings()

    # Use provided values or fall back to settings
    level = level or settings.logging.level
    log_file = log_file or settings.logging.file
    log_format = log_format or settings.logging.format
    include_timestamp = include_timestamp and settings.logging.include_timestamp

    # Get root logger for aurora_dev
    root_logger = logging.getLogger("aurora_dev")
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter based on format type
    if log_format.lower() == "json":
        formatter: logging.Formatter = JSONFormatter(include_timestamp)
    else:
        formatter = TextFormatter(include_timestamp)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Prevent propagation to root logger
    root_logger.propagate = False


def get_logger(
    name: str,
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> logging.LoggerAdapter:
    """
    Get a contextual logger for a specific component.

    Args:
        name: Logger name (typically module or agent name).
        agent_id: Optional agent identifier.
        task_id: Optional task identifier.
        session_id: Optional session identifier.
        project_id: Optional project identifier.

    Returns:
        A logger adapter with contextual information.
    """
    logger = logging.getLogger(f"aurora_dev.{name}")

    # Build extra context
    extra: dict[str, Any] = {}
    if agent_id:
        extra["agent_id"] = agent_id
    if task_id:
        extra["task_id"] = task_id
    if session_id:
        extra["session_id"] = session_id
    if project_id:
        extra["project_id"] = project_id

    return ContextualAdapter(logger, extra)


def get_agent_logger(
    agent_name: str,
    agent_id: str,
    task_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> logging.LoggerAdapter:
    """
    Get a logger specifically configured for an agent.

    Args:
        agent_name: Name of the agent (e.g., 'maestro', 'backend').
        agent_id: Unique identifier for this agent instance.
        task_id: Optional current task identifier.
        session_id: Optional session identifier.

    Returns:
        A logger adapter configured for the agent.
    """
    return get_logger(
        f"agents.{agent_name}",
        agent_id=agent_id,
        task_id=task_id,
        session_id=session_id,
    )


# Initialize logging on module import if settings are available
try:
    setup_logging()
except Exception:
    # Settings may not be available during testing
    pass
