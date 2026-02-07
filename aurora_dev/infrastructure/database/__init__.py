"""
Database infrastructure package for AURORA-DEV.

Exports database connection, session management, and models.
"""
from aurora_dev.infrastructure.database.connection import (
    check_health,
    close_engine,
    get_engine,
    get_session,
    get_session_factory,
)
from aurora_dev.infrastructure.database.models import (
    AgentSession,
    AgentSessionStatus,
    ArchitectureDecision,
    Base,
    Project,
    Reflection,
    Task,
    TaskStatus,
    TimestampMixin,
)

__all__ = [
    # Connection
    "get_engine",
    "get_session_factory",
    "get_session",
    "check_health",
    "close_engine",
    # Models
    "Base",
    "TimestampMixin",
    "Project",
    "Task",
    "TaskStatus",
    "AgentSession",
    "AgentSessionStatus",
    "ArchitectureDecision",
    "Reflection",
]
