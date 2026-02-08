"""
Orchestrator Engine for AURORA-DEV.

This package provides the main orchestration engine that coordinates
agent execution, manages workflows, and handles project lifecycle.
"""
from aurora_dev.core.orchestrator.engine import OrchestrationEngine
from aurora_dev.core.orchestrator.scheduler import TaskScheduler
from aurora_dev.core.orchestrator.lifecycle import AgentLifecycleManager
from aurora_dev.core.orchestrator.dual_mode import (
    DualModeOrchestrator,
    ExecutionMode,
    BreakpointConfig,
    Breakpoint,
    ExecutionResult,
)

__all__ = [
    "OrchestrationEngine",
    "TaskScheduler",
    "AgentLifecycleManager",
    "DualModeOrchestrator",
    "ExecutionMode",
    "BreakpointConfig",
    "Breakpoint",
    "ExecutionResult",
]
