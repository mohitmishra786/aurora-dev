"""
Core package for AURORA-DEV.

Provides configuration, logging, and other core utilities.
"""
from aurora_dev.core.config import Settings, get_settings
from aurora_dev.core.logging import (
    get_agent_logger,
    get_logger,
    setup_logging,
)

__all__ = [
    "get_settings",
    "Settings",
    "setup_logging",
    "get_logger",
    "get_agent_logger",
]
