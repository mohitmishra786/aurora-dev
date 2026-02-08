"""
Unit tests for REST API routes.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestProjectRoutes:
    """Tests for project routes."""
    
    def test_project_response_model(self):
        """Test ProjectResponse model validation."""
        from aurora_dev.interfaces.api.routes.projects import ProjectResponse
        
        response = ProjectResponse(
            id="test-project",
            name="Test Project",
            path="/tmp/test",
            status="active",
            config={"language": "python"},
            cost_summary={"total_cost_usd": 0.0},
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        
        assert response.id == "test-project"
        assert response.name == "Test Project"
        assert response.status == "active"


class TestTaskRoutes:
    """Tests for task routes."""
    
    def test_task_response_model(self):
        """Test TaskResponse model validation."""
        from aurora_dev.interfaces.api.routes.tasks import TaskResponse
        
        response = TaskResponse(
            id="task-1",
            project_id="project-1",
            task_type="feature",
            description="Test task",
            status="pending",
            priority=5,
            assigned_agent=None,
            progress_percent=0,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        
        assert response.id == "task-1"
        assert response.status == "pending"


class TestAgentRoutes:
    """Tests for agent routes."""
    
    def test_available_agents(self):
        """Test that all expected agents are defined."""
        from aurora_dev.interfaces.api.routes.agents import AVAILABLE_AGENTS
        
        expected_agents = [
            "maestro", "memory_coordinator", "architect",
            "backend", "frontend", "database", "integration",
            "test_engineer", "security_auditor", "code_reviewer",
            "validator", "devops", "documentation", "monitoring",
        ]
        
        for agent in expected_agents:
            assert agent in AVAILABLE_AGENTS, f"Missing agent: {agent}"
    
    def test_agent_response_model(self):
        """Test AgentResponse model validation."""
        from aurora_dev.interfaces.api.routes.agents import AgentResponse
        
        response = AgentResponse(
            id="maestro",
            name="Maestro",
            tier="orchestration",
            description="Test description",
            model="claude-sonnet-4-20250514",
            status="idle",
            current_task=None,
            tasks_completed=0,
            tasks_failed=0,
            last_active=None,
        )
        
        assert response.id == "maestro"
        assert response.tier == "orchestration"


class TestWorkflowRoutes:
    """Tests for workflow routes."""
    
    def test_workflow_response_model(self):
        """Test WorkflowResponse model validation."""
        from aurora_dev.interfaces.api.routes.workflows import WorkflowResponse
        
        response = WorkflowResponse(
            id="workflow-1",
            project_id="project-1",
            workflow_type="feature",
            status="running",
            current_phase="planning",
            attempt_number=1,
            max_attempts=5,
            progress_percent=10,
            started_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            completed_at=None,
            error=None,
        )
        
        assert response.id == "workflow-1"
        assert response.workflow_type == "feature"


class TestWebSocketManager:
    """Tests for WebSocket connection manager."""
    
    def test_get_connection_manager_singleton(self):
        """Test singleton pattern."""
        from aurora_dev.interfaces.ws.manager import (
            get_connection_manager,
            _manager,
        )
        
        manager1 = get_connection_manager()
        manager2 = get_connection_manager()
        
        assert manager1 is manager2
    
    def test_connection_manager_init(self):
        """Test ConnectionManager initialization."""
        from aurora_dev.interfaces.ws.manager import ConnectionManager
        
        manager = ConnectionManager()
        
        assert manager.get_active_connections() == 0
        assert manager.get_project_connections("test") == 0
