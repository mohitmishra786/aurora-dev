"""
Context pruning module for token budget management.

Intelligently prunes context to fit within token limits
while retaining the most relevant information.

Example usage:
    >>> pruner = ContextPruner(max_tokens=8000)
    >>> result = await pruner.prune(context_items, relevance_query="database optimization")
    >>> print(f"Kept {result.items_kept}, removed {result.items_removed}")
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class PruneStrategy(Enum):
    """Strategies for context pruning."""
    
    RECENCY = "recency"  # Keep most recent items
    RELEVANCE = "relevance"  # Keep most relevant to query
    IMPORTANCE = "importance"  # Keep highest importance score
    HYBRID = "hybrid"  # Combination of all factors


@dataclass
class ContextItem:
    """An item in the context window."""
    
    id: str
    content: str
    token_count: int
    timestamp: datetime
    importance: float = 0.5  # 0.0 to 1.0
    relevance_score: float = 0.0  # Computed on-demand
    source: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class PruneResult:
    """Result of a pruning operation."""
    
    kept_items: list[ContextItem]
    removed_items: list[ContextItem]
    original_tokens: int
    final_tokens: int
    items_kept: int
    items_removed: int
    strategy_used: PruneStrategy
    prune_time_ms: float


class ContextPruner:
    """
    Intelligent context pruner for token budget management.
    
    Uses multiple strategies to select which context items
    to keep when the total exceeds the token budget.
    
    Attributes:
        max_tokens: Maximum tokens allowed in context.
        reserve_tokens: Tokens to reserve for response.
        strategy: Default pruning strategy.
    """
    
    # Weights for hybrid strategy
    RECENCY_WEIGHT = 0.3
    RELEVANCE_WEIGHT = 0.4
    IMPORTANCE_WEIGHT = 0.3
    
    def __init__(
        self,
        max_tokens: int = 100000,
        reserve_tokens: int = 4000,
        strategy: PruneStrategy = PruneStrategy.HYBRID,
    ):
        """
        Initialize the context pruner.
        
        Args:
            max_tokens: Maximum tokens in context window.
            reserve_tokens: Tokens to reserve for response.
            strategy: Default pruning strategy.
        """
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self.strategy = strategy
        self._logger = get_logger(__name__)
    
    @property
    def available_tokens(self) -> int:
        """Tokens available for context."""
        return self.max_tokens - self.reserve_tokens
    
    async def prune(
        self,
        items: list[ContextItem],
        relevance_query: Optional[str] = None,
        strategy: Optional[PruneStrategy] = None,
        required_ids: Optional[set[str]] = None,
    ) -> PruneResult:
        """
        Prune context items to fit within token budget.
        
        Args:
            items: List of context items to prune.
            relevance_query: Optional query for relevance scoring.
            strategy: Override default strategy.
            required_ids: IDs of items that must be kept.
            
        Returns:
            PruneResult with kept and removed items.
        """
        import time
        start = time.time()
        
        strategy = strategy or self.strategy
        required_ids = required_ids or set()
        
        # Calculate total tokens
        original_tokens = sum(item.token_count for item in items)
        
        # If within budget, keep all
        if original_tokens <= self.available_tokens:
            return PruneResult(
                kept_items=items,
                removed_items=[],
                original_tokens=original_tokens,
                final_tokens=original_tokens,
                items_kept=len(items),
                items_removed=0,
                strategy_used=strategy,
                prune_time_ms=(time.time() - start) * 1000,
            )
        
        # Compute relevance scores if needed
        if relevance_query and strategy in [PruneStrategy.RELEVANCE, PruneStrategy.HYBRID]:
            await self._compute_relevance_scores(items, relevance_query)
        
        # Score items based on strategy
        scored_items = self._score_items(items, strategy)
        
        # Separate required and optional items
        required = [item for item in scored_items if item.id in required_ids]
        optional = [item for item in scored_items if item.id not in required_ids]
        
        # Sort optional by score (highest first)
        optional.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Build kept list starting with required
        kept_items = list(required)
        kept_tokens = sum(item.token_count for item in kept_items)
        removed_items = []
        
        # Add optional items until budget exhausted
        for item in optional:
            if kept_tokens + item.token_count <= self.available_tokens:
                kept_items.append(item)
                kept_tokens += item.token_count
            else:
                removed_items.append(item)
        
        elapsed = (time.time() - start) * 1000
        
        self._logger.info(
            f"Pruned context: {len(items)} -> {len(kept_items)} items, "
            f"{original_tokens} -> {kept_tokens} tokens"
        )
        
        return PruneResult(
            kept_items=kept_items,
            removed_items=removed_items,
            original_tokens=original_tokens,
            final_tokens=kept_tokens,
            items_kept=len(kept_items),
            items_removed=len(removed_items),
            strategy_used=strategy,
            prune_time_ms=elapsed,
        )
    
    def _score_items(
        self,
        items: list[ContextItem],
        strategy: PruneStrategy,
    ) -> list[ContextItem]:
        """Score items based on strategy."""
        now = datetime.now()
        
        for item in items:
            if strategy == PruneStrategy.RECENCY:
                # Score by recency (higher = more recent)
                age_hours = (now - item.timestamp).total_seconds() / 3600
                item.relevance_score = max(0, 1.0 - (age_hours / 24))
                
            elif strategy == PruneStrategy.IMPORTANCE:
                # Use importance directly
                item.relevance_score = item.importance
                
            elif strategy == PruneStrategy.RELEVANCE:
                # Relevance score already computed
                pass
                
            elif strategy == PruneStrategy.HYBRID:
                # Combine all factors
                age_hours = (now - item.timestamp).total_seconds() / 3600
                recency_score = max(0, 1.0 - (age_hours / 24))
                
                item.relevance_score = (
                    self.RECENCY_WEIGHT * recency_score +
                    self.RELEVANCE_WEIGHT * item.relevance_score +
                    self.IMPORTANCE_WEIGHT * item.importance
                )
        
        return items
    
    async def _compute_relevance_scores(
        self,
        items: list[ContextItem],
        query: str,
    ) -> None:
        """
        Compute relevance scores for items based on query.
        
        Uses keyword matching as fallback if embeddings not available.
        """
        query_terms = set(query.lower().split())
        
        for item in items:
            content_terms = set(item.content.lower().split())
            
            # Compute Jaccard similarity
            intersection = query_terms & content_terms
            union = query_terms | content_terms
            
            if union:
                item.relevance_score = len(intersection) / len(union)
            else:
                item.relevance_score = 0.0
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Uses simple heuristic: ~4 characters per token.
        """
        return len(text) // 4


