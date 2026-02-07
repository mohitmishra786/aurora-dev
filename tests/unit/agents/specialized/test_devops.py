"""Unit tests for DevOps Agents (DevOps, Documentation, Research)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from aurora_dev.agents.base_agent import AgentRole, AgentStatus


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestDevOpsAgent:
    """Tests for DevOpsAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test DevOps agent initialization."""
        from aurora_dev.agents.specialized.devops import DevOpsAgent
        
        agent = DevOpsAgent()
        
        assert agent.name == "DevOps"
        assert agent.role == AgentRole.DEVOPS
        assert agent.status == AgentStatus.IDLE

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has DevOps responsibilities."""
        from aurora_dev.agents.specialized.devops import DevOpsAgent
        
        agent = DevOpsAgent()
        prompt = agent.system_prompt
        
        assert "CI/CD" in prompt
        assert "Docker" in prompt
        assert "Kubernetes" in prompt

    @patch("aurora_dev.agents.specialized.devops.DevOpsAgent._call_api")
    def test_create_dockerfile(self, mock_api, mock_anthropic):
        """Test Dockerfile creation."""
        from aurora_dev.agents.specialized.devops import DevOpsAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="FROM python:3.11-slim\nWORKDIR /app",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = DevOpsAgent()
        result = agent.create_dockerfile(
            language="python",
            framework="fastapi",
            port=8000,
        )
        
        assert result["success"]
        assert "FROM python" in result["dockerfile"]

    @patch("aurora_dev.agents.specialized.devops.DevOpsAgent._call_api")
    def test_create_ci_pipeline(self, mock_api, mock_anthropic):
        """Test CI pipeline creation."""
        from aurora_dev.agents.specialized.devops import DevOpsAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="name: CI\non: push\njobs: {}",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = DevOpsAgent()
        result = agent.create_ci_pipeline(
            platform="github",
            stages=["lint", "test", "build"],
        )
        
        assert result["success"]
        assert result["platform"] == "github"


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestDocumentationAgent:
    """Tests for DocumentationAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test Documentation agent initialization."""
        from aurora_dev.agents.specialized.devops import DocumentationAgent
        
        agent = DocumentationAgent()
        
        assert agent.name == "Documentation"
        assert agent.role == AgentRole.DOCUMENTATION

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has documentation responsibilities."""
        from aurora_dev.agents.specialized.devops import DocumentationAgent
        
        agent = DocumentationAgent()
        prompt = agent.system_prompt
        
        assert "API documentation" in prompt
        assert "README" in prompt
        assert "runbooks" in prompt

    @patch("aurora_dev.agents.specialized.devops.DocumentationAgent._call_api")
    def test_generate_readme(self, mock_api, mock_anthropic):
        """Test README generation."""
        from aurora_dev.agents.specialized.devops import DocumentationAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="# Project Name\n\nA cool project",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = DocumentationAgent()
        result = agent.generate_readme(
            project_name="TestProject",
            description="A test project",
            features=["Feature 1"],
            tech_stack=["Python"],
        )
        
        assert result["success"]
        assert "# Project Name" in result["readme"]


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestResearchAgent:
    """Tests for ResearchAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test Research agent initialization."""
        from aurora_dev.agents.specialized.devops import ResearchAgent
        
        agent = ResearchAgent()
        
        assert agent.name == "Research"
        assert agent.role == AgentRole.RESEARCH

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has research responsibilities."""
        from aurora_dev.agents.specialized.devops import ResearchAgent
        
        agent = ResearchAgent()
        prompt = agent.system_prompt
        
        assert "research" in prompt.lower()
        assert "best practices" in prompt
        assert "CVE" in prompt

    @patch("aurora_dev.agents.specialized.devops.ResearchAgent._call_api")
    def test_research_technology(self, mock_api, mock_anthropic):
        """Test technology research."""
        from aurora_dev.agents.specialized.devops import ResearchAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="FastAPI is a modern Python framework...",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = ResearchAgent()
        result = agent.research_technology(
            topic="Python web frameworks",
            requirements=["async", "fast"],
        )
        
        assert result["success"]
        assert result["topic"] == "Python web frameworks"

    @patch("aurora_dev.agents.specialized.devops.ResearchAgent._call_api")
    def test_compare_solutions(self, mock_api, mock_anthropic):
        """Test solution comparison."""
        from aurora_dev.agents.specialized.devops import ResearchAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="| Feature | FastAPI | Flask |\n|---|---|---|",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = ResearchAgent()
        result = agent.compare_solutions(
            category="Web Frameworks",
            options=["FastAPI", "Flask", "Django"],
            criteria=["performance", "ecosystem"],
        )
        
        assert result["success"]


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestArchitectAgent:
    """Tests for ArchitectAgent class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test Architect agent initialization."""
        from aurora_dev.agents.specialized.architect import ArchitectAgent
        
        agent = ArchitectAgent()
        
        assert agent.name == "Architect"
        assert agent.role == AgentRole.ARCHITECT

    def test_system_prompt_contains_responsibilities(self, mock_anthropic):
        """Test system prompt has architect responsibilities."""
        from aurora_dev.agents.specialized.architect import ArchitectAgent
        
        agent = ArchitectAgent()
        prompt = agent.system_prompt
        
        assert "System Design" in prompt
        assert "microservices" in prompt
        assert "API Contracts" in prompt

    @patch("aurora_dev.agents.specialized.architect.ArchitectAgent._call_api")
    def test_design_architecture(self, mock_api, mock_anthropic):
        """Test architecture design."""
        from aurora_dev.agents.specialized.architect import ArchitectAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content=json.dumps({
                "architecture_style": "microservices",
                "rationale": "Independent scaling",
                "services": [],
                "adr": {"id": "ADR-001", "title": "Use microservices"}
            }),
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = ArchitectAgent()
        result = agent.design_architecture(
            requirements="Build e-commerce platform",
            constraints={"team_size": 15},
        )
        
        assert result.get("architecture_style") == "microservices"

    @patch("aurora_dev.agents.specialized.architect.ArchitectAgent._call_api")
    def test_generate_database_schema(self, mock_api, mock_anthropic):
        """Test database schema generation."""
        from aurora_dev.agents.specialized.architect import ArchitectAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="CREATE TABLE users (id UUID PRIMARY KEY);",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = ArchitectAgent()
        schema = agent.generate_database_schema(
            entities=["users", "orders"],
            database_type="postgresql",
        )
        
        assert "CREATE TABLE" in schema

    @patch("aurora_dev.agents.specialized.architect.ArchitectAgent._call_api")
    def test_generate_diagram(self, mock_api, mock_anthropic):
        """Test diagram generation."""
        from aurora_dev.agents.specialized.architect import ArchitectAgent
        from aurora_dev.agents.base_agent import AgentResponse, TokenUsage
        
        mock_api.return_value = AgentResponse(
            content="graph TD\n  A[Client] --> B[Server]",
            token_usage=TokenUsage(10, 50, 60),
            model="claude-3-5-haiku",
            stop_reason="end_turn",
            execution_time_ms=100,
        )
        
        agent = ArchitectAgent()
        diagram = agent.generate_diagram(
            diagram_type="c4_context",
            components=["Client", "Server", "Database"],
        )
        
        assert "graph" in diagram or "flowchart" in diagram or "Client" in diagram
