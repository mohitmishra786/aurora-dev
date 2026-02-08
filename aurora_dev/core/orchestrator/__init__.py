"""
Orchestrator Engine for AURORA-DEV.

This package provides the main orchestration engine that coordinates
agent execution, manages workflows, and handles project lifecycle.
"""
from aurora_dev.core.orchestrator.engine import OrchestrationEngine
from aurora_dev.core.orchestrator.scheduler import TaskScheduler
from aurora_dev.core.orchestrator.lifecycle import AgentLifecycleManager

__all__ = [
    "OrchestrationEngine",
    "TaskScheduler",
    "AgentLifecycleManager",
]
