"""Unit tests for Quality Agents (TestEngineer, SecurityAuditor, CodeReviewer)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from aurora_dev.agents.base_agent import AgentRole, AgentStatus


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestTestEngineerAgent:
    """Tests for TestEngineerAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test TestEngineer agent initialization."""
        from aurora_dev.agents.specialized.quality import TestEngineerAgent
        
        agent = TestEngineerAgent()
        
        assert agent.name == "TestEngineer"
        assert agent.role == AgentRole.TEST_ENGINEER
        assert agent.status == AgentStatus.IDLE

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has testing responsibilities."""
        from aurora_dev.agents.specialized.quality import TestEngineerAgent
        
        agent = TestEngineerAgent()
        prompt = agent.system_prompt
        
        assert "unit tests" in prompt
        assert "integration tests" in prompt
        assert "coverage" in prompt

    @patch("aurora_dev.agents.specialized.quality.TestEngineerAgent._call_api")
    def test_generate_unit_tests(self, mock_api, mock_anthropic):
        """Test unit test generation."""
        from aurora_dev.agents.specialized.quality import TestEngineerAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="def test_add(): assert add(1, 2) == 3",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = TestEngineerAgent()
        result = agent.generate_unit_tests(
            code="def add(a, b): return a + b",
            language="python",
        )
        
        assert result["coverage_target"] == 0.8
        assert result["success"]

    @patch("aurora_dev.agents.specialized.quality.TestEngineerAgent._call_api")
    def test_generate_e2e_tests(self, mock_api, mock_anthropic):
        """Test E2E test generation."""
        from aurora_dev.agents.specialized.quality import TestEngineerAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="test('login flow', async () => {})",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = TestEngineerAgent()
        result = agent.generate_e2e_tests(
            user_journey="User logs in and views dashboard",
            pages=["login", "dashboard"],
        )
        
        assert result["journey"] == "User logs in and views dashboard"
        assert result["success"]


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestSecurityAuditorAgent:
    """Tests for SecurityAuditorAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test SecurityAuditor agent initialization."""
        from aurora_dev.agents.specialized.quality import SecurityAuditorAgent
        
        agent = SecurityAuditorAgent()
        
        assert agent.name == "SecurityAuditor"
        assert agent.role == AgentRole.SECURITY_AUDITOR

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has security responsibilities."""
        from aurora_dev.agents.specialized.quality import SecurityAuditorAgent
        
        agent = SecurityAuditorAgent()
        prompt = agent.system_prompt
        
        assert "OWASP" in prompt
        assert "CVE" in prompt
        assert "SQL injection" in prompt

    @patch("aurora_dev.agents.specialized.quality.SecurityAuditorAgent._call_api")
    def test_audit_code(self, mock_api, mock_anthropic):
        """Test code security audit."""
        from aurora_dev.agents.specialized.quality import SecurityAuditorAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="No critical vulnerabilities found",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = SecurityAuditorAgent()
        result = agent.audit_code(
            code="password = input('Password: ')",
            language="python",
        )
        
        assert result["success"]

    @patch("aurora_dev.agents.specialized.quality.SecurityAuditorAgent._call_api")
    def test_check_dependencies(self, mock_api, mock_anthropic):
        """Test dependency vulnerability check."""
        from aurora_dev.agents.specialized.quality import SecurityAuditorAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="requests==2.28.0 - No known vulnerabilities",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = SecurityAuditorAgent()
        result = agent.check_dependencies(
            requirements="requests==2.28.0\nflask==2.0.0",
        )
        
        assert result["success"]


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestCodeReviewerAgent:
    """Tests for CodeReviewerAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test CodeReviewer agent initialization."""
        from aurora_dev.agents.specialized.quality import CodeReviewerAgent
        
        agent = CodeReviewerAgent()
        
        assert agent.name == "CodeReviewer"
        assert agent.role == AgentRole.CODE_REVIEWER

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has review responsibilities."""
        from aurora_dev.agents.specialized.quality import CodeReviewerAgent
        
        agent = CodeReviewerAgent()
        prompt = agent.system_prompt
        
        assert "SOLID" in prompt
        assert "quality" in prompt
        assert "best practices" in prompt.lower()

    @patch("aurora_dev.agents.specialized.quality.CodeReviewerAgent._call_api")
    def test_review_code(self, mock_api, mock_anthropic):
        """Test code review."""
        from aurora_dev.agents.specialized.quality import CodeReviewerAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="Code follows SOLID principles. Minor: consider extracting method.",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = CodeReviewerAgent()
        result = agent.review_code(
            code="class UserService: pass",
            language="python",
        )
        
        assert result["success"]

    @patch("aurora_dev.agents.specialized.quality.CodeReviewerAgent._call_api")
    def test_review_pr(self, mock_api, mock_anthropic):
        """Test PR review."""
        from aurora_dev.agents.specialized.quality import CodeReviewerAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="LGTM! Approved with minor suggestions.",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = CodeReviewerAgent()
        result = agent.review_pr(
            diff="+ new_function()\n- old_function()",
            description="Refactored user service",
        )
        
        assert result["success"]
