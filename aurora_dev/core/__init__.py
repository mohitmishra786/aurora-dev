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
from aurora_dev.core.reflexion import (
    ReflexionEngine,
    Reflection,
    ReflexionTrigger,
    TaskContext,
    AttemptResult,
    RetryContext,
)
from aurora_dev.core.project_manager import (
    ProjectManager,
    Project,
    ProjectConfig,
    ProjectContext,
    ProjectStatus,
    get_project_manager,
)

__all__ = [
    "get_settings",
    "Settings",
    "setup_logging",
    "get_logger",
    "get_agent_logger",
    # Reflexion
    "ReflexionEngine",
    "Reflection",
    "ReflexionTrigger",
    "TaskContext",
    "AttemptResult",
    "RetryContext",
    # Project management
    "ProjectManager",
    "Project",
    "ProjectConfig",
    "ProjectContext",
    "ProjectStatus",
    "get_project_manager",
]
