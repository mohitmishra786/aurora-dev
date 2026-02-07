"""Unit tests for Memory Coordinator Agent."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from aurora_dev.agents.base_agent import AgentRole, AgentStatus


class TestMemoryType:
    """Tests for MemoryType enum."""

    def test_memory_type_values(self):
        """Test memory type enum values."""
        from aurora_dev.agents.specialized.memory_coordinator import MemoryType
        
        assert MemoryType.SHORT_TERM.value == "short_term"
        assert MemoryType.LONG_TERM.value == "long_term"
        assert MemoryType.EPISODIC.value == "episodic"


class TestMemoryItem:
    """Tests for MemoryItem dataclass."""

    def test_memory_item_creation(self):
        """Test creating a memory item."""
        from aurora_dev.agents.specialized.memory_coordinator import MemoryItem, MemoryType
        
        item = MemoryItem(
            id="test-id",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
        )
        
        assert item.id == "test-id"
        assert item.content == "Test content"
        assert item.memory_type == MemoryType.SHORT_TERM
        assert item.relevance_score == 1.0
        assert item.access_count == 0

    def test_memory_item_to_dict(self):
        """Test converting memory item to dict."""
        from aurora_dev.agents.specialized.memory_coordinator import MemoryItem, MemoryType
        
        item = MemoryItem(
            id="test-id",
            content="Test content",
            memory_type=MemoryType.LONG_TERM,
            tags=["test", "unit"],
        )
        
        data = item.to_dict()
        
        assert data["id"] == "test-id"
        assert data["content"] == "Test content"
        assert data["memory_type"] == "long_term"
        assert data["tags"] == ["test", "unit"]

    def test_memory_item_from_dict(self):
        """Test creating memory item from dict."""
        from aurora_dev.agents.specialized.memory_coordinator import MemoryItem, MemoryType
        
        data = {
            "id": "test-id",
            "content": "Test content",
            "memory_type": "episodic",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "metadata": {"key": "value"},
            "tags": ["test"],
            "relevance_score": 0.8,
            "access_count": 5,
            "last_accessed": None,
        }
        
        item = MemoryItem.from_dict(data)
        
        assert item.id == "test-id"
        assert item.memory_type == MemoryType.EPISODIC
        assert item.relevance_score == 0.8


class TestArchitectureDecision:
    """Tests for ArchitectureDecision dataclass."""

    def test_adr_creation(self):
        """Test creating an ADR."""
        from aurora_dev.agents.specialized.memory_coordinator import ArchitectureDecision
        
        adr = ArchitectureDecision(
            id="ADR-001",
            title="Use PostgreSQL for primary database",
            context="Need a reliable relational database",
            decision="Use PostgreSQL",
            rationale="ACID compliance and JSON support",
        )
        
        assert adr.id == "ADR-001"
        assert adr.status == "accepted"

    def test_adr_to_dict(self):
        """Test converting ADR to dict."""
        from aurora_dev.agents.specialized.memory_coordinator import ArchitectureDecision
        
        adr = ArchitectureDecision(
            id="ADR-002",
            title="Test ADR",
            context="Context",
            decision="Decision",
            rationale="Rationale",
            tags=["database"],
        )
        
        data = adr.to_dict()
        
        assert data["id"] == "ADR-002"
        assert data["tags"] == ["database"]


class TestReflection:
    """Tests for Reflection dataclass."""

    def test_reflection_creation(self):
        """Test creating a reflection."""
        from aurora_dev.agents.specialized.memory_coordinator import Reflection
        
        reflection = Reflection(
            id="refl-001",
            task_id="task-001",
            agent_id="agent-001",
            attempt_number=1,
            self_critique="Could have been more thorough",
            improved_approach="Add more validation",
            lessons_learned=["Validate early"],
        )
        
        assert reflection.task_id == "task-001"
        assert reflection.attempt_number == 1

    def test_reflection_to_dict(self):
        """Test converting reflection to dict."""
        from aurora_dev.agents.specialized.memory_coordinator import Reflection
        
        reflection = Reflection(
            id="refl-002",
            task_id="task-002",
            agent_id="agent-002",
            attempt_number=2,
            self_critique="Critique",
            improved_approach="Approach",
        )
        
        data = reflection.to_dict()
        
        assert data["attempt_number"] == 2


@patch("aurora_dev.agents.base_agent.Anthropic")
class TestMemoryCoordinator:
    """Tests for MemoryCoordinator class."""

    def setup_method(self):
        """Reset registry before each test."""
        from aurora_dev.agents.registry import get_registry
        registry = get_registry()
        registry._agents.clear()
        registry._role_index.clear()
        registry._project_index.clear()

    def test_initialization(self, mock_anthropic):
        """Test Memory Coordinator initialization."""
        from aurora_dev.agents.specialized.memory_coordinator import MemoryCoordinator
        
        coordinator = MemoryCoordinator()
        
        assert coordinator.name == "MemoryCoordinator"
        assert coordinator.role == AgentRole.MEMORY_COORDINATOR

    def test_store_short_term(self, mock_anthropic):
        """Test storing short-term memory."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        item = coordinator.store(
            content="Current file: main.py",
            memory_type=MemoryType.SHORT_TERM,
            tags=["file", "active"],
        )
        
        assert item.content == "Current file: main.py"
        assert item.memory_type == MemoryType.SHORT_TERM
        stats = coordinator.get_stats()
        assert stats["short_term_count"] == 1

    def test_store_long_term(self, mock_anthropic):
        """Test storing long-term memory."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        item = coordinator.store(
            content="Use repository pattern for data access",
            memory_type=MemoryType.LONG_TERM,
            tags=["pattern", "architecture"],
        )
        
        assert item.memory_type == MemoryType.LONG_TERM
        stats = coordinator.get_stats()
        assert stats["long_term_count"] == 1
        assert stats["embedding_count"] == 1

    def test_retrieve_by_query(self, mock_anthropic):
        """Test retrieving memories by query."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        coordinator.store(
            "Use PostgreSQL for user data",
            MemoryType.LONG_TERM,
        )
        coordinator.store(
            "Use Redis for caching",
            MemoryType.LONG_TERM,
        )
        
        results = coordinator.retrieve("PostgreSQL database", limit=5)
        
        assert len(results) >= 1

    def test_retrieve_with_type_filter(self, mock_anthropic):
        """Test retrieving with memory type filter."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        coordinator.store("Short term", MemoryType.SHORT_TERM)
        coordinator.store("Long term", MemoryType.LONG_TERM)
        
        short_results = coordinator.retrieve(
            "term",
            memory_type=MemoryType.SHORT_TERM,
        )
        
        for item in short_results:
            assert item.memory_type == MemoryType.SHORT_TERM

    def test_store_decision(self, mock_anthropic):
        """Test storing an architecture decision."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            ArchitectureDecision,
            MemoryCoordinator,
        )
        
        coordinator = MemoryCoordinator()
        
        adr = ArchitectureDecision(
            id="ADR-001",
            title="Database Selection",
            context="Need a database",
            decision="Use PostgreSQL",
            rationale="ACID compliance",
            tags=["database"],
        )
        
        coordinator.store_decision(adr)
        
        stats = coordinator.get_stats()
        assert stats["adr_count"] == 1

    def test_store_reflection(self, mock_anthropic):
        """Test storing a reflection."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            Reflection,
        )
        
        coordinator = MemoryCoordinator()
        
        reflection = Reflection(
            id="refl-001",
            task_id="task-001",
            agent_id="agent-001",
            attempt_number=1,
            self_critique="Missed edge case",
            improved_approach="Add boundary checks",
            lessons_learned=["Always check boundaries"],
        )
        
        coordinator.store_reflection(reflection)
        
        stats = coordinator.get_stats()
        assert stats["reflection_count"] == 1

    def test_apply_decay(self, mock_anthropic):
        """Test memory decay application."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        item = coordinator.store("Test content", MemoryType.SHORT_TERM)
        # Simulate old access
        item.last_accessed = datetime.now(timezone.utc) - timedelta(days=14)
        
        affected = coordinator.apply_decay(decay_rate=0.1)
        
        assert affected >= 1

    def test_prune_low_relevance(self, mock_anthropic):
        """Test pruning low-relevance memories."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        item = coordinator.store("Low relevance", MemoryType.SHORT_TERM)
        item.relevance_score = 0.1
        
        pruned = coordinator.prune(threshold=0.2)
        
        assert pruned >= 1
        stats = coordinator.get_stats()
        assert stats["short_term_count"] == 0

    def test_get_stats(self, mock_anthropic):
        """Test getting memory statistics."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        coordinator.store("Short", MemoryType.SHORT_TERM)
        coordinator.store("Long", MemoryType.LONG_TERM)
        coordinator.store("Episode", MemoryType.EPISODIC)
        
        stats = coordinator.get_stats()
        
        assert stats["short_term_count"] == 1
        assert stats["long_term_count"] == 1
        assert stats["episodic_count"] == 1

    def test_access_count_increases(self, mock_anthropic):
        """Test that access count increases on retrieve."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        coordinator.store("Database patterns", MemoryType.LONG_TERM)
        
        # First retrieve
        results = coordinator.retrieve("Database", limit=1)
        if results:
            assert results[0].access_count >= 1

    def test_relevance_boost_on_access(self, mock_anthropic):
        """Test that relevance score increases on access."""
        from aurora_dev.agents.specialized.memory_coordinator import (
            MemoryCoordinator,
            MemoryType,
        )
        
        coordinator = MemoryCoordinator()
        
        item = coordinator.store("Frequently accessed", MemoryType.LONG_TERM)
        initial_relevance = item.relevance_score
        
        # Access it
        coordinator.retrieve("Frequently", limit=1)
        
        # Check if relevance increased (capped at 1.0)
        assert item.relevance_score >= initial_relevance
