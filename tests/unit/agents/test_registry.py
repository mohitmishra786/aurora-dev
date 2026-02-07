"""Unit tests for Agent Registry."""
from unittest.mock import MagicMock, patch

import pytest


class TestAgentRegistry:
    """Tests for AgentRegistry class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import AgentRegistry
        AgentRegistry.reset()

    def teardown_method(self):
        """Clean up after each test."""
        from aurora_dev.agents.registry import AgentRegistry
        AgentRegistry.reset()

    def test_singleton_pattern(self):
        """Test that registry is a singleton."""
        from aurora_dev.agents.registry import get_registry
        
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2

    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_register_agent(self, mock_anthropic):
        """Test registering an agent."""
        from aurora_dev.agents.base_agent import AgentRole, BaseAgent, AgentResponse
        from aurora_dev.agents.registry import get_registry
        
        class TestAgent(BaseAgent):
            @property
            def role(self) -> AgentRole:
                return AgentRole.BACKEND
            
            @property
            def system_prompt(self) -> str:
                return "Test"
            
            def execute(self, task):
                return AgentResponse(
                    content="",
                    token_usage=self._total_usage,
                    model=self._model,
                    stop_reason="end_turn",
                    execution_time_ms=0,
                )
        
        registry = get_registry()
        agent = TestAgent(name="test")
        
        registry.register(agent)
        
        assert registry.count() == 1
        assert registry.get(agent.agent_id) is agent

    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_unregister_agent(self, mock_anthropic):
        """Test unregistering an agent."""
        from aurora_dev.agents.base_agent import AgentRole, BaseAgent, AgentResponse
        from aurora_dev.agents.registry import get_registry
        
        class TestAgent(BaseAgent):
            @property
            def role(self) -> AgentRole:
                return AgentRole.BACKEND
            
            @property
            def system_prompt(self) -> str:
                return "Test"
            
            def execute(self, task):
                return AgentResponse(
                    content="",
                    token_usage=self._total_usage,
                    model=self._model,
                    stop_reason="end_turn",
                    execution_time_ms=0,
                )
        
        registry = get_registry()
        agent = TestAgent()
        
        registry.register(agent)
        assert registry.count() == 1
        
        removed = registry.unregister(agent.agent_id)
        
        assert removed is agent
        assert registry.count() == 0

    @patch("aurora_dev.agents.base_agent.Anthropic")
    def test_get_by_role(self, mock_anthropic):
        """Test getting agents by role."""
        from aurora_dev.agents.base_agent import AgentRole, BaseAgent, AgentResponse
        from aurora_dev.agents.registry import get_registry
        
        class BackendAgent(BaseAgent):
            @property
            def role(self) -> AgentRole:
                return AgentRole.BACKEND
            
            @property
            def system_prompt(self) -> str:
                return "Test"
            
            def execute(self, task):
                return AgentResponse(
                    content="",
                    token_usage=self._total_usage,
                    model=self._model,
                    stop_reason="end_turn",
                    execution_time_ms=0,
                )
        
        class FrontendAgent(BaseAgent):
            @property
            def role(self) -> AgentRole:
                return AgentRole.FRONTEND
            
            @property
            def system_prompt(self) -> str:
                return "Test"
            
            def execute(self, task):
                return AgentResponse(
                    content="",
                    token_usage=self._total_usage,
                    model=self._model,
                    stop_reason="end_turn",
                    execution_time_ms=0,
                )
        
        registry = get_registry()
        
        backend1 = BackendAgent()
        backend2 = BackendAgent()
        frontend = FrontendAgent()
        
        registry.register(backend1)
        registry.register(backend2)
        registry.register(frontend)
        
        backend_agents = registry.get_by_role(AgentRole.BACKEND)
        frontend_agents = registry.get_by_role(AgentRole.FRONTEND)
        
        assert len(backend_agents) == 2
        assert len(frontend_agents) == 1

    def test_get_stats(self):
        """Test getting registry statistics."""
        from aurora_dev.agents.registry import get_registry
        
        registry = get_registry()
        stats = registry.get_stats()
        
        assert "total_agents" in stats
        assert "agents_by_status" in stats
        assert "agents_by_role" in stats
