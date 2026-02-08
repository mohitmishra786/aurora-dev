"""
Memory Coordinator Agent for AURORA-DEV.

The Memory Coordinator manages hierarchical memory across all sessions:
- Short-term: Session context, active file states (Redis)
- Long-term: Architecture decisions, learned patterns (Mem0 + FAISS)
- Episodic: Success/failure reflections, task history
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from aurora_dev.agents.base_agent import (
    AgentResponse,
    AgentRole,
    AgentStatus,
    BaseAgent,
)
from aurora_dev.core.logging import get_agent_logger
from aurora_dev.core.memory.redis_store import RedisMemoryStore, REDIS_AVAILABLE


class MemoryType(Enum):
    """Types of memory in the hierarchical system."""
    
    SHORT_TERM = "short_term"      # Session context, current state
    LONG_TERM = "long_term"        # Architecture decisions, patterns
    EPISODIC = "episodic"          # Task history, reflections


@dataclass
class MemoryItem:
    """A single memory item."""
    
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    relevance_score: float = 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "tags": self.tags,
            "relevance_score": self.relevance_score,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryItem":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            relevance_score=data.get("relevance_score", 1.0),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
        )


@dataclass
class ArchitectureDecision:
    """Record of an architecture decision (ADR)."""
    
    id: str
    title: str
    context: str
    decision: str
    rationale: str
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    consequences: dict[str, list[str]] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "accepted"  # proposed, accepted, deprecated, superseded
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "context": self.context,
            "decision": self.decision,
            "rationale": self.rationale,
            "alternatives": self.alternatives,
            "consequences": self.consequences,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
        }


@dataclass
class Reflection:
    """A reflexion entry from task execution."""
    
    id: str
    task_id: str
    agent_id: str
    attempt_number: int
    self_critique: str
    improved_approach: str
    lessons_learned: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "attempt_number": self.attempt_number,
            "self_critique": self.self_critique,
            "improved_approach": self.improved_approach,
            "lessons_learned": self.lessons_learned,
            "timestamp": self.timestamp.isoformat(),
        }


MEMORY_SYSTEM_PROMPT = """You are the Memory Coordinator Agent, responsible for managing the hierarchical memory system of AURORA-DEV.

Your memory types:
1. **Short-term Memory**: Current session context, active file states, pending changes
2. **Long-term Memory**: Architecture decisions, design patterns, best practices
3. **Episodic Memory**: Task success/failure history, reflexion notes, learned lessons

Operations:
- Store: Add new memories with proper categorization and tags
- Retrieve: Find relevant memories using semantic search
- Update: Modify existing memories, adjust relevance scores
- Decay: Reduce relevance of unused memories (10%/week)
- Prune: Archive low-relevance memories to cold storage