class HierarchicalContextManager:
    """
    Manages hierarchical context at different scopes.
    
    Levels:
        - Project: Persists across sessions
        - Session: Current user session
        - Task: Current task only
        - Agent: Agent-specific context
    """
    
    def __init__(self, pruner: Optional[ContextPruner] = None):
        """Initialize with optional pruner."""
        self.pruner = pruner or ContextPruner()
        self._contexts: dict[str, dict[str, list[ContextItem]]] = {
            "project": {},
            "session": {},
            "task": {},
            "agent": {},
        }
        self._logger = get_logger(__name__)
    
    def add_item(
        self,
        level: str,
        scope_id: str,
        item: ContextItem,
    ) -> None:
        """
        Add item to a context level.
        
        Args:
            level: Context level (project, session, task, agent).
            scope_id: Unique ID for the scope.
            item: Context item to add.
        """
        if level not in self._contexts:
            raise ValueError(f"Invalid level: {level}")
        
        if scope_id not in self._contexts[level]:
            self._contexts[level][scope_id] = []
        
        self._contexts[level][scope_id].append(item)
    
    def get_items(
        self,
        level: str,
        scope_id: str,
    ) -> list[ContextItem]:
        """Get items from a context level."""
        if level not in self._contexts:
            return []
        return self._contexts[level].get(scope_id, [])
    
    async def get_merged_context(
        self,
        project_id: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> list[ContextItem]:
        """
        Get merged context from all applicable levels.
        
        Automatically prunes to fit within token budget.
        """
        all_items = []
        
        # Project context (always included, lower priority)
        project_items = self.get_items("project", project_id)
        for item in project_items:
            item.importance = min(item.importance, 0.3)  # Cap project importance
        all_items.extend(project_items)
        
        # Session context
        if session_id:
            session_items = self.get_items("session", session_id)
            for item in session_items:
                item.importance = min(item.importance, 0.5)
            all_items.extend(session_items)
        
        # Task context (higher priority)
        if task_id:
            task_items = self.get_items("task", task_id)
            for item in task_items:
                item.importance = max(item.importance, 0.7)
            all_items.extend(task_items)
        
        # Agent context
        if agent_id:
            agent_items = self.get_items("agent", agent_id)
            all_items.extend(agent_items)
        
        # Prune if needed
        if max_tokens:
            self.pruner.max_tokens = max_tokens
        
        result = await self.pruner.prune(all_items, strategy=PruneStrategy.HYBRID)
        return result.kept_items
    
    def clear_level(self, level: str, scope_id: Optional[str] = None) -> None:
        """
        Clear a context level.
        
        Args:
            level: Level to clear.
            scope_id: Optional specific scope (clears all if None).
        """
        if level not in self._contexts:
            return
        
        if scope_id:
            self._contexts[level].pop(scope_id, None)
        else:
            self._contexts[level] = {}
