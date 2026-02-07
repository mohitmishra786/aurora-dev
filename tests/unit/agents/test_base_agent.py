"""Unit tests for BaseAgent class."""
import uuid
from unittest.mock import MagicMock, patch

import pytest


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_token_usage_creation(self):
        """Test creating TokenUsage."""
        from aurora_dev.agents.base_agent import TokenUsage
        
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150

    def test_token_usage_add(self):
        """Test adding token usages."""
        from aurora_dev.agents.base_agent import TokenUsage
        
        usage1 = TokenUsage(input_tokens=100, output_tokens=50)
        usage2 = TokenUsage(input_tokens=200, output_tokens=100)
        
        usage1.add(usage2)
        
        assert usage1.input_tokens == 300
        assert usage1.output_tokens == 150
        assert usage1.total_tokens == 450


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_response_success(self):
        """Test successful response."""
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        response = AgentResponse(
            content="Test response",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="claude-3-5-haiku-20241022",
            stop_reason="end_turn",
            execution_time_ms=500.0,
        )
        
        assert response.success is True
        assert response.content == "Test response"

    def test_response_failure(self):
        """Test failed response."""
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        response = AgentResponse(
            content="",
            token_usage=TokenUsage(),
            model="claude-3-5-haiku-20241022",
            stop_reason="error",
            execution_time_ms=100.0,
            error="API Error",
        )
        
        assert response.success is False
        assert response.error == "API Error"


class TestResponseCache:
    """Tests for ResponseCache class."""

    def test_cache_set_and_get(self):
        """Test caching and retrieving responses."""
        from aurora_dev.agents.base_agent import (
            AgentResponse,
            ResponseCache,
            TokenUsage,
        )
        
        cache = ResponseCache(max_size=10, ttl_seconds=3600)
        
        messages = [{"role": "user", "content": "Hello"}]
        system = "You are a helpful assistant"
        model = "claude-3-5-haiku-20241022"
        
        response = AgentResponse(
            content="Hi there!",
            token_usage=TokenUsage(input_tokens=10, output_tokens=5),
            model=model,
            stop_reason="end_turn",
            execution_time_ms=100.0,
        )
        
        # Set
        cache.set(messages, system, model, response)
        
        # Get
        cached = cache.get(messages, system, model)
        
        assert cached is not None
        assert cached.content == "Hi there!"

    def test_cache_miss(self):
        """Test cache miss."""
        from aurora_dev.agents.base_agent import ResponseCache
        
        cache = ResponseCache()
        
        result = cache.get(
            [{"role": "user", "content": "Hello"}],
            "system",
            "model",
        )
        
        assert result is None

    def test_cache_max_size(self):
        """Test cache size limit."""
        from aurora_dev.agents.base_agent import (
            AgentResponse,
            ResponseCache,
            TokenUsage,
        )
        
        cache = ResponseCache(max_size=2, ttl_seconds=3600)
        
        for i in range(3):
            messages = [{"role": "user", "content": f"Message {i}"}]
            response = AgentResponse(
                content=f"Response {i}",
                token_usage=TokenUsage(),
                model="test",
                stop_reason="end_turn",
                execution_time_ms=100.0,
            )
            cache.set(messages, "system", "model", response)
        
        # First message should be evicted
        result = cache.get([{"role": "user", "content": "Message 0"}], "system", "model")
        assert result is None
        
        # Later messages should still be cached
        result = cache.get([{"role": "user", "content": "Message 2"}], "system", "model")
        assert result is not None


class TestAgentRole:
    """Tests for AgentRole enum."""

    def test_agent_roles_exist(self):
        """Test that expected agent roles exist."""
        from aurora_dev.agents.base_agent import AgentRole
        
        assert AgentRole.MAESTRO.value == "maestro"
        assert AgentRole.BACKEND.value == "backend"
        assert AgentRole.FRONTEND.value == "frontend"
        assert AgentRole.TEST_ENGINEER.value == "test_engineer"


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_agent_statuses(self):
        """Test agent status values."""
        from aurora_dev.agents.base_agent import AgentStatus
        
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.WORKING.value == "working"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"


class TestBaseAgent:
    """Tests for BaseAgent abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that BaseAgent cannot be instantiated directly."""
        from aurora_dev.agents.base_agent import BaseAgent
        
        with pytest.raises(TypeError):
            BaseAgent()  # type: ignore

    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_concrete_agent_instantiation(self, mock_anthropic):
        """Test instantiating a concrete agent."""
        from aurora_dev.agents.base_agent import (
            AgentResponse,
            AgentRole,
            AgentStatus,
            BaseAgent,
        )
        
        class TestAgent(BaseAgent):
            @property
            def role(self) -> AgentRole:
                return AgentRole.BACKEND
            
            @property
            def system_prompt(self) -> str:
                return "You are a test agent."
            
            def execute(self, task):
                return AgentResponse(
                    content="Done",
                    token_usage=self._total_usage,
                    model=self._model,
                    stop_reason="end_turn",
                    execution_time_ms=0,
                )
        
        agent = TestAgent(name="test-agent")
        
        assert agent.name == "test-agent"
        assert agent.role == AgentRole.BACKEND
        assert agent.status == AgentStatus.IDLE
        assert agent.request_count == 0

    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_agent_get_stats(self, mock_anthropic):
        """Test getting agent statistics."""
        from aurora_dev.agents.base_agent import AgentRole, BaseAgent, AgentResponse
        
        class TestAgent(BaseAgent):
            @property
            def role(self) -> AgentRole:
                return AgentRole.BACKEND
            
            @property
            def system_prompt(self) -> str:
                return "You are a test agent."
            
            def execute(self, task):
                return AgentResponse(
                    content="Done",
                    token_usage=self._total_usage,
                    model=self._model,
                    stop_reason="end_turn",
                    execution_time_ms=0,
                )
        
        agent = TestAgent(
            name="stats-test",
            project_id="project-123",
        )
        
        stats = agent.get_stats()
        
        assert stats["name"] == "stats-test"
        assert stats["role"] == "backend"
        assert stats["project_id"] == "project-123"
        assert stats["request_count"] == 0
        assert "created_at" in stats