When asked to retrieve memories, analyze the query and return the most relevant items.
For storing, extract key entities, patterns, and learnings from the content.
"""


class MemoryCoordinator(BaseAgent):
    """
    Memory Coordinator Agent managing hierarchical memory.
    
    Implements:
    - Short-term memory (Redis-backed)
    - Long-term memory (vector store)
    - Episodic memory (task history)
    - Memory decay and pruning
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Memory Coordinator."""
        super().__init__(
            name=name or "MemoryCoordinator",
            project_id=project_id,
            session_id=session_id,
        )
        
        # In-memory storage fallback (production uses Redis + vector DB)
        self._short_term: dict[str, MemoryItem] = {}
        self._long_term: dict[str, MemoryItem] = {}
        self._episodic: dict[str, MemoryItem] = {}
        
        # Redis-backed persistent storage
        self._redis_store: Optional[RedisMemoryStore] = None
        if project_id and REDIS_AVAILABLE:
            try:
                self._redis_store = RedisMemoryStore(project_id=project_id)
                self._logger.info("Redis memory store initialized")
            except Exception as e:
                self._logger.warning(f"Redis unavailable, using in-memory: {e}")
        
        # Architecture decisions
        self._adrs: dict[str, ArchitectureDecision] = {}
        
        # Reflexions
        self._reflections: dict[str, Reflection] = {}
        
        # Vector index simulation (production uses FAISS)
        self._embeddings: dict[str, list[float]] = {}
        
        self._logger.info("Memory Coordinator initialized")
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.MEMORY_COORDINATOR
    
    @property
    def system_prompt(self) -> str:
        """Return the system prompt."""
        return MEMORY_SYSTEM_PROMPT
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for memory content."""
        hash_input = f"{content}{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def store(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ) -> MemoryItem:
        """
        Store a new memory item.
        
        Args:
            content: The content to store.
            memory_type: Type of memory.
            metadata: Optional metadata.
            tags: Optional tags for categorization.
            
        Returns:
            The stored memory item.
        """
        memory_id = self._generate_id(content)
        
        item = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata or {},
            tags=tags or [],
        )
        
        # Store in appropriate location
        if memory_type == MemoryType.SHORT_TERM:
            self._short_term[memory_id] = item
            # Also persist to Redis if available
            if self._redis_store:
                self._redis_store.store(
                    memory_id=memory_id,
                    memory_type="short",
                    data=item.to_dict(),
                )
        elif memory_type == MemoryType.LONG_TERM:
            self._long_term[memory_id] = item
            # Generate embedding (simplified)
            self._embeddings[memory_id] = self._simple_embedding(content)
            # Persist to Redis for long-term (no TTL)
            if self._redis_store:
                self._redis_store.store(
                    memory_id=memory_id,
                    memory_type="long",
                    data=item.to_dict(),
                    ttl_seconds=None,  # No expiration for long-term
                )
        else:
            self._episodic[memory_id] = item
            if self._redis_store:
                self._redis_store.store(
                    memory_id=memory_id,
                    memory_type="episodic",
                    data=item.to_dict(),
                    ttl_seconds=None,
                )
        
        self._logger.debug(
            f"Stored memory: {memory_type.value}",
            extra={"memory_id": memory_id},
        )
        
        return item
    
    def _simple_embedding(self, text: str) -> list[float]:
        """
        Generate a simple embedding for text.
        
        In production, use OpenAI/Anthropic embeddings.
        """
        # Simple hash-based embedding (placeholder)
        words = text.lower().split()
        embedding = [0.0] * 128
        for i, word in enumerate(words[:128]):
            embedding[i] = float(hash(word) % 1000) / 1000.0
        return embedding
    
    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def retrieve(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
        min_relevance: float = 0.0,
    ) -> list[MemoryItem]:
        """
        Retrieve memories matching a query.
        
        Args:
            query: Search query.
            memory_type: Optional type filter.
            limit: Maximum results.
            min_relevance: Minimum relevance score.
            
        Returns:
            List of matching memory items.
        """
        results: list[tuple[float, MemoryItem]] = []
        query_embedding = self._simple_embedding(query)
        
        # Determine which stores to search
        stores: list[dict[str, MemoryItem]] = []
        if memory_type is None:
            stores = [self._short_term, self._long_term, self._episodic]
        elif memory_type == MemoryType.SHORT_TERM:
            stores = [self._short_term]
        elif memory_type == MemoryType.LONG_TERM:
            stores = [self._long_term]
        else:
            stores = [self._episodic]
        
        # Search each store
        for store in stores:
            for memory_id, item in store.items():
                # Calculate similarity
                if memory_id in self._embeddings:
                    similarity = self._cosine_similarity(
                        query_embedding, self._embeddings[memory_id]
                    )
                else:
                    # Simple keyword matching fallback
                    query_words = set(query.lower().split())
                    content_words = set(item.content.lower().split())
                    overlap = len(query_words & content_words)
                    similarity = overlap / max(len(query_words), 1)
                
                # Apply relevance decay
                final_score = similarity * item.relevance_score
                
                if final_score >= min_relevance:
                    results.append((final_score, item))
        
        # Sort by score and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Update access counts
        top_items = []
        for score, item in results[:limit]:
            item.access_count += 1
            item.last_accessed = datetime.now(timezone.utc)
            # Boost relevance for accessed items
            item.relevance_score = min(1.0, item.relevance_score * 1.05)
            top_items.append(item)
        
        return top_items
    
    def store_decision(self, decision: ArchitectureDecision) -> None:
        """Store an architecture decision."""
        self._adrs[decision.id] = decision
        
        # Also store in long-term memory for retrieval
        content = f"ADR: {decision.title}\nContext: {decision.context}\nDecision: {decision.decision}"
        self.store(
            content=content,
            memory_type=MemoryType.LONG_TERM,
            metadata={"adr_id": decision.id},
            tags=decision.tags + ["adr", "architecture"],
        )
        
        self._logger.info(f"Stored ADR: {decision.title}")
    
    def store_reflection(self, reflection: Reflection) -> None:
        """Store a reflexion entry."""
        self._reflections[reflection.id] = reflection
        
        # Store lessons in episodic memory
        content = f"Task {reflection.task_id}: {reflection.self_critique}\nLessons: {', '.join(reflection.lessons_learned)}"
        self.store(
            content=content,
            memory_type=MemoryType.EPISODIC,
            metadata={"reflection_id": reflection.id, "task_id": reflection.task_id},
            tags=["reflection", "lesson"],
        )
        
        self._logger.info(f"Stored reflection for task {reflection.task_id}")
    
    def get_reflections_for_task_type(self, task_type: str) -> list[Reflection]:
        """Get relevant reflections for a task type."""
        return list(self._reflections.values())  # Simplified
    
    def apply_decay(self, decay_rate: float = 0.1) -> int:
        """
        Apply memory decay to reduce relevance of unused memories.
        
        Args:
            decay_rate: Rate of decay (0.1 = 10%).
            
        Returns:
            Number of memories affected.
        """
        affected = 0
        now = datetime.now(timezone.utc)
        
        for store in [self._short_term, self._long_term, self._episodic]:
            for item in store.values():
                if item.last_accessed:
                    days_since_access = (now - item.last_accessed).days
                    if days_since_access >= 7:
                        weeks = days_since_access // 7
                        item.relevance_score *= (1 - decay_rate) ** weeks
                        affected += 1
        
        return affected
    
    def prune(self, threshold: float = 0.2) -> int:
        """
        Prune memories below relevance threshold.
        
        Args:
            threshold: Minimum relevance to keep.
            
        Returns:
            Number of memories pruned.
        """
        pruned = 0
        
        for store in [self._short_term, self._long_term, self._episodic]:
            to_remove = [
                mid for mid, item in store.items()
                if item.relevance_score < threshold
            ]
            for mid in to_remove:
                del store[mid]
                self._embeddings.pop(mid, None)
                pruned += 1
        
        if pruned > 0:
            self._logger.info(f"Pruned {pruned} low-relevance memories")
        
        return pruned
    
    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        return {
            "short_term_count": len(self._short_term),
            "long_term_count": len(self._long_term),
            "episodic_count": len(self._episodic),
            "adr_count": len(self._adrs),
            "reflection_count": len(self._reflections),
            "embedding_count": len(self._embeddings),
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a memory operation."""
        self._set_status(AgentStatus.WORKING)
        
        operation = task.get("operation", "retrieve")
        
        if operation == "store":
            content = task.get("content", "")
            mem_type = MemoryType(task.get("memory_type", "short_term"))
            item = self.store(content, mem_type, task.get("metadata"), task.get("tags"))
            result = {"stored": item.to_dict()}
            
        elif operation == "retrieve":
            query = task.get("query", "")
            mem_type = MemoryType(task["memory_type"]) if task.get("memory_type") else None
            items = self.retrieve(query, mem_type, task.get("limit", 5))
            result = {"results": [i.to_dict() for i in items]}
            
        elif operation == "stats":
            result = self.get_stats()
            
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        self._set_status(AgentStatus.IDLE)
        
        return AgentResponse(
            content=json.dumps(result, indent=2),
            token_usage=self._total_usage,
            model=self._model,
            stop_reason="end_turn",
            execution_time_ms=0,
        )
