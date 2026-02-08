"""
Unit tests for state machine phases and transitions.

Tests the PAUSED, AWAITING_APPROVAL phases and collaborative
mode transition rules.
"""
import pytest
from datetime import datetime, timezone

from aurora_dev.core.state_machine.states import (
    WorkflowPhase,
    TransitionType,
    TransitionRule,
    WorkflowState,
    get_default_transitions,
    get_collaborative_transitions,
)
from aurora_dev.core.state_machine.machine import StateMachine


class TestWorkflowPhases:
    """Test the extended WorkflowPhase enum."""
    
    def test_paused_phase_exists(self):
        """PAUSED phase should exist in the enum."""
        assert hasattr(WorkflowPhase, "PAUSED")
        assert WorkflowPhase.PAUSED.value == "paused"
    
    def test_awaiting_approval_phase_exists(self):
        """AWAITING_APPROVAL phase should exist in the enum."""
        assert hasattr(WorkflowPhase, "AWAITING_APPROVAL")
        assert WorkflowPhase.AWAITING_APPROVAL.value == "awaiting_approval"
    
    def test_all_active_phases_present(self):
        """All active workflow phases should be present."""
        active_phases = [
            "IDLE", "REQUIREMENTS", "DESIGN", "IMPLEMENTATION",
            "TESTING", "CODE_REVIEW", "SECURITY_AUDIT",
            "DOCUMENTATION", "DEPLOYMENT", "MONITORING",
        ]
        for phase in active_phases:
            assert hasattr(WorkflowPhase, phase), f"Missing phase: {phase}"
    
    def test_terminal_phases_present(self):
        """Terminal phases should be present."""
        terminal_phases = ["COMPLETED", "FAILED", "CANCELLED"]
        for phase in terminal_phases:
            assert hasattr(WorkflowPhase, phase), f"Missing terminal phase: {phase}"


class TestTransitionTypes:
    """Test the extended TransitionType enum."""
    
    def test_human_approval_type_exists(self):
        """HUMAN_APPROVAL transition type should exist."""
        assert hasattr(TransitionType, "HUMAN_APPROVAL")
        assert TransitionType.HUMAN_APPROVAL.value == "human_approval"
    
    def test_breakpoint_type_exists(self):
        """BREAKPOINT transition type should exist."""
        assert hasattr(TransitionType, "BREAKPOINT")
        assert TransitionType.BREAKPOINT.value == "breakpoint"
    
    def test_original_types_preserved(self):
        """Original transition types should still exist."""
        original_types = ["AUTOMATIC", "MANUAL", "CONDITIONAL", "TIMEOUT", "ERROR"]
        for t in original_types:
            assert hasattr(TransitionType, t), f"Missing type: {t}"


class TestWorkflowState:
    """Test the WorkflowState dataclass."""
    
    def test_is_paused_false_for_active_phases(self):
        """is_paused should be False for active phases."""
        state = WorkflowState(
            workflow_id="test-123",
            current_phase=WorkflowPhase.IMPLEMENTATION,
        )
        assert state.is_paused is False
    
    def test_is_paused_true_for_paused_phase(self):
        """is_paused should be True for PAUSED phase."""
        state = WorkflowState(
            workflow_id="test-123",
            current_phase=WorkflowPhase.PAUSED,
        )
        assert state.is_paused is True
    
    def test_is_paused_true_for_awaiting_approval(self):
        """is_paused should be True for AWAITING_APPROVAL phase."""
        state = WorkflowState(
            workflow_id="test-123",
            current_phase=WorkflowPhase.AWAITING_APPROVAL,
        )
        assert state.is_paused is True
    
    def test_to_dict_includes_is_paused(self):
        """to_dict should include is_paused field."""
        state = WorkflowState(
            workflow_id="test-123",
            current_phase=WorkflowPhase.PAUSED,
        )
        result = state.to_dict()
        assert "is_paused" in result
        assert result["is_paused"] is True


class TestCollaborativeTransitions:
    """Test collaborative mode transition rules."""
    
    def test_collaborative_transitions_include_base(self):
        """Collaborative transitions should include base transitions."""
        base = get_default_transitions()
        collab = get_collaborative_transitions()
        
        # Collaborative should have more rules
        assert len(collab) > len(base)
    
    def test_collaborative_has_design_breakpoint(self):
        """Should have a breakpoint after DESIGN phase."""
        transitions = get_collaborative_transitions()
        
        design_to_approval = [
            t for t in transitions
            if t.from_phase == WorkflowPhase.DESIGN
            and t.to_phase == WorkflowPhase.AWAITING_APPROVAL
        ]
        
        assert len(design_to_approval) > 0, "Missing DESIGN -> AWAITING_APPROVAL transition"
    
    def test_collaborative_has_deployment_breakpoint(self):
        """Should have a breakpoint before deployment."""
        transitions = get_collaborative_transitions()
        
        pre_deployment = [
            t for t in transitions
            if t.to_phase == WorkflowPhase.AWAITING_APPROVAL
            and t.from_phase == WorkflowPhase.SECURITY_AUDIT
        ]
        
        assert len(pre_deployment) > 0, "Missing pre-deployment breakpoint"
    
    def test_approval_to_next_phase_transitions(self):
        """AWAITING_APPROVAL should transition to next phase on approval."""
        transitions = get_collaborative_transitions()
        
        from_approval = [
            t for t in transitions
            if t.from_phase == WorkflowPhase.AWAITING_APPROVAL
        ]
        
        assert len(from_approval) > 0, "No transitions from AWAITING_APPROVAL"


