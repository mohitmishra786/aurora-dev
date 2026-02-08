"""
Dual-Mode Orchestrator for AURORA-DEV.

Provides orchestration with support for both autonomous and collaborative
(human-in-the-loop) execution modes with configurable breakpoints.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from aurora_dev.core.state_machine.machine import StateMachine
from aurora_dev.core.state_machine.states import (
    WorkflowPhase,
    WorkflowState,
    get_collaborative_transitions,
    get_default_transitions,
)


logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution mode for the orchestrator.
    
    AUTONOMOUS: Full automatic execution without human intervention.
    COLLABORATIVE: Pauses at configured breakpoints for human review.
    """
    
    AUTONOMOUS = "autonomous"
    COLLABORATIVE = "collaborative"


class Breakpoint(Enum):
    """Predefined breakpoint locations in the workflow.
    
    These checkpoints pause execution for human review in collaborative mode.
    """
    
    POST_DESIGN = "post_design"           # After architecture/design phase
    POST_PLAN = "post_plan"               # After task planning
    PRE_TESTING = "pre_testing"           # Before running tests
    PRE_DEPLOYMENT = "pre_deployment"     # Before deployment
    ON_FAILURE = "on_failure"             # When any phase fails


@dataclass
class BreakpointConfig:
    """Configuration for workflow breakpoints.
    
    Determines which points in the workflow require human approval
    before proceeding.
    
    Attributes:
        post_design: Pause after design/architecture phase.
        post_plan: Pause after task planning.
        pre_testing: Pause before running tests.
        pre_deployment: Pause before deployment.
        on_failure: Pause when a phase fails.
        custom_phases: Additional phases to pause at.
    """
    
    post_design: bool = True
    post_plan: bool = False
    pre_testing: bool = False
    pre_deployment: bool = True
    on_failure: bool = True
    custom_phases: list[WorkflowPhase] = field(default_factory=list)
    
    def should_pause_at(self, phase: WorkflowPhase) -> Optional[Breakpoint]:
        """Check if workflow should pause at the given phase.
        
        Args:
            phase: The completed phase to check.
            
        Returns:
            The Breakpoint that applies, or None if no pause needed.
        """
        if phase == WorkflowPhase.DESIGN and self.post_design:
            return Breakpoint.POST_DESIGN
        if phase == WorkflowPhase.REQUIREMENTS and self.post_plan:
            return Breakpoint.POST_PLAN
        if phase == WorkflowPhase.IMPLEMENTATION and self.pre_testing:
            return Breakpoint.PRE_TESTING
        if phase == WorkflowPhase.SECURITY_AUDIT and self.pre_deployment:
            return Breakpoint.PRE_DEPLOYMENT
        if phase == WorkflowPhase.FAILED and self.on_failure:
            return Breakpoint.ON_FAILURE
        if phase in self.custom_phases:
            return Breakpoint.POST_DESIGN  # Generic breakpoint
        return None


@dataclass
class ExecutionResult:
    """Result from dual-mode orchestration execution.
    
    Attributes:
        workflow_id: Workflow identifier.
        status: Final status (completed, paused, failed).
        current_phase: Current workflow phase.
        is_paused: Whether workflow is paused for approval.
        checkpoint: If paused, the breakpoint that caused the pause.
        outputs: Any outputs from the execution.
        error: Error message if failed.
    """
    
    workflow_id: str
    status: str
    current_phase: WorkflowPhase
    is_paused: bool = False
    checkpoint: Optional[Breakpoint] = None
    outputs: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "current_phase": self.current_phase.value,
            "is_paused": self.is_paused,
            "checkpoint": self.checkpoint.value if self.checkpoint else None,
            "outputs": self.outputs,
            "error": self.error,
        }


NotificationHandler = Callable[[str, WorkflowState, Breakpoint], None]


