"""Unit tests for Developer Agents (Backend, Frontend, Database, Integration)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from aurora_dev.agents.base_agent import AgentRole, AgentStatus


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestBackendAgent:
    """Tests for BackendAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test Backend agent initialization."""
        from aurora_dev.agents.specialized.developers import BackendAgent
        
        agent = BackendAgent()
        
        assert agent.name == "BackendDeveloper"
        assert agent.role == AgentRole.BACKEND
        assert agent.status == AgentStatus.IDLE

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has backend responsibilities."""
        from aurora_dev.agents.specialized.developers import BackendAgent
        
        agent = BackendAgent()
        prompt = agent.system_prompt
        
        assert "business logic" in prompt
        assert "RESTful" in prompt
        assert "authentication" in prompt

    @patch("aurora_dev.agents.specialized.developers.BackendAgent._call_api")
    def test_implement_endpoint(self, mock_api, mock_anthropic):
        """Test endpoint implementation."""
        from aurora_dev.agents.specialized.developers import BackendAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="def create_user(): pass",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = BackendAgent()
        result = agent.implement_endpoint(
            endpoint="/api/users",
            method="POST",
            description="Create new user",
        )
        
        assert result["endpoint"] == "/api/users"
        assert result["method"] == "POST"
        assert result["success"]


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestFrontendAgent:
    """Tests for FrontendAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test Frontend agent initialization."""
        from aurora_dev.agents.specialized.developers import FrontendAgent
        
        agent = FrontendAgent()
        
        assert agent.name == "FrontendDeveloper"
        assert agent.role == AgentRole.FRONTEND

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has frontend responsibilities."""
        from aurora_dev.agents.specialized.developers import FrontendAgent
        
        agent = FrontendAgent()
        prompt = agent.system_prompt
        
        assert "UI components" in prompt
        assert "state management" in prompt
        assert "accessibility" in prompt

    @patch("aurora_dev.agents.specialized.developers.FrontendAgent._call_api")
    def test_implement_component(self, mock_api, mock_anthropic):
        """Test component implementation."""
        from aurora_dev.agents.specialized.developers import FrontendAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="function Button() { return <button /> }",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = FrontendAgent()
        result = agent.implement_component(
            component_name="Button",
            props={"label": "string", "onClick": "function"},
            description="Primary button component",
        )
        
        assert result["component"] == "Button"
        assert result["success"]


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestDatabaseAgent:
    """Tests for DatabaseAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test Database agent initialization."""
        from aurora_dev.agents.specialized.developers import DatabaseAgent
        
        agent = DatabaseAgent()
        
        assert agent.name == "DatabaseSpecialist"
        assert agent.role == AgentRole.DATABASE

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has database responsibilities."""
        from aurora_dev.agents.specialized.developers import DatabaseAgent
        
        agent = DatabaseAgent()
        prompt = agent.system_prompt
        
        assert "schema" in prompt
        assert "indexes" in prompt
        assert "migrations" in prompt

    @patch("aurora_dev.agents.specialized.developers.DatabaseAgent._call_api")
    def test_design_schema(self, mock_api, mock_anthropic):
        """Test schema design."""
        from aurora_dev.agents.specialized.developers import DatabaseAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="CREATE TABLE users (id UUID PRIMARY KEY);",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = DatabaseAgent()
        result = agent.design_schema(
            entities=[{"name": "users", "fields": ["id", "email"]}],
            relationships=[],
        )
        
        assert result["database"] == "postgresql"
        assert result["success"]


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestIntegrationAgent:
    """Tests for IntegrationAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test Integration agent initialization."""
        from aurora_dev.agents.specialized.developers import IntegrationAgent
        
        agent = IntegrationAgent()
        
        assert agent.name == "IntegrationSpecialist"
        assert agent.role == AgentRole.INTEGRATION

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has integration responsibilities."""
        from aurora_dev.agents.specialized.developers import IntegrationAgent
        
        agent = IntegrationAgent()
        prompt = agent.system_prompt
        
        assert "third-party" in prompt
        assert "OAuth" in prompt
        assert "circuit breaker" in prompt.lower()

    @patch("aurora_dev.agents.specialized.developers.IntegrationAgent._call_api")
    def test_integrate_service(self, mock_api, mock_anthropic):
        """Test service integration."""
        from aurora_dev.agents.specialized.developers import IntegrationAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="class StripeClient: pass",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = IntegrationAgent()
        result = agent.integrate_service(
            service="Stripe",
            operations=["create_payment", "refund"],
        )
        
        assert result["service"] == "Stripe"
        assert result["success"]
