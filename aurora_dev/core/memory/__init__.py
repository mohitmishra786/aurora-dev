"""
Memory management for AURORA-DEV agents.

Provides context compression, pruning, and cross-project learning.
"""
from aurora_dev.core.memory.compression import (
    MemoryCompressor,
    CompressionResult,
    MemoryEntry,
)
from aurora_dev.core.memory.context_pruner import (
    ContextPruner,
    PruneResult,
)
from aurora_dev.core.memory.cross_project import (
    CrossProjectLearning,
    PatternCategory,
)

# Vector store and Mem0 (optional dependencies)
try:
    from aurora_dev.core.memory.vector_store import (
        VectorStore,
        VectorEntry,
        SearchResult,
        AgentMemory,
    )
except ImportError:
    VectorStore = None  # type: ignore
    VectorEntry = None  # type: ignore
    SearchResult = None  # type: ignore
    AgentMemory = None  # type: ignore

try:
    from aurora_dev.core.memory.mem0_client import (
        Mem0Client,
        MemoryRecord,
        AgentMem0,
    )
except ImportError:
    Mem0Client = None  # type: ignore
    MemoryRecord = None  # type: ignore
    AgentMem0 = None  # type: ignore

__all__ = [
    "MemoryCompressor",
    "CompressionResult",
    "MemoryEntry",
    "ContextPruner",
    "PruneResult",
    "CrossProjectLearning",
    "PatternCategory",
    "VectorStore",
    "VectorEntry",
    "SearchResult",
    "AgentMemory",
    "Mem0Client",
    "MemoryRecord",
    "AgentMem0",
]


