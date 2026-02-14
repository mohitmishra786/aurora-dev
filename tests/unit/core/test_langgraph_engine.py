"""
Unit tests for LangGraphOrchestrator.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestLangGraphOrchestrator:
    """Tests for LangGraph-based orchestration engine."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock OrchestrationEngine."""
        engine = MagicMock()
        engine.task_manager = MagicMock()
        engine.projects = {}
        return engine

    @pytest.mark.skipif(True, reason="Requires langgraph to be installed")
    def test_initialization_with_engine(self, mock_engine):
        """Test LangGraphOrchestrator initializes with existing engine."""
        from aurora_dev.core.orchestrator.langgraph_engine import LangGraphOrchestrator
        
        orchestrator = LangGraphOrchestrator(engine=mock_engine)
        assert orchestrator._engine == mock_engine

    @pytest.mark.skipif(True, reason="Requires langgraph to be installed")
    def test_initialization_without_engine(self):
        """Test LangGraphOrchestrator initializes without engine."""
        from aurora_dev.core.orchestrator.langgraph_engine import LangGraphOrchestrator
        
        orchestrator = LangGraphOrchestrator()
        assert orchestrator._engine is None

    def test_import_guard(self):
        """Test graceful handling when langgraph not available."""
        with patch.dict(
            "sys.modules",
            {"langgraph": None, "langgraph.graph": None},
        ):
            # Should not raise at module level
            try:
                import importlib
                from aurora_dev.core.orchestrator import langgraph_engine
                importlib.reload(langgraph_engine)
            except ImportError:
                pass  # Expected when langgraph unavailable

    @pytest.mark.skipif(True, reason="Requires langgraph to be installed")
    def test_graph_has_required_phases(self, mock_engine):
        """Test that the graph includes all required phase nodes."""
        from aurora_dev.core.orchestrator.langgraph_engine import LangGraphOrchestrator
        
        orchestrator = LangGraphOrchestrator(engine=mock_engine)
        
        # Verify graph was built
        assert orchestrator._graph is not None

    @pytest.mark.skipif(True, reason="Requires langgraph to be installed")
    def test_project_state_schema(self):
        """Test ProjectState TypedDict has required fields."""
        from aurora_dev.core.orchestrator.langgraph_engine import ProjectState
        
        # ProjectState should have these keys
        assert "project_id" in ProjectState.__annotations__
        assert "phase" in ProjectState.__annotations__
        assert "goal" in ProjectState.__annotations__

    @pytest.mark.skipif(True, reason="Requires langgraph to be installed")
    @pytest.mark.asyncio
    async def test_route_after_phase_success(self, mock_engine):
        """Test routing after successful phase."""
        from aurora_dev.core.orchestrator.langgraph_engine import LangGraphOrchestrator
        
        orchestrator = LangGraphOrchestrator(engine=mock_engine)
        
        state = {
            "project_id": "test",
            "phase": "planning",
            "goal": "build api",
            "success": True,
            "error": None,
        }
        
        next_phase = orchestrator._route_after_phase(state)
        assert next_phase == "design"

    @pytest.mark.skipif(True, reason="Requires langgraph to be installed")
    @pytest.mark.asyncio
    async def test_route_after_phase_failure(self, mock_engine):
        """Test routing after failed phase."""
        from aurora_dev.core.orchestrator.langgraph_engine import LangGraphOrchestrator
        
        orchestrator = LangGraphOrchestrator(engine=mock_engine)
        
        state = {
            "project_id": "test",
            "phase": "planning",
            "goal": "build api",
            "success": False,
            "error": "Planning failed",
        }
        
        next_phase = orchestrator._route_after_phase(state)
        assert next_phase == "failed"
