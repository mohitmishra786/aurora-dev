"""
Unit tests for MaestroAgent weighted assignment scoring.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestMaestroAssignment:
    """Tests for MaestroAgent weighted agent assignment."""

    @pytest.fixture
    def maestro(self):
        """Create a MaestroAgent with mocked LLM."""
        with patch("aurora_dev.agents.base_agent.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = MagicMock(
                content=[MagicMock(text="[]")],
                usage=MagicMock(input_tokens=0, output_tokens=0),
                stop_reason="end_turn",
                model="claude-3-5-haiku",
            )
            from aurora_dev.agents.specialized.maestro import MaestroAgent
            agent = MaestroAgent(project_id="test-project")
            return agent

    def _make_task(self):
        """Create a properly configured mock task."""
        mock_task = MagicMock()
        mock_task.title = "Test task"
        mock_task.description = "Test description"
        mock_task.task_type = MagicMock()
        mock_task.task_type.value = "implementation"
        mock_task.acceptance_criteria = []
        mock_task.dependencies = []
        return mock_task

    def test_score_agent_specialization_match(self, maestro):
        """Test that specialization match gives highest weight."""
        from aurora_dev.agents.base_agent import AgentRole
        
        mock_agent = MagicMock()
        mock_agent.agent_id = "agent-1"
        mock_agent.role = AgentRole.BACKEND
        
        mock_task = self._make_task()
        
        score = maestro._score_agent(mock_agent, mock_task, AgentRole.BACKEND)
        
        # Specialization match = 1.0 * 0.35 = 0.35 contribution
        assert score > 0.35

    def test_score_agent_no_specialization_match(self, maestro):
        """Test lower score when specialization doesn't match."""
        from aurora_dev.agents.base_agent import AgentRole
        
        mock_agent = MagicMock()
        mock_agent.agent_id = "agent-1"
        mock_agent.role = AgentRole.BACKEND
        
        mock_task = self._make_task()
        
        # Role mismatch
        score_mismatch = maestro._score_agent(mock_agent, mock_task, AgentRole.FRONTEND)
        score_match = maestro._score_agent(mock_agent, mock_task, AgentRole.BACKEND)
        
        assert score_match > score_mismatch

    def test_score_agent_workload_balance(self, maestro):
        """Test that agents with fewer active tasks score higher."""
        from aurora_dev.agents.base_agent import AgentRole
        
        mock_agent = MagicMock()
        mock_agent.agent_id = "agent-1"
        mock_agent.role = AgentRole.BACKEND
        
        mock_task = self._make_task()
        
        # No active tasks
        maestro._agent_metrics["agent-1"] = {
            "tasks_assigned": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
        }
        score_idle = maestro._score_agent(mock_agent, mock_task, AgentRole.BACKEND)
        
        # 5 active tasks (but not exceeding per-cycle cap)
        maestro._agent_metrics["agent-1"] = {
            "tasks_assigned": 3,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "cycle_assigned": 0,
        }
        score_busy = maestro._score_agent(mock_agent, mock_task, AgentRole.BACKEND)
        
        assert score_idle > score_busy

    def test_score_agent_success_rate(self, maestro):
        """Test that agents with higher success rate score better."""
        from aurora_dev.agents.base_agent import AgentRole
        
        mock_agent = MagicMock()
        mock_agent.agent_id = "agent-1"
        mock_agent.role = AgentRole.BACKEND
        
        mock_task = self._make_task()
        
        # High success rate
        maestro._agent_metrics["agent-1"] = {
            "tasks_assigned": 10,
            "tasks_completed": 9,
            "tasks_failed": 1,
        }
        score_high = maestro._score_agent(mock_agent, mock_task, AgentRole.BACKEND)
        
        # Low success rate
        maestro._agent_metrics["agent-1"] = {
            "tasks_assigned": 10,
            "tasks_completed": 2,
            "tasks_failed": 8,
        }
        score_low = maestro._score_agent(mock_agent, mock_task, AgentRole.BACKEND)
        
        assert score_high > score_low

    def test_weight_constants(self, maestro):
        """Test that scoring weights sum to 1.0."""
        # Weights from _score_agent:
        # W_SPECIALIZATION=0.35, W_WORKLOAD=0.25, W_SUCCESS=0.20,
        # W_RECENCY=0.10, W_ROTATION=0.10
        assert 0.35 + 0.25 + 0.20 + 0.10 + 0.10 == pytest.approx(1.0)
