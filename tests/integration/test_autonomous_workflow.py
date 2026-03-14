"""
Integration test for autonomous workflow execution.

Tests the complete flow from user request through all phases
to final deployment using the autonomous mode.
"""
import asyncio
import pytest
from unittest.mock import patch, MagicMock

from aurora_dev.core.orchestrator.dual_mode import (
    DualModeOrchestrator,
    ExecutionMode,
    BreakpointConfig,
)
from aurora_dev.core.orchestrator.phase_executor import PhaseExecutor
from aurora_dev.core.state_machine.machine import StateMachine
from aurora_dev.core.state_machine.states import WorkflowPhase


@pytest.mark.asyncio
async def test_autonomous_workflow_execution():
    """Test complete autonomous workflow execution through all phases."""
    # Initialize state machine
    state_machine = StateMachine()

    # Create workflow with realistic project data
    workflow_id = "integration-test-workflow"
    initial_data = {
        "project_id": "integration-test-project",
        "goal": "Build a simple user management API",
        "tech_stack": ["python", "fastapi", "postgresql"],
        "requirements": "Create a REST API for user registration, login, and profile management",
    }

    state_machine.create_workflow(
        workflow_id=workflow_id,
        initial_data=initial_data,
    )

    # Initialize orchestrator in autonomous mode
    orchestrator = DualModeOrchestrator(
        state_machine=state_machine,
        mode=ExecutionMode.AUTONOMOUS,
    )

    # Initialize phase executor
    phase_executor = PhaseExecutor(project_id="integration-test-project")

    # Mock the agent API calls to avoid actual API calls
    with patch.object(
        phase_executor.product_analyst,
        "analyze_requirements",
        return_value={
            "functional_requirements": [
                {
                    "id": "FR001",
                    "title": "User Registration",
                    "description": "Allow new users to register with email and password",
                    "priority": "must_have",
                }
            ],
            "user_stories": [],
            "acceptance_criteria": [],
        },
    ), patch.object(
        phase_executor.architect,
        "design_architecture",
        return_value={
            "architecture_style": "monolith",
            "services": [],
            "communication": {},
            "data_storage": {},
        },
    ):
        # Create sync wrapper for phase executor
        def phase_executor_wrapper(phase, context):
            return asyncio.run(phase_executor.execute_phase(phase, context))

        # Execute the workflow
        result = await orchestrator.execute(
            workflow_id=workflow_id,
            phase_executor=phase_executor_wrapper,
        )

    # Verify workflow completed successfully
    assert result.status == "completed"
    assert result.current_phase == WorkflowPhase.COMPLETED
    assert result.error is None

    # Verify workflow progressed through expected phases
    workflow_state = state_machine.get_workflow(workflow_id)
    assert workflow_state is not None
    assert workflow_state.current_phase == WorkflowPhase.COMPLETED


@pytest.mark.asyncio
async def test_collaborative_workflow_with_breakpoints():
    """Test collaborative workflow execution pauses at breakpoints."""
    # Initialize state machine
    state_machine = StateMachine()

    # Create workflow
    workflow_id = "collaborative-test-workflow"
    initial_data = {
        "project_id": "collaborative-test-project",
        "goal": "Build a web application",
        "tech_stack": ["python", "react"],
    }

    state_machine.create_workflow(
        workflow_id=workflow_id,
        initial_data=initial_data,
    )

    # Configure breakpoints
    bp_config = BreakpointConfig(
        post_design=True,
        post_plan=False,
        pre_testing=False,
        pre_deployment=True,
        on_failure=True,
    )

    # Initialize orchestrator in collaborative mode
    orchestrator = DualModeOrchestrator(
        state_machine=state_machine,
        mode=ExecutionMode.COLLABORATIVE,
        breakpoints=bp_config,
    )

    # Initialize phase executor
    phase_executor = PhaseExecutor(project_id="collaborative-test-project")

    # Create sync wrapper
    def phase_executor_wrapper(phase, context):
        return asyncio.run(phase_executor.execute_phase(phase, context))

    # Mock agent responses to avoid actual API calls
    with patch.object(
        phase_executor.product_analyst,
        "analyze_requirements",
        return_value={
            "functional_requirements": [],
            "user_stories": [],
            "acceptance_criteria": [],
        },
    ), patch.object(
        phase_executor.architect,
        "design_architecture",
        return_value={
            "architecture_style": "monolith",
            "services": [],
            "communication": {},
            "data_storage": {},
        },
    ):
        # Execute the workflow
        result = await orchestrator.execute(
            workflow_id=workflow_id,
            phase_executor=phase_executor_wrapper,
        )

    # In collaborative mode, workflow may pause at breakpoints
    # For this test, we verify it completes or pauses appropriately
    assert result.status in ["completed", "paused"]

    # Verify the workflow state is valid
    workflow_state = state_machine.get_workflow(workflow_id)
    assert workflow_state is not None


@pytest.mark.asyncio
async def test_phase_executor_with_context():
    """Test phase executor properly uses context data."""
    # Initialize phase executor
    phase_executor = PhaseExecutor(project_id="test-context-project")

    # Test context with project data
    context = {
        "project_id": "test-context-project",
        "goal": "Build API",
        "tech_stack": ["python"],
        "requirements": "User management API",
    }

    # Mock the product analyst to verify it receives context
    with patch.object(
        phase_executor.product_analyst,
        "analyze_requirements",
        return_value={
            "functional_requirements": [],
            "user_stories": [],
            "acceptance_criteria": [],
        },
    ) as mock_analyze:
        # Execute requirements phase
        result = await phase_executor.execute_phase(
            WorkflowPhase.REQUIREMENTS,
            context,
        )

        # Verify the phase completed
        assert result["status"] == "completed"
        assert result["phase"] == "requirements"

        # Verify analyze_requirements was called with context
        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        assert "context" in call_args.kwargs or len(call_args.args) > 1


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
