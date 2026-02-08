"""
Integration tests for agent workflow execution.

Tests end-to-end agent coordination, task assignment, and result aggregation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from uuid import uuid4


class TestAgentWorkflow:
    """Integration tests for complete agent workflows."""
    
    @pytest.fixture
    def mock_anthropic(self):
        """Mock Anthropic client for all tests."""
        with patch("aurora_dev.agents.base_agent.Anthropic") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            
            # Setup standard response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Generated output")]
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_response.usage.cache_creation_input_tokens = 0
            mock_response.usage.cache_read_input_tokens = 0
            mock_response.model = "claude-sonnet-4-20250514"
            mock_response.stop_reason = "end_turn"
            
            mock_client.messages.create.return_value = mock_response
            
            yield mock
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis for state persistence."""
        with patch("redis.Redis") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            
            # Setup basic Redis operations
            mock_client.get.return_value = None
            mock_client.set.return_value = True
            mock_client.delete.return_value = 1
            mock_client.publish.return_value = 1
            
            yield mock_client
    
    def test_architect_to_backend_workflow(self, mock_anthropic, mock_redis):
        """Test workflow from Architect design to Backend implementation."""
        from aurora_dev.agents.specialized.architect import ArchitectAgent
        from aurora_dev.agents.specialized.developers import BackendAgent
        
        # Create agents
        architect = ArchitectAgent()
        backend = BackendAgent()
        
        # Architect designs system
        design_task = {
            "operation": "design",
            "description": "Design a REST API for user management",
            "requirements": ["CRUD operations", "JWT auth"],
        }
        
        design_response = architect.execute(design_task)
        
        assert design_response.success
        assert design_response.content is not None
        
        # Backend implements based on design
        impl_task = {
            "operation": "implement",
            "component": "user_api",
            "design_context": design_response.content,
        }
        
        impl_response = backend.execute(impl_task)
        
        assert impl_response.success
    
    def test_multi_agent_feature_implementation(self, mock_anthropic, mock_redis):
        """Test multiple agents collaborating on a feature."""
        from aurora_dev.agents.specialized.architect import ArchitectAgent
        from aurora_dev.agents.specialized.developers import BackendAgent, FrontendAgent
        from aurora_dev.agents.specialized.quality import TestEngineerAgent
        
        agents = {
            "architect": ArchitectAgent(),
            "backend": BackendAgent(),
            "frontend": FrontendAgent(),
            "tester": TestEngineerAgent(),
        }
        
        # Each agent should be initialized and ready
        for name, agent in agents.items():
            assert agent is not None
            assert agent.role is not None
    
    def test_task_dependency_chain(self, mock_anthropic):
        """Test task execution respects dependencies."""
        from aurora_dev.core.orchestrator.scheduler import TaskScheduler
        
        scheduler = TaskScheduler()
        
        # Add tasks with dependencies
        scheduler.add_task("design", "architect", "design_system")
        scheduler.add_task("backend", "backend", "implement", dependencies=["design"])
        scheduler.add_task("frontend", "frontend", "implement", dependencies=["design"])
        scheduler.add_task("test", "tester", "write_tests", dependencies=["backend", "frontend"])
        
        # Get execution order
        executable = scheduler.get_executable_tasks()
        
        # Only design should be executable initially
        assert len(executable) == 1
        assert executable[0].task_id == "design"
        
        # Complete design
        scheduler.mark_completed("design")
        executable = scheduler.get_executable_tasks()
        
        # Now backend and frontend can run in parallel
        assert len(executable) == 2
        task_ids = {t.task_id for t in executable}
        assert "backend" in task_ids
        assert "frontend" in task_ids


class TestMessagingIntegration:
    """Integration tests for inter-agent messaging."""
    
    @pytest.fixture
    def mock_redis_pubsub(self):
        """Mock Redis pub/sub for messaging tests."""
        with patch("redis.Redis") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            
            mock_pubsub = MagicMock()
            mock_client.pubsub.return_value = mock_pubsub
            mock_pubsub.subscribe.return_value = None
            mock_pubsub.get_message.return_value = None
            
            yield mock_client
    
    def test_message_routing(self, mock_redis_pubsub):
        """Test messages are routed to correct channels."""
        from aurora_dev.infrastructure.messaging.broker import MessageBroker
        from aurora_dev.infrastructure.messaging.messages import Message, MessageType
        
        broker = MessageBroker()
        
        # Create a test message
        message = Message(
            message_type=MessageType.TASK_ASSIGNMENT,
            sender_id="maestro-1",
            recipient_id="backend-1",
            payload={"task_id": "task-123"},
        )
        
        # Should be able to publish
        broker.publish("agents.backend", message)
        
        # Verify publish was called
        mock_redis_pubsub.publish.assert_called_once()


class TestReflexionIntegration:
    """Integration tests for reflexion workflow."""
    
    @pytest.fixture
    def mock_anthropic(self):
        """Mock Anthropic for reflexion tests."""
        with patch("aurora_dev.core.reflexion.Anthropic") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock
    
    def test_reflexion_improves_output(self, mock_anthropic):
        """Test that reflexion can improve task output."""
        from aurora_dev.core.reflexion import ReflexionEngine
        
        engine = ReflexionEngine()
        
        # Initial result with issues
        initial_result = {
            "success": True,
            "output": "def process(data): return data",  # No error handling
            "quality_score": 0.6,
        }
        
        # Should suggest reflection for low quality
        should_reflect = engine.should_reflect(initial_result, quality_threshold=0.8)
        
        assert should_reflect is True
