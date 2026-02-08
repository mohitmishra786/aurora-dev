"""
State Machine for AURORA-DEV workflow management.

Provides state machine logic for managing workflow transitions,
state persistence, and event handling.
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

import redis

from aurora_dev.core.config import get_settings
from aurora_dev.core.state_machine.states import (
    TransitionRule,
    TransitionType,
    WorkflowPhase,
    WorkflowState,
    get_default_transitions,
)


logger = logging.getLogger(__name__)


@dataclass
class TransitionEvent:
    """Event emitted on state transitions.
    
    Attributes:
        workflow_id: Workflow identifier.
        from_phase: Source phase.
        to_phase: Target phase.
        timestamp: Event timestamp.
        trigger: What triggered the transition.
        data: Additional event data.
    """
    
    workflow_id: str
    from_phase: WorkflowPhase
    to_phase: WorkflowPhase
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trigger: str = "automatic"
    data: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "workflow_id": self.workflow_id,
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger,
            "data": self.data,
        }


EventHandler = Callable[[TransitionEvent], None]


class StateMachine:
    """State machine for workflow management.
    
    Manages workflow states, validates transitions, and
    persists state to Redis.
    
    Attributes:
        workflows: Active workflow states.
        rules: Transition rules.
        event_handlers: Event handlers by phase.
    """
    
    def __init__(self, persist: bool = True) -> None:
        """Initialize the state machine.
        
        Args:
            persist: Whether to persist state to Redis.
        """
        self.workflows: dict[str, WorkflowState] = {}
        self.rules: dict[tuple[WorkflowPhase, WorkflowPhase], TransitionRule] = {}
        self.event_handlers: dict[WorkflowPhase, list[EventHandler]] = {}
        self._persist = persist
        self._redis: Optional[redis.Redis] = None
        self._prefix = "aurora:workflow:"
        
        self._load_default_rules()
        
        if persist:
            self._init_redis()
        
        logger.info("StateMachine initialized")
    
    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            settings = get_settings()
            self._redis = redis.from_url(
                settings.redis.url,
                decode_responses=True,
            )
        except Exception as e:
            logger.warning(f"Redis connection failed, persistence disabled: {e}")
            self._persist = False
    
    def _load_default_rules(self) -> None:
        """Load default transition rules."""
        for rule in get_default_transitions():
            self.add_rule(rule)
    
    def add_rule(self, rule: TransitionRule) -> None:
        """Add a transition rule.
        
        Args:
            rule: Transition rule to add.
        """
        key = (rule.from_phase, rule.to_phase)
        self.rules[key] = rule
        logger.debug(f"Added rule: {rule.from_phase.value} -> {rule.to_phase.value}")
    
    def remove_rule(
        self,
        from_phase: WorkflowPhase,
        to_phase: WorkflowPhase,
    ) -> bool:
        """Remove a transition rule.
        
        Args:
            from_phase: Source phase.
            to_phase: Target phase.
            
        Returns:
            True if rule was removed.
        """
        key = (from_phase, to_phase)
        if key in self.rules:
            del self.rules[key]
            return True
        return False
    
    def create_workflow(
        self,
        workflow_id: Optional[str] = None,
        initial_data: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> WorkflowState:
        """Create a new workflow.
        
        Args:
            workflow_id: Optional workflow ID.
            initial_data: Initial workflow data.
            metadata: Additional metadata.
            
        Returns:
            Created workflow state.
        """
        wf_id = workflow_id or str(uuid4())
        
        state = WorkflowState(
            workflow_id=wf_id,
            data=initial_data or {},
            metadata=metadata or {},
        )
        
        self.workflows[wf_id] = state
        
        if self._persist:
            self._save_state(state)
        
        logger.info(f"Created workflow: {wf_id}")
        
        return state
    
    def get_workflow(
        self,
        workflow_id: str,
    ) -> Optional[WorkflowState]:
        """Get a workflow state.
        
        Args:
            workflow_id: Workflow identifier.
            
        Returns:
            Workflow state or None.
        """
        if workflow_id in self.workflows:
            return self.workflows[workflow_id]
        
        if self._persist:
            state = self._load_state(workflow_id)
            if state:
                self.workflows[workflow_id] = state
                return state
        
        return None
    
    def can_transition(
        self,
        workflow_id: str,
        to_phase: WorkflowPhase,
    ) -> bool:
        """Check if a transition is allowed.
        
        Args:
            workflow_id: Workflow identifier.
            to_phase: Target phase.
            
        Returns:
            True if transition is allowed.
        """
        state = self.get_workflow(workflow_id)
        if state is None:
            return False
        
        if state.is_terminal:
            return False
        
        key = (state.current_phase, to_phase)
        rule = self.rules.get(key)
        
        if rule is None:
            return False
        
        return rule.can_transition(state.data)
    
    def transition(
        self,
        workflow_id: str,
        to_phase: WorkflowPhase,
        trigger: str = "automatic",
        data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Perform a state transition.
        
        Args:
            workflow_id: Workflow identifier.
            to_phase: Target phase.
            trigger: What triggered the transition.
            data: Additional transition data.
            
        Returns:
            True if transition was successful.
            
        Raises:
            ValueError: If transition is not allowed.
        """
        state = self.get_workflow(workflow_id)
        if state is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        from_phase = state.current_phase
        
        if not self.can_transition(workflow_id, to_phase):
            logger.warning(
                f"Invalid transition: {from_phase.value} -> {to_phase.value}"
            )
            return False
        
        key = (from_phase, to_phase)
        rule = self.rules[key]
        
        if data:
            state.data.update(data)
        
        state.transition_to(to_phase)
        
        if self._persist:
            self._save_state(state)
        
        event = TransitionEvent(
            workflow_id=workflow_id,
            from_phase=from_phase,
            to_phase=to_phase,
            trigger=trigger,
            data=data or {},
        )
        
        self._emit_event(event)
        
        if rule.on_transition:
            try:
                rule.on_transition(state.data)
            except Exception as e:
                logger.error(f"Transition callback error: {e}")
        
        logger.info(
            f"Workflow {workflow_id}: {from_phase.value} -> {to_phase.value}"
        )
        
        return True
    
    def force_transition(
        self,
        workflow_id: str,
        to_phase: WorkflowPhase,
        reason: str = "forced",
    ) -> bool:
        """Force a state transition without validation.
        
        Args:
            workflow_id: Workflow identifier.
            to_phase: Target phase.
            reason: Reason for forced transition.
            
        Returns:
            True if transition was successful.
        """
        state = self.get_workflow(workflow_id)
        if state is None:
            return False
        
        from_phase = state.current_phase
        state.transition_to(to_phase)
        
        if self._persist:
            self._save_state(state)
        
        event = TransitionEvent(
            workflow_id=workflow_id,
            from_phase=from_phase,
            to_phase=to_phase,
            trigger=f"forced: {reason}",
        )
        
        self._emit_event(event)
        
        logger.warning(
            f"Forced transition {workflow_id}: {from_phase.value} -> {to_phase.value}"
        )
        
        return True
    
    def fail_workflow(
        self,
        workflow_id: str,
        error: str,
    ) -> bool:
        """Mark a workflow as failed.
        
        Args:
            workflow_id: Workflow identifier.
            error: Error message.
            
        Returns:
            True if workflow was marked as failed.
        """
        state = self.get_workflow(workflow_id)
        if state is None:
            return False
        
        state.set_error(error)
        
        if self._persist:
            self._save_state(state)
        
        logger.error(f"Workflow {workflow_id} failed: {error}")
        
        return True
    
    def cancel_workflow(
        self,
        workflow_id: str,
    ) -> bool:
        """Cancel a workflow.
        
        Args:
            workflow_id: Workflow identifier.
            
        Returns:
            True if workflow was cancelled.
        """
        return self.force_transition(
            workflow_id,
            WorkflowPhase.CANCELLED,
            reason="user_cancelled",
        )
    
    def on_enter(
        self,
        phase: WorkflowPhase,
        handler: EventHandler,
    ) -> None:
        """Register a handler for entering a phase.
        
        Args:
            phase: Phase to handle.
            handler: Event handler function.
        """
        if phase not in self.event_handlers:
            self.event_handlers[phase] = []
        self.event_handlers[phase].append(handler)
    
    def _emit_event(self, event: TransitionEvent) -> None:
        """Emit a transition event.
        
        Args:
            event: Transition event.
        """
        handlers = self.event_handlers.get(event.to_phase, [])
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def get_valid_transitions(
        self,
        workflow_id: str,
    ) -> list[WorkflowPhase]:
        """Get valid next phases for a workflow.
        
        Args:
            workflow_id: Workflow identifier.
            
        Returns:
            List of valid next phases.
        """
        state = self.get_workflow(workflow_id)
        if state is None or state.is_terminal:
            return []
        
        valid = []
        
        for (from_phase, to_phase), rule in self.rules.items():
            if from_phase == state.current_phase:
                if rule.can_transition(state.data):
                    valid.append(to_phase)
        
        return valid
    
    def update_data(
        self,
        workflow_id: str,
        data: dict[str, Any],
    ) -> bool:
        """Update workflow data.
        
        Args:
            workflow_id: Workflow identifier.
            data: Data to update.
            
        Returns:
            True if data was updated.
        """
        state = self.get_workflow(workflow_id)
        if state is None:
            return False
        
        state.data.update(data)
        state.updated_at = datetime.now(timezone.utc)
        
        if self._persist:
            self._save_state(state)
        
        return True
    
    def _save_state(self, state: WorkflowState) -> None:
        """Save state to Redis.
        
        Args:
            state: State to save.
        """
        if self._redis is None:
            return
        
        try:
            key = f"{self._prefix}{state.workflow_id}"
            self._redis.setex(
                key,
                86400 * 7,
                json.dumps(state.to_dict()),
            )
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_state(
        self,
        workflow_id: str,
    ) -> Optional[WorkflowState]:
        """Load state from Redis.
        
        Args:
            workflow_id: Workflow identifier.
            
        Returns:
            Loaded state or None.
        """
        if self._redis is None:
            return None
        
        try:
            key = f"{self._prefix}{workflow_id}"
            data = self._redis.get(key)
            
            if data is None:
                return None
            
            return WorkflowState.from_dict(json.loads(data))
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def list_workflows(
        self,
        phase: Optional[WorkflowPhase] = None,
        active_only: bool = False,
    ) -> list[WorkflowState]:
        """List workflows with optional filtering.
        
        Args:
            phase: Filter by phase.
            active_only: Only return active workflows.
            
        Returns:
            List of matching workflows.
        """
        workflows = list(self.workflows.values())
        
        if phase:
            workflows = [w for w in workflows if w.current_phase == phase]
        
        if active_only:
            workflows = [w for w in workflows if not w.is_terminal]
        
        return workflows
    
    def get_statistics(self) -> dict[str, Any]:
        """Get state machine statistics.
        
        Returns:
            Dictionary with statistics.
        """
        workflows = list(self.workflows.values())
        
        by_phase = {}
        for wf in workflows:
            phase = wf.current_phase.value
            by_phase[phase] = by_phase.get(phase, 0) + 1
        
        active = sum(1 for w in workflows if not w.is_terminal)
        completed = sum(
            1 for w in workflows
            if w.current_phase == WorkflowPhase.COMPLETED
        )
        failed = sum(
            1 for w in workflows
            if w.current_phase == WorkflowPhase.FAILED
        )
        
        return {
            "total_workflows": len(workflows),
            "active_workflows": active,
            "completed_workflows": completed,
            "failed_workflows": failed,
            "by_phase": by_phase,
            "rules_count": len(self.rules),
        }


if __name__ == "__main__":
    machine = StateMachine(persist=False)
    
    workflow = machine.create_workflow()
    print(f"Created: {workflow.workflow_id}")
    print(f"Phase: {workflow.current_phase.value}")
    
    valid = machine.get_valid_transitions(workflow.workflow_id)
    print(f"Valid transitions: {[p.value for p in valid]}")
    
    machine.transition(workflow.workflow_id, WorkflowPhase.REQUIREMENTS)
    print(f"After transition: {workflow.current_phase.value}")
    
    print(f"Stats: {machine.get_statistics()}")
