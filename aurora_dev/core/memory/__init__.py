"""
Advanced Memory Module for AURORA-DEV.

Provides context pruning, memory compression, and
cross-project learning capabilities.
"""
from aurora_dev.core.memory.context_pruner import (
    ContextPruner,
    PruneStrategy,
    PruneResult,
)
from aurora_dev.core.memory.compression import (
    MemoryCompressor,
    CompressionStrategy,
)
from aurora_dev.core.memory.cross_project import (
    CrossProjectLearning,
    ProjectPattern,
)

__all__ = [
    "ContextPruner",
    "PruneStrategy",
    "PruneResult",
    "MemoryCompressor",
    "CompressionStrategy",
    "CrossProjectLearning",
    "ProjectPattern",
]