class DualModeOrchestrator:
    """Orchestrator supporting autonomous and collaborative execution modes.
    
    In AUTONOMOUS mode, workflows execute fully automatically with
    self-correction on failures.
    
    In COLLABORATIVE mode, workflows pause at configured breakpoints
    to allow human review and approval before proceeding.
    
    Attributes:
        mode: Current execution mode.
        breakpoints: Breakpoint configuration.
        state_machine: Workflow state machine.
        notification_handler: Optional callback for human notification.
    """
    
    def __init__(
        self,
        mode: ExecutionMode = ExecutionMode.AUTONOMOUS,
        breakpoints: Optional[BreakpointConfig] = None,
        state_machine: Optional[StateMachine] = None,
        notification_handler: Optional[NotificationHandler] = None,
        persist: bool = True,
    ) -> None:
        """Initialize the dual-mode orchestrator.
        
        Args:
            mode: Execution mode (autonomous or collaborative).
            breakpoints: Configuration for workflow breakpoints.
            state_machine: Optional existing state machine instance.
            notification_handler: Callback when human notification is needed.
            persist: Whether to persist state to Redis.
        """
        self.mode = mode
        self.breakpoints = breakpoints or BreakpointConfig()
        self.notification_handler = notification_handler
        
        # Use existing or create new state machine
        self.state_machine = state_machine or StateMachine(persist=persist)
        
        # Load collaborative transition rules if in collaborative mode
        if mode == ExecutionMode.COLLABORATIVE:
            self._load_collaborative_rules()
        
        logger.info(f"DualModeOrchestrator initialized in {mode.value} mode")
    
    def _load_collaborative_rules(self) -> None:
        """Load collaborative-mode transition rules into state machine."""
        for rule in get_collaborative_transitions():
            self.state_machine.add_rule(rule)
        logger.debug("Loaded collaborative transition rules")
    
    async def create_workflow(
        self,
        task_description: str,
        project_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> WorkflowState:
        """Create a new workflow for execution.
        
        Args:
            task_description: Description of what the workflow should accomplish.
            project_id: Optional project identifier.
            metadata: Additional workflow metadata.
            
        Returns:
            Created workflow state.
        """
        initial_data = {
            "task_description": task_description,
            "project_id": project_id,
            "execution_mode": self.mode.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        workflow_metadata = metadata or {}
        workflow_metadata["orchestrator_mode"] = self.mode.value
        
        state = self.state_machine.create_workflow(
            initial_data=initial_data,
            metadata=workflow_metadata,
        )
        
        logger.info(f"Created workflow {state.workflow_id} in {self.mode.value} mode")
        return state
    
    async def execute(
        self,
        workflow_id: str,
        phase_executor: Optional[Callable[[WorkflowPhase, dict], dict]] = None,
    ) -> ExecutionResult:
        """Execute a workflow based on configured mode.
        
        Args:
            workflow_id: Workflow identifier.
            phase_executor: Optional function to execute each phase.
            
        Returns:
            Execution result with status and any outputs.
        """
        if self.mode == ExecutionMode.AUTONOMOUS:
            return await self._execute_autonomous(workflow_id, phase_executor)
        return await self._execute_collaborative(workflow_id, phase_executor)
    
    async def _execute_autonomous(
        self,
        workflow_id: str,
        phase_executor: Optional[Callable[[WorkflowPhase, dict], dict]] = None,
    ) -> ExecutionResult:
        """Execute workflow in autonomous mode without human intervention.
        
        Args:
            workflow_id: Workflow identifier.
            phase_executor: Optional function to execute each phase.
            
        Returns:
            Execution result.
        """
        state = self.state_machine.get_workflow(workflow_id)
        if state is None:
            return ExecutionResult(
                workflow_id=workflow_id,
                status="error",
                current_phase=WorkflowPhase.IDLE,
                error="Workflow not found",
            )
        
        outputs = {}
        
        while not state.is_terminal:
            # Get valid next phases
            valid_transitions = self.state_machine.get_valid_transitions(workflow_id)
            
            if not valid_transitions:
                logger.warning(f"No valid transitions from {state.current_phase.value}")
                break
            
            # Select next phase (first valid for autonomous)
            next_phase = valid_transitions[0]
            
            # Execute phase if executor provided
            if phase_executor:
                try:
                    phase_output = await asyncio.to_thread(
                        phase_executor, state.current_phase, state.data
                    )
                    outputs[state.current_phase.value] = phase_output
                    state.data.update(phase_output)
                except Exception as e:
                    logger.error(f"Phase execution failed: {e}")
                    self.state_machine.fail_workflow(workflow_id, str(e))
                    state = self.state_machine.get_workflow(workflow_id)
                    break
            
            # Transition to next phase
            success = self.state_machine.transition(
                workflow_id, next_phase, trigger="autonomous"
            )
            
            if not success:
                logger.error(f"Transition to {next_phase.value} failed")
                break
            
            state = self.state_machine.get_workflow(workflow_id)
        
        return ExecutionResult(
            workflow_id=workflow_id,
            status="completed" if state.current_phase == WorkflowPhase.COMPLETED else state.current_phase.value,
            current_phase=state.current_phase,
            outputs=outputs,
            error=state.error,
        )
    
    async def _execute_collaborative(
        self,
        workflow_id: str,
        phase_executor: Optional[Callable[[WorkflowPhase, dict], dict]] = None,
    ) -> ExecutionResult:
        """Execute workflow in collaborative mode with breakpoints.
        
        Execution pauses at configured breakpoints for human review.
        
        Args:
            workflow_id: Workflow identifier.
            phase_executor: Optional function to execute each phase.
            
        Returns:
            Execution result, which may indicate paused status.
        """
        state = self.state_machine.get_workflow(workflow_id)
        if state is None:
            return ExecutionResult(
                workflow_id=workflow_id,
                status="error",
                current_phase=WorkflowPhase.IDLE,
                error="Workflow not found",
            )
        
        outputs = {}
        
        while not state.is_terminal and not state.is_paused:
            # Check for breakpoint at current phase
            breakpoint = self.breakpoints.should_pause_at(state.current_phase)
            
            if breakpoint:
                # Pause workflow for human review
                logger.info(f"Breakpoint reached: {breakpoint.value}")
                
                success = self.state_machine.await_approval(
                    workflow_id, checkpoint=breakpoint.value
                )
                
                if success and self.notification_handler:
                    await asyncio.to_thread(
                        self.notification_handler,
                        workflow_id,
                        state,
                        breakpoint,
                    )
                
                return ExecutionResult(
                    workflow_id=workflow_id,
                    status="paused",
                    current_phase=state.current_phase,
                    is_paused=True,
                    checkpoint=breakpoint,
                    outputs=outputs,
                )
            
            # Get valid next phases
            valid_transitions = self.state_machine.get_valid_transitions(workflow_id)
            
            if not valid_transitions:
                logger.warning(f"No valid transitions from {state.current_phase.value}")
                break
            
            # Select next phase
            next_phase = valid_transitions[0]
            
            # Execute phase if executor provided
            if phase_executor:
                try:
                    phase_output = await asyncio.to_thread(
                        phase_executor, state.current_phase, state.data
                    )
                    outputs[state.current_phase.value] = phase_output
                    state.data.update(phase_output)
                except Exception as e:
                    logger.error(f"Phase execution failed: {e}")
                    
                    # Check if we should pause on failure
                    if self.breakpoints.on_failure:
                        self.state_machine.pause_workflow(
                            workflow_id, reason=f"phase_failure:{str(e)}"
                        )
                        state = self.state_machine.get_workflow(workflow_id)
                        
                        return ExecutionResult(
                            workflow_id=workflow_id,
                            status="paused",
                            current_phase=state.current_phase,
                            is_paused=True,
                            checkpoint=Breakpoint.ON_FAILURE,
                            outputs=outputs,
                            error=str(e),
                        )
                    else:
                        self.state_machine.fail_workflow(workflow_id, str(e))
                        state = self.state_machine.get_workflow(workflow_id)
                        break
            
            # Transition to next phase
            success = self.state_machine.transition(
                workflow_id, next_phase, trigger="collaborative"
            )
            
            if not success:
                logger.error(f"Transition to {next_phase.value} failed")
                break
            
            state = self.state_machine.get_workflow(workflow_id)
        
        return ExecutionResult(
            workflow_id=workflow_id,
            status="completed" if state.current_phase == WorkflowPhase.COMPLETED else state.current_phase.value,
            current_phase=state.current_phase,
            is_paused=state.is_paused,
            outputs=outputs,
            error=state.error,
        )
    
    async def approve(
        self,
        workflow_id: str,
        reviewer_id: str,
        comments: Optional[str] = None,
        modifications: Optional[dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Approve a paused workflow and resume execution.
        
        Args:
            workflow_id: Workflow identifier.
            reviewer_id: ID of the approving user.
            comments: Optional review comments.
            modifications: Optional modifications to workflow data.
            
        Returns:
            Execution result after resuming.
        """
        state = self.state_machine.get_workflow(workflow_id)
        if state is None:
            return ExecutionResult(
                workflow_id=workflow_id,
                status="error",
                current_phase=WorkflowPhase.IDLE,
                error="Workflow not found",
            )
        
        if not state.is_paused:
            return ExecutionResult(
                workflow_id=workflow_id,
                status="error",
                current_phase=state.current_phase,
                error="Workflow is not paused",
            )
        
        # Apply any modifications
        if modifications:
            self.state_machine.update_data(workflow_id, modifications)
        
        # Resume the workflow
        approval_data = {
            "reviewer_id": reviewer_id,
            "comments": comments,
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }
        
        success = self.state_machine.resume_workflow(workflow_id, approval_data)
        
        if not success:
            return ExecutionResult(
                workflow_id=workflow_id,
                status="error",
                current_phase=state.current_phase,
                is_paused=True,
                error="Failed to resume workflow",
            )
        
        logger.info(f"Workflow {workflow_id} approved by {reviewer_id}")
        
        # Continue execution after approval
        return await self.execute(workflow_id)
    
    async def reject(
        self,
        workflow_id: str,
        reviewer_id: str,
        reason: str,
    ) -> ExecutionResult:
        """Reject a paused workflow and cancel execution.
        
        Args:
            workflow_id: Workflow identifier.
            reviewer_id: ID of the rejecting user.
            reason: Reason for rejection.
            
        Returns:
            Execution result after cancellation.
        """
        state = self.state_machine.get_workflow(workflow_id)
        if state is None:
            return ExecutionResult(
                workflow_id=workflow_id,
                status="error",
                current_phase=WorkflowPhase.IDLE,
                error="Workflow not found",
            )
        
        if not state.is_paused:
            return ExecutionResult(
                workflow_id=workflow_id,
                status="error",
                current_phase=state.current_phase,
                error="Workflow is not paused",
            )
        
        # Store rejection data
        rejection_data = {
            "rejected_by": reviewer_id,
            "rejection_reason": reason,
            "rejected_at": datetime.now(timezone.utc).isoformat(),
        }
        self.state_machine.update_data(workflow_id, rejection_data)
        
        # Cancel the workflow
        self.state_machine.cancel_workflow(workflow_id)
        state = self.state_machine.get_workflow(workflow_id)
        
        logger.info(f"Workflow {workflow_id} rejected by {reviewer_id}: {reason}")
        
        return ExecutionResult(
            workflow_id=workflow_id,
            status="rejected",
            current_phase=state.current_phase,
            is_paused=False,
            error=reason,
        )
    
    def get_pending_approvals(self) -> list[dict[str, Any]]:
        """Get list of workflows awaiting approval.
        
        Returns:
            List of workflow states that are paused.
        """
        pending = self.state_machine.list_pending_approvals()
        return [
            {
                "workflow_id": w.workflow_id,
                "current_phase": w.current_phase.value,
                "paused_at": w.data.get("approval_requested_at"),
                "checkpoint": w.data.get("approval_checkpoint"),
                "task_description": w.data.get("task_description"),
            }
            for w in pending
        ]
    
    def set_mode(self, mode: ExecutionMode) -> None:
        """Change the execution mode.
        
        Args:
            mode: New execution mode.
        """
        old_mode = self.mode
        self.mode = mode
        
        if mode == ExecutionMode.COLLABORATIVE and old_mode != mode:
            self._load_collaborative_rules()
        
        logger.info(f"Changed execution mode from {old_mode.value} to {mode.value}")


if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # Create orchestrator in collaborative mode
        config = BreakpointConfig(post_design=True, pre_deployment=True)
        orchestrator = DualModeOrchestrator(
            mode=ExecutionMode.COLLABORATIVE,
            breakpoints=config,
            persist=False,
        )
        
        # Create workflow
        workflow = await orchestrator.create_workflow(
            task_description="Build a REST API with user authentication",
            project_id="demo-project",
        )
        
        print(f"Created workflow: {workflow.workflow_id}")
        print(f"Mode: {orchestrator.mode.value}")
        print(f"Breakpoints: post_design={config.post_design}, pre_deployment={config.pre_deployment}")
        
        # Get pending approvals
        pending = orchestrator.get_pending_approvals()
        print(f"Pending approvals: {len(pending)}")
    
    asyncio.run(demo())
