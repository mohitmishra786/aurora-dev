"""
AURORA-DEV: Neural EXecution Unified System - Full Orchestration & Recursive Generation Environment.

A fully autonomous, self-improving multi-agent software development system.
"""

__version__ = "0.1.0"
__author__ = "AURORA-DEV Team"
__description__ = "Multi-agent autonomous software development system"

from aurora_dev.core import get_logger, get_settings, setup_logging

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "get_settings",
    "setup_logging",
    "get_logger",
]
