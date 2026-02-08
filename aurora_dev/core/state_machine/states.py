"""
State definitions for AURORA-DEV workflow state machine.

Provides workflow phases, state representations, and transition rules
for managing complex workflow execution.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class WorkflowPhase(Enum):
    """Workflow execution phases.
    
    Defines the phases of a development workflow, including
    human-in-the-loop control states.
    """
    
    # Active workflow phases
    IDLE = "idle"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    
    # Human-in-the-loop control states
    PAUSED = "paused"                      # Workflow paused for human review
    AWAITING_APPROVAL = "awaiting_approval"  # Blocked on human approval
    
    # Terminal states
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransitionType(Enum):
    """Types of state transitions.
    
    Categorizes how transitions occur, including
    human-in-the-loop approval types.
    """
    
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    CONDITIONAL = "conditional"
    TIMEOUT = "timeout"
    ERROR = "error"
    
    # Human-in-the-loop transition types
    HUMAN_APPROVAL = "human_approval"  # Requires human sign-off to proceed
    BREAKPOINT = "breakpoint"          # Automatic pause at configured points


@dataclass
class TransitionRule:
    """Rule defining a valid state transition.
    
    Attributes:
        from_phase: Source phase.
        to_phase: Target phase.
        transition_type: Type of transition.
        condition: Optional condition function.
        on_transition: Optional callback on transition.
        timeout_seconds: Optional timeout for automatic transition.
        description: Human-readable description.
    """
    
    from_phase: WorkflowPhase
    to_phase: WorkflowPhase
    transition_type: TransitionType = TransitionType.AUTOMATIC
    condition: Optional[Callable[[dict], bool]] = None
    on_transition: Optional[Callable[[dict], None]] = None
    timeout_seconds: Optional[int] = None
    description: str = ""
    
    def can_transition(self, context: dict[str, Any]) -> bool:
        """Check if transition is allowed.
        
        Args:
            context: Current workflow context.
            
        Returns:
            True if transition is allowed.
        """
        if self.condition is None:
            return True
        return self.condition(context)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "transition_type": self.transition_type.value,
            "timeout_seconds": self.timeout_seconds,
            "description": self.description,
        }


@dataclass
class WorkflowState:
    """Current state of a workflow.
    
    Attributes:
        workflow_id: Unique workflow identifier.
        current_phase: Current workflow phase.
        previous_phase: Previous workflow phase.
        phase_history: List of phase transitions.
        data: Workflow data/context.
        created_at: State creation timestamp.
        updated_at: Last update timestamp.
        phase_started_at: Current phase start timestamp.
        error: Optional error message.
        metadata: Additional metadata.
    """
    
    workflow_id: str
    current_phase: WorkflowPhase = WorkflowPhase.IDLE
    previous_phase: Optional[WorkflowPhase] = None
    phase_history: list[tuple[WorkflowPhase, datetime]] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    phase_started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_terminal(self) -> bool:
        """Check if workflow is in a terminal state.
        
        Returns:
            True if workflow has ended.
        """
        return self.current_phase in {
            WorkflowPhase.COMPLETED,
            WorkflowPhase.FAILED,
            WorkflowPhase.CANCELLED,
        }
    
    @property
    def is_paused(self) -> bool:
        """Check if workflow is paused for human intervention.
        
        Returns:
            True if workflow is paused or awaiting approval.
        """
        return self.current_phase in {
            WorkflowPhase.PAUSED,
            WorkflowPhase.AWAITING_APPROVAL,
        }
    
    @property
    def phase_duration_seconds(self) -> float:
        """Calculate current phase duration.
        
        Returns:
            Duration in seconds.
        """
        return (datetime.now(timezone.utc) - self.phase_started_at).total_seconds()
    
    @property
    def total_duration_seconds(self) -> float:
        """Calculate total workflow duration.
        
        Returns:
            Duration in seconds.
        """
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()
    
    def transition_to(self, new_phase: WorkflowPhase) -> None:
        """Transition to a new phase.
        
        Args:
            new_phase: Target phase.
        """
        now = datetime.now(timezone.utc)
        
        self.phase_history.append((self.current_phase, now))
        self.previous_phase = self.current_phase
        self.current_phase = new_phase
        self.phase_started_at = now
        self.updated_at = now
    
    def set_error(self, error: str) -> None:
        """Set error and transition to failed state.
        
        Args:
            error: Error message.
        """
        self.error = error
        self.transition_to(WorkflowPhase.FAILED)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "workflow_id": self.workflow_id,
            "current_phase": self.current_phase.value,
            "previous_phase": self.previous_phase.value if self.previous_phase else None,
            "phase_history": [
                {"phase": p.value, "timestamp": t.isoformat()}
                for p, t in self.phase_history
            ],
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "phase_started_at": self.phase_started_at.isoformat(),
            "phase_duration_seconds": self.phase_duration_seconds,
            "total_duration_seconds": self.total_duration_seconds,
            "is_terminal": self.is_terminal,
            "is_paused": self.is_paused,
            "error": self.error,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Create from dictionary.
        
        Args:
            data: Dictionary data.
            
        Returns:
            WorkflowState instance.
        """
        history = [
            (WorkflowPhase(item["phase"]), datetime.fromisoformat(item["timestamp"]))
            for item in data.get("phase_history", [])
        ]
        
        return cls(
            workflow_id=data["workflow_id"],
            current_phase=WorkflowPhase(data.get("current_phase", "idle")),
            previous_phase=WorkflowPhase(data["previous_phase"]) if data.get("previous_phase") else None,
            phase_history=history,
            data=data.get("data", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(timezone.utc),
            phase_started_at=datetime.fromisoformat(data["phase_started_at"]) if data.get("phase_started_at") else datetime.now(timezone.utc),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


def get_default_transitions() -> list[TransitionRule]:
    """Get default workflow transition rules.
    
    Returns:
        List of default transition rules.
    """
    return [
        TransitionRule(
            from_phase=WorkflowPhase.IDLE,
            to_phase=WorkflowPhase.REQUIREMENTS,
            description="Start workflow with requirements gathering",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.REQUIREMENTS,
            to_phase=WorkflowPhase.DESIGN,
            description="Requirements complete, proceed to design",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.DESIGN,
            to_phase=WorkflowPhase.IMPLEMENTATION,
            description="Design complete, proceed to implementation",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.IMPLEMENTATION,
            to_phase=WorkflowPhase.TESTING,
            description="Implementation complete, proceed to testing",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.TESTING,
            to_phase=WorkflowPhase.CODE_REVIEW,
            description="Testing complete, proceed to code review",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.CODE_REVIEW,
            to_phase=WorkflowPhase.SECURITY_AUDIT,
            description="Code review complete, proceed to security audit",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.SECURITY_AUDIT,
            to_phase=WorkflowPhase.DEPLOYMENT,
            description="Security audit passed, proceed to deployment",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.DEPLOYMENT,
            to_phase=WorkflowPhase.COMPLETED,
            description="Deployment complete, workflow finished",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.TESTING,
            to_phase=WorkflowPhase.IMPLEMENTATION,
            transition_type=TransitionType.CONDITIONAL,
            description="Tests failed, return to implementation",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.CODE_REVIEW,
            to_phase=WorkflowPhase.IMPLEMENTATION,
            transition_type=TransitionType.CONDITIONAL,
            description="Review requested changes, return to implementation",
        ),
    ]


def get_collaborative_transitions() -> list[TransitionRule]:
    """Get transition rules for collaborative (human-in-the-loop) mode.
    
    Includes breakpoints that pause workflow for human review
    at key decision points.
    
    Returns:
        List of collaborative mode transition rules.
    """
    base_transitions = get_default_transitions()
    
    # Add breakpoint transitions for collaborative mode
    collaborative_transitions = [
        # Breakpoint: After design phase for architecture review
        TransitionRule(
            from_phase=WorkflowPhase.DESIGN,
            to_phase=WorkflowPhase.AWAITING_APPROVAL,
            transition_type=TransitionType.BREAKPOINT,
            description="Pause for architecture review before implementation",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.AWAITING_APPROVAL,
            to_phase=WorkflowPhase.IMPLEMENTATION,
            transition_type=TransitionType.HUMAN_APPROVAL,
            condition=lambda ctx: ctx.get("phase_before_pause") == "design",
            description="Resume implementation after architecture approval",
        ),
        
        # Breakpoint: Pre-deployment approval
        TransitionRule(
            from_phase=WorkflowPhase.SECURITY_AUDIT,
            to_phase=WorkflowPhase.AWAITING_APPROVAL,
            transition_type=TransitionType.BREAKPOINT,
            description="Pause for deployment approval after security audit",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.AWAITING_APPROVAL,
            to_phase=WorkflowPhase.DEPLOYMENT,
            transition_type=TransitionType.HUMAN_APPROVAL,
            condition=lambda ctx: ctx.get("phase_before_pause") == "security_audit",
            description="Resume deployment after approval",
        ),
        
        # Manual pause from any active phase
        TransitionRule(
            from_phase=WorkflowPhase.REQUIREMENTS,
            to_phase=WorkflowPhase.PAUSED,
            transition_type=TransitionType.MANUAL,
            description="Manually pause during requirements",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.IMPLEMENTATION,
            to_phase=WorkflowPhase.PAUSED,
            transition_type=TransitionType.MANUAL,
            description="Manually pause during implementation",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.TESTING,
            to_phase=WorkflowPhase.PAUSED,
            transition_type=TransitionType.MANUAL,
            description="Manually pause during testing",
        ),
        
        # Resume from paused state
        TransitionRule(
            from_phase=WorkflowPhase.PAUSED,
            to_phase=WorkflowPhase.REQUIREMENTS,
            transition_type=TransitionType.HUMAN_APPROVAL,
            condition=lambda ctx: ctx.get("resume_phase") == "requirements",
            description="Resume to requirements after pause",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.PAUSED,
            to_phase=WorkflowPhase.IMPLEMENTATION,
            transition_type=TransitionType.HUMAN_APPROVAL,
            condition=lambda ctx: ctx.get("resume_phase") == "implementation",
            description="Resume to implementation after pause",
        ),
        TransitionRule(
            from_phase=WorkflowPhase.PAUSED,
            to_phase=WorkflowPhase.TESTING,
            transition_type=TransitionType.HUMAN_APPROVAL,
            condition=lambda ctx: ctx.get("resume_phase") == "testing",
            description="Resume to testing after pause",
        ),
        
        # Rejection from awaiting approval
        TransitionRule(
            from_phase=WorkflowPhase.AWAITING_APPROVAL,
            to_phase=WorkflowPhase.CANCELLED,
            transition_type=TransitionType.HUMAN_APPROVAL,
            condition=lambda ctx: ctx.get("approval_rejected", False),
            description="Workflow cancelled due to rejection",
        ),
    ]
    
    return base_transitions + collaborative_transitions


if __name__ == "__main__":
    state = WorkflowState(workflow_id="wf-123")
    print(f"Initial state: {state.current_phase.value}")
    
    state.transition_to(WorkflowPhase.REQUIREMENTS)
    print(f"After transition: {state.current_phase.value}")
    print(f"Previous: {state.previous_phase.value if state.previous_phase else None}")
    
    print(f"State dict: {state.to_dict()}")
