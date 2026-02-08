"""
State Machine for AURORA-DEV workflow execution.

This package provides a state machine for managing workflow phases,
state transitions, and state persistence.
"""
from aurora_dev.core.state_machine.states import (
    WorkflowPhase,
    WorkflowState,
    TransitionRule,
)
from aurora_dev.core.state_machine.machine import StateMachine

__all__ = [
    "WorkflowPhase",
    "WorkflowState",
    "TransitionRule",
    "StateMachine",
]
