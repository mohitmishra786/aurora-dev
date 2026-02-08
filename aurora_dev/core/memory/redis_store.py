"""
Redis-backed memory storage for AURORA-DEV.

Provides persistent storage backend for the MemoryCoordinator,
enabling session persistence and cross-agent memory sharing.
"""
import json
from datetime import datetime, timezone
from typing import Any, Optional

from aurora_dev.core.logging import get_logger

logger = get_logger("memory.redis")

# Try to import Redis - graceful fallback if unavailable
try:
    from aurora_dev.infrastructure.cache import (
        cache_delete,
        cache_exists,
        cache_get,
        cache_set,
        get_redis_client,
    )
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False


class RedisMemoryStore:
    """
    Redis-backed storage for memory items.
    
    Provides persistent, distributed storage with automatic
    TTL-based expiration for short-term memories.
    
    Key format:
    - Short-term: aurora:memory:{project_id}:short:{memory_id}
    - Long-term: aurora:memory:{project_id}:long:{memory_id}
    - Episodic: aurora:memory:{project_id}:episodic:{memory_id}
    """
    
    def __init__(
        self,
        project_id: str,
        default_ttl_seconds: int = 3600 * 24,  # 24 hours for short-term
    ) -> None:
        """
        Initialize Redis memory store.
        
        Args:
            project_id: Project identifier for key namespacing.
            default_ttl_seconds: Default TTL for short-term memories.
        """
        self._project_id = project_id
        self._default_ttl = default_ttl_seconds
        self._prefix = f"aurora:memory:{project_id}"
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, memory persistence disabled")
    
    def _make_key(self, memory_type: str, memory_id: str) -> str:
        """Create a Redis key for a memory item."""
        return f"{self._prefix}:{memory_type}:{memory_id}"
    
    def _serialize(self, item: dict[str, Any]) -> str:
        """Serialize a memory item to JSON."""
        return json.dumps(item, default=str)
    
    def _deserialize(self, data: str) -> dict[str, Any]:
        """Deserialize a memory item from JSON."""
        return json.loads(data)
    
    def store(
        self,
        memory_id: str,
        memory_type: str,
        data: dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Store a memory item in Redis.
        
        Args:
            memory_id: Unique memory identifier.
            memory_type: Type of memory (short, long, episodic).
            data: Memory item data as dictionary.
            ttl_seconds: Optional TTL override.
            
        Returns:
            True if stored successfully.
        """
        if not REDIS_AVAILABLE:
            return False
        
        key = self._make_key(memory_type, memory_id)
        value = self._serialize(data)
        
        # Apply TTL only for short-term memories
        ttl = ttl_seconds or (self._default_ttl if memory_type == "short" else None)
        
        try:
            success = cache_set(key, value, expire_seconds=ttl)
            if success:
                # Also add to the memory type index
                index_key = f"{self._prefix}:index:{memory_type}"
                client = get_redis_client()
                client.sadd(index_key, memory_id)
            return success
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    def retrieve(
        self,
        memory_id: str,
        memory_type: str,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve a memory item from Redis.
        
        Args:
            memory_id: Unique memory identifier.
            memory_type: Type of memory.
            
        Returns:
            Memory item data or None if not found.
        """
        if not REDIS_AVAILABLE:
            return None
        
        key = self._make_key(memory_type, memory_id)
        
        try:
            data = cache_get(key)
            if data:
                return self._deserialize(data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return None
    
    def delete(self, memory_id: str, memory_type: str) -> bool:
        """Delete a memory item from Redis."""
        if not REDIS_AVAILABLE:
            return False
        
        key = self._make_key(memory_type, memory_id)
        
        try:
            success = cache_delete(key)
            if success:
                # Remove from index
                index_key = f"{self._prefix}:index:{memory_type}"
                client = get_redis_client()
                client.srem(index_key, memory_id)
            return success
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    def list_ids(self, memory_type: str) -> list[str]:
        """
        List all memory IDs of a given type.
        
        Args:
            memory_type: Type of memory to list.
            
        Returns:
            List of memory IDs.
        """
        if not REDIS_AVAILABLE:
            return []
        
        index_key = f"{self._prefix}:index:{memory_type}"
        
        try:
            client = get_redis_client()
            return list(client.smembers(index_key))
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            return []
    
    def get_all(self, memory_type: str) -> list[dict[str, Any]]:
        """
        Get all memory items of a given type.
        
        Args:
            memory_type: Type of memory to retrieve.
            
        Returns:
            List of memory item dictionaries.
        """
        ids = self.list_ids(memory_type)
        items = []
        
        for memory_id in ids:
            item = self.retrieve(memory_id, memory_type)
            if item:
                items.append(item)
        
        return items
    
    def clear(self, memory_type: Optional[str] = None) -> int:
        """
        Clear memories of a specific type or all types.
        
        Args:
            memory_type: Type to clear, or None for all.
            
        Returns:
            Number of items cleared.
        """
        if not REDIS_AVAILABLE:
            return 0
        
        types_to_clear = (
            [memory_type] if memory_type
            else ["short", "long", "episodic"]
        )
        
        cleared = 0
        for mem_type in types_to_clear:
            ids = self.list_ids(mem_type)
            for memory_id in ids:
                if self.delete(memory_id, mem_type):
                    cleared += 1
        
        return cleared
    
    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return REDIS_AVAILABLE


def get_memory_store(project_id: str) -> RedisMemoryStore:
    """Get a RedisMemoryStore instance for a project."""
    return RedisMemoryStore(project_id=project_id)
