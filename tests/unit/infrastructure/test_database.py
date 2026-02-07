"""Unit tests for database infrastructure."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestDatabaseModels:
    """Tests for database models."""

    def test_project_model_creation(self):
        """Test creating a Project model."""
        from aurora_dev.infrastructure.database.models import Project
        
        project = Project(
            name="Test Project",
            description="A test project",
            repository_url="https://github.com/test/repo",
        )
        
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.repository_url == "https://github.com/test/repo"

    def test_task_model_creation(self):
        """Test creating a Task model."""
        from aurora_dev.infrastructure.database.models import Task, TaskStatus
        
        # Set status explicitly since column defaults only apply on INSERT
        task = Task(
            project_id=uuid.uuid4(),
            name="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=5,
            complexity_score=3,
            attempt_count=0,
            max_attempts=5,
        )
        
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 5
        assert task.attempt_count == 0
        assert task.max_attempts == 5

    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        from aurora_dev.infrastructure.database.models import TaskStatus
        
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_agent_session_model_creation(self):
        """Test creating an AgentSession model."""
        from aurora_dev.infrastructure.database.models import (
            AgentSession,
            AgentSessionStatus,
        )
        
        # Set defaults explicitly since column defaults only apply on INSERT
        session = AgentSession(
            project_id=uuid.uuid4(),
            agent_type="backend",
            agent_name="Backend Agent 1",
            model_name="claude-sonnet-4-20250514",
            status=AgentSessionStatus.IDLE,
            total_tokens_used=0,
            total_api_cost=0,
        )
        
        assert session.agent_type == "backend"
        assert session.status == AgentSessionStatus.IDLE
        assert session.total_tokens_used == 0
        assert session.total_api_cost == 0

    def test_architecture_decision_model_creation(self):
        """Test creating an ArchitectureDecision model."""
        from aurora_dev.infrastructure.database.models import ArchitectureDecision
        
        # Set status explicitly since column defaults only apply on INSERT
        adr = ArchitectureDecision(
            project_id=uuid.uuid4(),
            title="Use PostgreSQL for data storage",
            context="Need a reliable relational database",
            decision="Use PostgreSQL 15",
            rationale="Battle-tested, ACID compliant, good performance",
            status="proposed",
        )
        
        assert adr.title == "Use PostgreSQL for data storage"
        assert adr.status == "proposed"

    def test_reflection_model_creation(self):
        """Test creating a Reflection model."""
        from aurora_dev.infrastructure.database.models import Reflection
        
        reflection = Reflection(
            task_id=uuid.uuid4(),
            agent_session_id=uuid.uuid4(),
            attempt_number=1,
            self_critique="Need to handle edge cases better",
            improved_approach="Added input validation",
            success=True,
        )
        
        assert reflection.attempt_number == 1
        assert reflection.success is True


class TestConnectionModule:
    """Tests for database connection module."""

    @patch("aurora_dev.infrastructure.database.connection.create_engine")
    def test_get_engine_returns_engine(self, mock_create_engine, mock_settings):
        """Test that get_engine returns an engine."""
        from aurora_dev.infrastructure.database.connection import get_engine, close_engine
        
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        engine = get_engine()
        assert engine is mock_engine
        mock_create_engine.assert_called_once()
        
        # Cleanup
        close_engine()

    @patch("aurora_dev.infrastructure.database.connection.create_engine")
    def test_get_session_factory_returns_factory(self, mock_create_engine, mock_settings):
        """Test that get_session_factory returns a session factory."""
        from aurora_dev.infrastructure.database.connection import (
            get_session_factory,
            close_engine,
        )
        
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        factory = get_session_factory()
        assert factory is not None
        assert callable(factory)
        
        # Cleanup
        close_engine()
