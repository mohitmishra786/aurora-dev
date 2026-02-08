"""
Unit tests for BaseAgent.

Tests agent initialization, API integration, retry logic, and token tracking.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

from aurora_dev.agents.base_agent import (
    AgentRole,
    AgentStatus,
    TokenUsage,
    AgentResponse,
    ResponseCache,
    BaseAgent,
)


class TestAgentRole:
    """Tests for AgentRole enum."""
    
    def test_all_roles_defined(self) -> None:
        """Verify all expected agent roles are defined."""
        expected_roles = [
            "MAESTRO", "MEMORY_COORDINATOR", "ARCHITECT", "RESEARCH",
            "PRODUCT_ANALYST", "BACKEND", "FRONTEND", "DATABASE",
            "INTEGRATION", "TEST_ENGINEER", "SECURITY_AUDITOR",
            "CODE_REVIEWER", "VALIDATOR", "DEVOPS", "DOCUMENTATION", "MONITORING"
        ]
        
        actual_roles = [role.name for role in AgentRole]
        
        for role in expected_roles:
            assert role in actual_roles, f"Missing role: {role}"
    
    def test_role_values(self) -> None:
        """Verify role values are lowercase strings."""
        for role in AgentRole:
            assert isinstance(role.value, str)
            assert role.value == role.value.lower()


class TestAgentStatus:
    """Tests for AgentStatus enum."""
    
    def test_all_statuses_defined(self) -> None:
        """Verify all expected statuses are defined."""
        expected = ["IDLE", "INITIALIZING", "WORKING", "WAITING", 
                    "PAUSED", "COMPLETED", "FAILED", "TERMINATED"]
        
        actual = [s.name for s in AgentStatus]
        
        for status in expected:
            assert status in actual, f"Missing status: {status}"


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""
    
    def test_default_values(self) -> None:
        """Test default initialization."""
        usage = TokenUsage()
        
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.cache_creation_tokens == 0
        assert usage.cache_read_tokens == 0
    
    def test_total_tokens(self) -> None:
        """Test total token calculation."""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            cache_creation_tokens=20,
            cache_read_tokens=10,
        )
        
        assert usage.total_tokens == 180
    
    def test_add(self) -> None:
        """Test adding token usage."""
        usage1 = TokenUsage(input_tokens=100, output_tokens=50)
        usage2 = TokenUsage(input_tokens=200, output_tokens=100)
        
        usage1.add(usage2)
        
        assert usage1.input_tokens == 300
        assert usage1.output_tokens == 150
    
    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        result = usage.to_dict()
        
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["total_tokens"] == 150


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""
    
    def test_success_property_true(self) -> None:
        """Test success property when no error."""
        response = AgentResponse(
            content="test content",
            token_usage=TokenUsage(),
            model="claude-3-sonnet",
            stop_reason="end_turn",
            execution_time_ms=100.0,
        )
        
        assert response.success is True
    
    def test_success_property_false(self) -> None:
        """Test success property when error present."""
        response = AgentResponse(
            content="",
            token_usage=TokenUsage(),
            model="claude-3-sonnet",
            stop_reason="error",
            execution_time_ms=100.0,
            error="API error occurred",
        )
        
        assert response.success is False
    
    def test_from_cache_default(self) -> None:
        """Test from_cache default is False."""
        response = AgentResponse(
            content="test",
            token_usage=TokenUsage(),
            model="claude-3-sonnet",
            stop_reason="end_turn",
            execution_time_ms=100.0,
        )
        
        assert response.from_cache is False


class TestResponseCache:
    """Tests for ResponseCache."""
    
    def test_cache_set_get(self) -> None:
        """Test setting and getting cached response."""
        cache = ResponseCache(max_size=10, ttl_seconds=3600)
        
        messages = [{"role": "user", "content": "test"}]
        system = "system prompt"
        model = "claude-3-sonnet"
        
        response = AgentResponse(
            content="cached response",
            token_usage=TokenUsage(),
            model=model,
            stop_reason="end_turn",
            execution_time_ms=50.0,
        )
        
        # Set cache
        cache.set(messages, system, model, response)
        
        # Get cache
        cached = cache.get(messages, system, model)
        
        assert cached is not None
        assert cached.content == "cached response"
        assert cached.from_cache is True
    
    def test_cache_miss(self) -> None:
        """Test cache miss returns None."""
        cache = ResponseCache()
        
        result = cache.get(
            [{"role": "user", "content": "new query"}],
            "system",
            "model"
        )
        
        assert result is None
    
    def test_cache_clear(self) -> None:
        """Test cache clearing."""
        cache = ResponseCache()
        
        messages = [{"role": "user", "content": "test"}]
        response = AgentResponse(
            content="test",
            token_usage=TokenUsage(),
            model="model",
            stop_reason="end_turn",
            execution_time_ms=50.0,
        )
        
        cache.set(messages, "system", "model", response)
        cache.clear()
        
        assert cache.get(messages, "system", "model") is None


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.BACKEND
    
    @property
    def system_prompt(self) -> str:
        return "Test system prompt"
    
    def execute(self, task: dict) -> AgentResponse:
        return AgentResponse(
            content="executed",
            token_usage=TokenUsage(),
            model=self._model,
            stop_reason="end_turn",
            execution_time_ms=100.0,
        )


class TestBaseAgent:
    """Tests for BaseAgent class."""
    
    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_initialization(self, mock_anthropic: Mock) -> None:
        """Test agent initialization."""
        agent = ConcreteAgent(name="TestAgent")
        
        assert agent.name == "TestAgent"
        assert agent.role == AgentRole.BACKEND
        assert agent.system_prompt == "Test system prompt"
    
    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_agent_id_generated(self, mock_anthropic: Mock) -> None:
        """Test unique agent ID is generated."""
        agent1 = ConcreteAgent()
        agent2 = ConcreteAgent()
        
        assert agent1.agent_id != agent2.agent_id
    
    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_execute_returns_response(self, mock_anthropic: Mock) -> None:
        """Test execute method returns AgentResponse."""
        agent = ConcreteAgent()
        
        response = agent.execute({"task": "test"})
        
        assert isinstance(response, AgentResponse)
        assert response.content == "executed"
    
    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_status_tracking(self, mock_anthropic: Mock) -> None:
        """Test agent status tracking."""
        agent = ConcreteAgent()
        
        # Initially should be idle
        assert agent._status == AgentStatus.IDLE
        
        # Change status
        agent._set_status(AgentStatus.WORKING)
        assert agent._status == AgentStatus.WORKING


class TestAgentWithMockedAPI:
    """Tests for agent API integration with mocked Anthropic."""
    
    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_call_api_success(self, mock_anthropic_class: Mock) -> None:
        """Test successful API call."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="API response")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.usage.cache_creation_input_tokens = 0
        mock_response.usage.cache_read_input_tokens = 0
        mock_response.model = "claude-3-sonnet"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        
        agent = ConcreteAgent()
        
        response = agent._call_api(
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1024,
            temperature=0.7,
        )
        
        assert response.success
        assert response.content == "API response"
        assert response.token_usage.input_tokens == 100
        assert response.token_usage.output_tokens == 50