class TestStateMachinePauseResume:
    """Test StateMachine pause/resume functionality."""
    
    def test_pause_workflow(self):
        """pause_workflow should set phase to PAUSED."""
        machine = StateMachine(persist=False)
        state = machine.create_workflow()
        workflow_id = state.workflow_id
        
        # Advance to a running phase
        machine.transition(workflow_id, WorkflowPhase.REQUIREMENTS)
        machine.transition(workflow_id, WorkflowPhase.DESIGN)
        
        # Pause
        success = machine.pause_workflow(workflow_id, reason="test pause")
        assert success is True
        
        state = machine.get_workflow(workflow_id)
        assert state.current_phase == WorkflowPhase.PAUSED
        assert state.is_paused is True
        # Check that phase_before_pause is stored for resume
        assert state.data.get("phase_before_pause") == "design"
    
    def test_resume_workflow(self):
        """resume_workflow should restore previous phase."""
        machine = StateMachine(persist=False)
        state = machine.create_workflow()
        workflow_id = state.workflow_id
        
        # Advance and pause
        machine.transition(workflow_id, WorkflowPhase.REQUIREMENTS)
        machine.transition(workflow_id, WorkflowPhase.DESIGN)
        machine.pause_workflow(workflow_id)
        
        # Resume
        approval_data = {"approved_by": "reviewer-1"}
        success = machine.resume_workflow(workflow_id, approval_data)
        assert success is True
        
        state = machine.get_workflow(workflow_id)
        # Should resume to the phase before pause
        assert state.current_phase == WorkflowPhase.DESIGN
        assert state.is_paused is False
    
    def test_await_approval(self):
        """await_approval should set phase to AWAITING_APPROVAL."""
        machine = StateMachine(persist=False)
        state = machine.create_workflow()
        workflow_id = state.workflow_id
        
        # Advance to design
        machine.transition(workflow_id, WorkflowPhase.REQUIREMENTS)
        machine.transition(workflow_id, WorkflowPhase.DESIGN)
        
        # Request approval
        success = machine.await_approval(workflow_id, checkpoint="architecture_review")
        assert success is True
        
        state = machine.get_workflow(workflow_id)
        assert state.current_phase == WorkflowPhase.AWAITING_APPROVAL
        assert state.is_paused is True
        assert state.data.get("approval_checkpoint") == "architecture_review"
    
    def test_list_pending_approvals(self):
        """list_pending_approvals should return paused workflows."""
        machine = StateMachine(persist=False)
        
        # Create multiple workflows
        state1 = machine.create_workflow()
        state2 = machine.create_workflow()
        state3 = machine.create_workflow()
        
        # Pause two of them
        machine.transition(state1.workflow_id, WorkflowPhase.REQUIREMENTS)
        machine.await_approval(state1.workflow_id, checkpoint="test")
        
        machine.transition(state2.workflow_id, WorkflowPhase.REQUIREMENTS)
        machine.pause_workflow(state2.workflow_id)
        
        # Leave state3 running
        machine.transition(state3.workflow_id, WorkflowPhase.REQUIREMENTS)
        
        pending = machine.list_pending_approvals()
        
        assert len(pending) == 2
        pending_ids = [w.workflow_id for w in pending]
        assert state1.workflow_id in pending_ids
        assert state2.workflow_id in pending_ids
        assert state3.workflow_id not in pending_ids


class TestStateMachineStats:
    """Test StateMachine statistics with paused workflows."""
    
    def test_get_statistics_includes_paused(self):
        """get_statistics should include paused workflow counts."""
        machine = StateMachine(persist=False)
        
        # Create and pause a workflow
        state = machine.create_workflow()
        machine.transition(state.workflow_id, WorkflowPhase.REQUIREMENTS)
        machine.pause_workflow(state.workflow_id)
        
        stats = machine.get_statistics()
        
        assert "total_workflows" in stats
        # Check by_phase includes paused
        assert "by_phase" in stats
        assert "paused" in stats["by_phase"]
        assert stats["by_phase"]["paused"] >= 1
