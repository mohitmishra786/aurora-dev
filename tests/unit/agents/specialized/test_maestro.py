"""Unit tests for Maestro Agent."""
import json
from unittest.mock import MagicMock, patch

import pytest

from aurora_dev.agents.base_agent import AgentRole, AgentStatus
from aurora_dev.agents.task import TaskComplexity, TaskPriority, TaskStatus, TaskType


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestMaestroAgent:
    """Tests for MaestroAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_maestro_initialization(self, mock_anthropic):
        """Test Maestro agent initialization."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent(project_id="test-project")
        
        assert agent.name == "Maestro"
        assert agent.role == AgentRole.MAESTRO
        assert agent.status == AgentStatus.IDLE
        assert agent._project_id == "test-project"

    def test_maestro_role_is_maestro(self, mock_anthropic):
        """Test that role returns MAESTRO."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        assert agent.role == AgentRole.MAESTRO

    def test_maestro_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has orchestration responsibilities."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        prompt = agent.system_prompt
        
        assert "Task Decomposition" in prompt
        assert "Task Assignment" in prompt
        assert "Progress Monitoring" in prompt

    @patch("aurora_dev.agents.specialized.maestro.MaestroAgent._call_api")
    def test_decompose_goal_with_valid_response(self, mock_api, mock_anthropic):
        """Test goal decomposition with valid JSON response."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content=json.dumps({
                "tasks": [
                    {
                        "name": "Setup database",
                        "description": "Create PostgreSQL schema",
                        "type": "WRITE_CODE",
                        "target_agent": "DATABASE",
                        "priority": "HIGH",
                        "complexity": "MEDIUM",
                        "dependencies": [],
                        "requirements": ["PostgreSQL"]
                    }
                ],
                "execution_order": ["task-1"],
                "notes": "Start with database setup"
            }),
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = MaestroAgent()
        tasks = agent.decompose_goal("Build a user management system")
        
        assert len(tasks) == 1
        assert tasks[0].name == "Setup database"
        assert tasks[0].priority == TaskPriority.HIGH
        assert tasks[0].complexity == TaskComplexity.MEDIUM

    def test_parse_task_type(self, mock_anthropic):
        """Test parsing task type strings."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        
        assert agent._parse_task_type("WRITE_CODE") == TaskType.WRITE_CODE
        assert agent._parse_task_type("FIX_BUG") == TaskType.FIX_BUG
        assert agent._parse_task_type("DESIGN_ARCHITECTURE") == TaskType.DESIGN_ARCHITECTURE
        assert agent._parse_task_type("UNKNOWN") == TaskType.WRITE_CODE

    def test_parse_priority(self, mock_anthropic):
        """Test parsing priority strings."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        
        assert agent._parse_priority("LOW") == TaskPriority.LOW
        assert agent._parse_priority("NORMAL") == TaskPriority.NORMAL
        assert agent._parse_priority("HIGH") == TaskPriority.HIGH
        assert agent._parse_priority("CRITICAL") == TaskPriority.CRITICAL
        assert agent._parse_priority("UNKNOWN") == TaskPriority.NORMAL

    def test_parse_complexity(self, mock_anthropic):
        """Test parsing complexity strings."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        
        assert agent._parse_complexity("TRIVIAL") == TaskComplexity.TRIVIAL
        assert agent._parse_complexity("LOW") == TaskComplexity.LOW
        assert agent._parse_complexity("MEDIUM") == TaskComplexity.MEDIUM
        assert agent._parse_complexity("HIGH") == TaskComplexity.HIGH
        assert agent._parse_complexity("VERY_HIGH") == TaskComplexity.VERY_HIGH

    def test_get_project_status_empty(self, mock_anthropic):
        """Test project status with no tasks."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        status = agent.get_project_status()
        
        assert status["total_tasks"] == 0
        assert status["completed"] == 0
        assert status["failed"] == 0

    def test_get_next_tasks_empty(self, mock_anthropic):
        """Test getting next tasks with empty graph."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        tasks = agent.get_next_tasks()
        
        assert tasks == []

    def test_process_messages_empty(self, mock_anthropic):
        """Test processing with no messages."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        processed = agent.process_messages()
        
        assert processed == 0


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestMaestroTaskParsing:
    """Tests for Maestro's task parsing functionality."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_parse_empty_response(self, mock_anthropic):
        """Test parsing empty response."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        tasks = agent._parse_task_response("", None)
        
        assert tasks == []

    def test_parse_invalid_json(self, mock_anthropic):
        """Test parsing invalid JSON."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        tasks = agent._parse_task_response("not valid json", None)
        
        assert tasks == []

    def test_parse_valid_response_with_context(self, mock_anthropic):
        """Test parsing valid response with context."""
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        agent = MaestroAgent()
        response = json.dumps({
            "tasks": [
                {
                    "name": "Test Task",
                    "description": "A test task",
                    "type": "WRITE_CODE",
                    "target_agent": "BACKEND",
                    "priority": "NORMAL",
                    "complexity": "LOW",
                    "dependencies": [],
                    "requirements": []
                }
            ]
        })
        
        tasks = agent._parse_task_response(response, {"project_id": "proj-123"})
        
        assert len(tasks) == 1
        assert tasks[0].project_id == "proj-123"
