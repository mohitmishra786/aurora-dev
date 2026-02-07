"""
Agent State Management for AURORA-DEV.

This module provides state persistence, recovery, and synchronization
for agents. States can be stored in memory, Redis, or database.
"""
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from aurora_dev.core.logging import get_logger

logger = get_logger("state")


class StateStorageType(Enum):
    """Types of state storage backends."""
    
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"


@dataclass
class AgentState:
    """
    Represents the complete state of an agent.
    
    Includes working memory, task context, and execution state.
    """
    
    agent_id: str
    agent_role: str
    
    # Current task state
    current_task_id: Optional[str] = None
    task_context: dict[str, Any] = field(default_factory=dict)
    
    # Working memory
    short_term_memory: list[dict[str, Any]] = field(default_factory=list)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    
    # Execution tracking
    execution_step: int = 0
    total_tokens_used: int = 0
    total_api_calls: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Checkpoints
    last_checkpoint_at: Optional[datetime] = None
    checkpoint_data: Optional[dict[str, Any]] = None
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.last_checkpoint_at:
            data["last_checkpoint_at"] = self.last_checkpoint_at.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert state to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        """Create state from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("last_checkpoint_at"):
            data["last_checkpoint_at"] = datetime.fromisoformat(
                data["last_checkpoint_at"]
            )
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "AgentState":
        """Create state from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def add_to_memory(self, item: dict[str, Any], max_items: int = 50) -> None:
        """Add item to short-term memory with size limit."""
        self.short_term_memory.append({
            **item,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(self.short_term_memory) > max_items:
            self.short_term_memory = self.short_term_memory[-max_items:]
        self.updated_at = datetime.now(timezone.utc)
    
    def add_message(self, role: str, content: str, max_messages: int = 100) -> None:
        """Add message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > max_messages:
            self.conversation_history = self.conversation_history[-max_messages:]
        self.updated_at = datetime.now(timezone.utc)
    
    def create_checkpoint(self, data: Optional[dict[str, Any]] = None) -> None:
        """Create a state checkpoint."""
        self.last_checkpoint_at = datetime.now(timezone.utc)
        self.checkpoint_data = data or self.to_dict()
        self.updated_at = datetime.now(timezone.utc)
    
    def clear_memory(self) -> None:
        """Clear working memory."""
        self.short_term_memory.clear()
        self.conversation_history.clear()
        self.updated_at = datetime.now(timezone.utc)


class StateStore(ABC):
    """Abstract base class for state storage backends."""
    
    @abstractmethod
    def save(self, state: AgentState) -> bool:
        """Save agent state."""
        pass
    
    @abstractmethod
    def load(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state."""
        pass
    
    @abstractmethod
    def delete(self, agent_id: str) -> bool:
        """Delete agent state."""
        pass
    
    @abstractmethod
    def exists(self, agent_id: str) -> bool:
        """Check if state exists."""
        pass
    
    @abstractmethod
    def list_agents(self) -> list[str]:
        """List all stored agent IDs."""
        pass


class MemoryStateStore(StateStore):
    """In-memory state storage."""
    
    def __init__(self) -> None:
        """Initialize memory store."""
        self._states: dict[str, AgentState] = {}
    
    def save(self, state: AgentState) -> bool:
        """Save state to memory."""
        self._states[state.agent_id] = state
        logger.debug(f"State saved for agent {state.agent_id}")
        return True
    
    def load(self, agent_id: str) -> Optional[AgentState]:
        """Load state from memory."""
        return self._states.get(agent_id)
    
    def delete(self, agent_id: str) -> bool:
        """Delete state from memory."""
        if agent_id in self._states:
            del self._states[agent_id]
            logger.debug(f"State deleted for agent {agent_id}")
            return True
        return False
    
    def exists(self, agent_id: str) -> bool:
        """Check if state exists."""
        return agent_id in self._states
    
    def list_agents(self) -> list[str]:
        """List all agent IDs."""
        return list(self._states.keys())
    
    def clear(self) -> None:
        """Clear all states."""
        self._states.clear()


class RedisStateStore(StateStore):
    """Redis-backed state storage."""
    
    def __init__(self, key_prefix: str = "aurora:state:") -> None:
        """
        Initialize Redis store.
        
        Args:
            key_prefix: Prefix for Redis keys.
        """
        self._prefix = key_prefix
    
    def _get_key(self, agent_id: str) -> str:
        """Get Redis key for agent."""
        return f"{self._prefix}{agent_id}"
    
    def save(self, state: AgentState) -> bool:
        """Save state to Redis."""
        from aurora_dev.infrastructure.cache import cache_set
        
        key = self._get_key(state.agent_id)
        try:
            cache_set(key, state.to_json(), expire_seconds=86400)  # 24h TTL
            logger.debug(f"State saved to Redis for agent {state.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save state to Redis: {e}")
            return False
    
    def load(self, agent_id: str) -> Optional[AgentState]:
        """Load state from Redis."""
        from aurora_dev.infrastructure.cache import cache_get
        
        key = self._get_key(agent_id)
        try:
            data = cache_get(key)
            if data:
                return AgentState.from_json(data)
        except Exception as e:
            logger.error(f"Failed to load state from Redis: {e}")
        return None
    
    def delete(self, agent_id: str) -> bool:
        """Delete state from Redis."""
        from aurora_dev.infrastructure.cache import cache_delete
        
        key = self._get_key(agent_id)
        try:
            return cache_delete(key)
        except Exception as e:
            logger.error(f"Failed to delete state from Redis: {e}")
            return False
    
    def exists(self, agent_id: str) -> bool:
        """Check if state exists in Redis."""
        from aurora_dev.infrastructure.cache import cache_exists
        
        key = self._get_key(agent_id)
        try:
            return cache_exists(key)
        except Exception:
            return False
    
    def list_agents(self) -> list[str]:
        """List all agent IDs (requires SCAN, may be slow)."""
        from aurora_dev.infrastructure.cache import get_redis_client
        
        try:
            client = get_redis_client()
            cursor = 0
            agent_ids = []
            
            while True:
                cursor, keys = client.scan(
                    cursor, match=f"{self._prefix}*", count=100
                )
                for key in keys:
                    agent_id = key.replace(self._prefix, "")
                    agent_ids.append(agent_id)
                if cursor == 0:
                    break
            
            return agent_ids
        except Exception as e:
            logger.error(f"Failed to list agents from Redis: {e}")
            return []


class StateManager:
    """
    Manages agent state across different storage backends.
    
    Provides a unified interface for state operations with
    automatic fallback and synchronization.
    """
    
    def __init__(
        self,
        primary_store: Optional[StateStore] = None,
        fallback_store: Optional[StateStore] = None,
    ) -> None:
        """
        Initialize state manager.
        
        Args:
            primary_store: Primary storage backend.
            fallback_store: Fallback storage for recovery.
        """
        self._primary = primary_store or MemoryStateStore()
        self._fallback = fallback_store
        
        logger.info(
            f"State manager initialized with {type(self._primary).__name__}"
        )
    
    def save(self, state: AgentState) -> bool:
        """
        Save agent state.
        
        Args:
            state: The state to save.
            
        Returns:
            True if saved successfully.
        """
        success = self._primary.save(state)
        
        # Also save to fallback if available
        if self._fallback:
            self._fallback.save(state)
        
        return success
    
    def load(self, agent_id: str) -> Optional[AgentState]:
        """
        Load agent state.
        
        Tries primary store first, falls back if needed.
        
        Args:
            agent_id: The agent ID to load.
            
        Returns:
            The agent state, or None if not found.
        """
        state = self._primary.load(agent_id)
        
        if not state and self._fallback:
            state = self._fallback.load(agent_id)
            if state:
                # Sync to primary
                self._primary.save(state)
                logger.info(f"State recovered from fallback for agent {agent_id}")
        
        return state
    
    def delete(self, agent_id: str) -> bool:
        """Delete agent state from all stores."""
        primary_deleted = self._primary.delete(agent_id)
        if self._fallback:
            self._fallback.delete(agent_id)
        return primary_deleted
    
    def exists(self, agent_id: str) -> bool:
        """Check if state exists in any store."""
        exists = self._primary.exists(agent_id)
        if not exists and self._fallback:
            exists = self._fallback.exists(agent_id)
        return exists
    
    def create_checkpoint(self, agent_id: str) -> bool:
        """
        Create a checkpoint for an agent.
        
        Args:
            agent_id: The agent ID to checkpoint.
            
        Returns:
            True if checkpoint created.
        """
        state = self.load(agent_id)
        if state:
            state.create_checkpoint()
            return self.save(state)
        return False
    
    def restore_checkpoint(self, agent_id: str) -> Optional[AgentState]:
        """
        Restore an agent to its last checkpoint.
        
        Args:
            agent_id: The agent ID to restore.
            
        Returns:
            The restored state, or None if no checkpoint.
        """
        state = self.load(agent_id)
        if state and state.checkpoint_data:
            restored = AgentState.from_dict(state.checkpoint_data)
            self.save(restored)
            logger.info(f"State restored from checkpoint for agent {agent_id}")
            return restored
        return None


# Global state manager
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """
    Get the global state manager instance.
    
    Returns:
        The StateManager singleton.
    """
    global _state_manager
    if _state_manager is None:
        # Use Redis as primary if available, memory as fallback
        try:
            from aurora_dev.infrastructure.cache import check_health
            if check_health():
                _state_manager = StateManager(
                    primary_store=RedisStateStore(),
                    fallback_store=MemoryStateStore(),
                )
            else:
                _state_manager = StateManager()
        except Exception:
            _state_manager = StateManager()
    return _state_manager
