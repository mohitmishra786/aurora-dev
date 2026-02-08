"""
Tests for Advanced Memory module.
"""
import pytest
from datetime import datetime, timedelta


class TestContextPruner:
    """Tests for context pruner."""
    
    def test_prune_strategy_enum(self):
        """Test PruneStrategy enum values."""
        from aurora_dev.core.memory.context_pruner import PruneStrategy
        
        assert PruneStrategy.RECENCY.value == "recency"
        assert PruneStrategy.RELEVANCE.value == "relevance"
        assert PruneStrategy.HYBRID.value == "hybrid"
    
    def test_context_item_creation(self):
        """Test ContextItem creation."""
        from aurora_dev.core.memory.context_pruner import ContextItem
        
        item = ContextItem(
            id="test-1",
            content="Test content",
            token_count=10,
            timestamp=datetime.now(),
            importance=0.8,
        )
        
        assert item.id == "test-1"
        assert item.token_count == 10
        assert item.importance == 0.8
    
    def test_context_pruner_init(self):
        """Test ContextPruner initialization."""
        from aurora_dev.core.memory.context_pruner import ContextPruner
        
        pruner = ContextPruner(max_tokens=50000, reserve_tokens=2000)
        
        assert pruner.max_tokens == 50000
        assert pruner.reserve_tokens == 2000
        assert pruner.available_tokens == 48000
    
    @pytest.mark.asyncio
    async def test_prune_under_budget(self):
        """Test pruning when under budget."""
        from aurora_dev.core.memory.context_pruner import (
            ContextPruner, ContextItem, PruneStrategy
        )
        
        pruner = ContextPruner(max_tokens=1000, reserve_tokens=100)
        
        items = [
            ContextItem(id="1", content="a" * 100, token_count=25, timestamp=datetime.now()),
            ContextItem(id="2", content="b" * 100, token_count=25, timestamp=datetime.now()),
        ]
        
        result = await pruner.prune(items, strategy=PruneStrategy.RECENCY)
        
        assert result.items_kept == 2
        assert result.items_removed == 0
    
    def test_hierarchical_context_manager_init(self):
        """Test HierarchicalContextManager initialization."""
        from aurora_dev.core.memory.context_pruner import HierarchicalContextManager
        
        manager = HierarchicalContextManager()
        
        assert manager.get_items("project", "test") == []


class TestMemoryCompression:
    """Tests for memory compression."""
    
    def test_compression_strategy_enum(self):
        """Test CompressionStrategy enum values."""
        from aurora_dev.core.memory.compression import CompressionStrategy
        
        assert CompressionStrategy.SUMMARIZE.value == "summarize"
        assert CompressionStrategy.DEDUPLICATE.value == "deduplicate"
    
    def test_memory_compressor_init(self):
        """Test MemoryCompressor initialization."""
        from aurora_dev.core.memory.compression import MemoryCompressor
        
        compressor = MemoryCompressor(target_compression_ratio=0.25)
        
        assert compressor.target_compression_ratio == 0.25
    
    @pytest.mark.asyncio
    async def test_compress_short_content(self):
        """Test that short content is not compressed."""
        from aurora_dev.core.memory.compression import (
            MemoryCompressor, CompressionStrategy
        )
        
        compressor = MemoryCompressor(min_content_length=200)
        
        result = await compressor.compress(
            "Short text",
            strategy=CompressionStrategy.SUMMARIZE,
        )
        
        assert result.compression_ratio == 1.0
        assert result.strategy_used == CompressionStrategy.NONE
    
    @pytest.mark.asyncio
    async def test_deduplicate_content(self):
        """Test deduplication of content."""
        from aurora_dev.core.memory.compression import (
            MemoryCompressor, CompressionStrategy
        )
        
        compressor = MemoryCompressor(min_content_length=10)
        
        content = "Line one\nLine two\nLine one\nLine three\nLine two"
        
        result = await compressor.compress(
            content,
            strategy=CompressionStrategy.DEDUPLICATE,
        )
        
        lines = result.compressed_content.split("\n")
        assert len(lines) == 3  # Duplicates removed


class TestCrossProjectLearning:
    """Tests for cross-project learning."""
    
    def test_pattern_category_enum(self):
        """Test PatternCategory enum values."""
        from aurora_dev.core.memory.cross_project import PatternCategory
        
        assert PatternCategory.ARCHITECTURE.value == "architecture"
        assert PatternCategory.TESTING.value == "testing"
    
    def test_project_pattern_creation(self):
        """Test ProjectPattern creation."""
        from aurora_dev.core.memory.cross_project import (
            ProjectPattern, PatternCategory
        )
        
        pattern = ProjectPattern(
            id="pat-1",
            category=PatternCategory.ARCHITECTURE,
            name="Test Pattern",
            description="A test pattern",
            problem_context="Testing",
            solution_approach="Use tests",
            implementation_notes="Write unit tests",
            success_count=5,
            failure_count=1,
        )
        
        assert pattern.success_rate() == 5/6
        assert "architecture" in pattern.to_dict()["category"]
    
    def test_cross_project_learning_init(self):
        """Test CrossProjectLearning initialization."""
        from aurora_dev.core.memory.cross_project import CrossProjectLearning
        
        learning = CrossProjectLearning()
        
        assert learning.get_pattern_count() == 0
    
    @pytest.mark.asyncio
    async def test_register_pattern(self):
        """Test registering a pattern."""
        from aurora_dev.core.memory.cross_project import (
            CrossProjectLearning, ProjectPattern, PatternCategory
        )
        
        learning = CrossProjectLearning()
        
        pattern = ProjectPattern(
            id="",
            category=PatternCategory.TESTING,
            name="Unit Test Pattern",
            description="Write comprehensive unit tests",
            problem_context="Code quality",
            solution_approach="Test-driven development",
            implementation_notes="Use pytest",
        )
        
        pattern_id = await learning.register_pattern(pattern)
        
        assert pattern_id is not None
        assert learning.get_pattern_count() == 1
