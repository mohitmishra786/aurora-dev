"""
Mem0 integration for persistent agent memory.

Provides long-term memory capabilities using Mem0,
enabling agents to retain and recall information across sessions.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False

from aurora_dev.core.config import get_settings
from aurora_dev.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryRecord:
    """A memory record from Mem0.
    
    Attributes:
        id: Unique memory identifier.
        content: Memory content text.
        user_id: Associated user/agent ID.
        metadata: Additional metadata.
        created_at: Creation timestamp.
    """
    
    id: str
    content: str
    user_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Mem0Client:
    """Client for Mem0 memory service.
    
    Provides long-term memory storage and retrieval for agents,
    enabling learning and context retention across conversations.
    
    Example:
        >>> client = Mem0Client()
        >>> client.add("User prefers TypeScript over JavaScript", user_id="agent-frontend")
        >>> memories = client.search("programming language preferences", user_id="agent-frontend")
    """
    
    def __init__(self) -> None:
        """Initialize the Mem0 client."""
        if not MEM0_AVAILABLE:
            raise ImportError(
                "Mem0 is not installed. "
                "Install it with: pip install mem0ai"
            )
        
        self.settings = get_settings()
        
        # Configure Mem0 with settings
        config = {
            "llm": {
                "provider": "anthropic",
                "config": {
                    "api_key": self.settings.anthropic.api_key,
                    "model": "claude-3-haiku-20240307",
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "api_key": self.settings.mem0.openai_api_key,
                    "model": "text-embedding-3-small",
                },
            },
            "vector_store": {
                "provider": "pinecone",
                "config": {
                    "api_key": self.settings.pinecone.api_key,
                    "index_name": f"{self.settings.pinecone.index_name}-mem0",
                    "cloud": self.settings.pinecone.cloud,
                    "region": self.settings.pinecone.region,
                },
            },
        }
        
        self._memory = Memory.from_config(config)
        
        logger.info("Mem0Client initialized")
    
    def add(
        self,
        content: str,
        user_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Add a memory.
        
        Args:
            content: Memory content text.
            user_id: User or agent ID to associate with.
            metadata: Optional additional metadata.
            
        Returns:
            Memory ID.
        """
        result = self._memory.add(
            content,
            user_id=user_id,
            metadata=metadata or {},
        )
        
        memory_id = result.get("id", "unknown")
        
        logger.debug(
            "Added memory",
            memory_id=memory_id,
            user_id=user_id,
        )
        
        return memory_id
    
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> list[MemoryRecord]:
        """Search for relevant memories.
        
        Args:
            query: Search query.
            user_id: User or agent ID to search for.
            limit: Maximum number of results.
            
        Returns:
            List of matching memory records.
        """
        results = self._memory.search(
            query,
            user_id=user_id,
            limit=limit,
        )
        
        records = []
        for result in results:
            records.append(
                MemoryRecord(
                    id=result.get("id", ""),
                    content=result.get("memory", ""),
                    user_id=user_id,
                    metadata=result.get("metadata", {}),
                )
            )
        
        logger.debug(
            "Memory search completed",
            query_length=len(query),
            num_results=len(records),
        )
        
        return records
    
    def get_all(self, user_id: str) -> list[MemoryRecord]:
        """Get all memories for a user.
        
        Args:
            user_id: User or agent ID.
            
        Returns:
            List of all memory records.
        """
        results = self._memory.get_all(user_id=user_id)
        
        records = []
        for result in results:
            records.append(
                MemoryRecord(
                    id=result.get("id", ""),
                    content=result.get("memory", ""),
                    user_id=user_id,
                    metadata=result.get("metadata", {}),
                )
            )
        
        return records
    
    def delete(self, memory_id: str) -> None:
        """Delete a specific memory.
        
        Args:
            memory_id: ID of memory to delete.
        """
        self._memory.delete(memory_id)
        
        logger.debug("Deleted memory", memory_id=memory_id)
    
    def delete_all(self, user_id: str) -> None:
        """Delete all memories for a user.
        
        Args:
            user_id: User or agent ID.
        """
        self._memory.delete_all(user_id=user_id)
        
        logger.info("Deleted all memories", user_id=user_id)
    
    def update(
        self,
        memory_id: str,
        content: str,
    ) -> None:
        """Update a memory's content.
        
        Args:
            memory_id: ID of memory to update.
            content: New content.
        """
        self._memory.update(memory_id, content)
        
        logger.debug("Updated memory", memory_id=memory_id)


class AgentMem0:
    """High-level Mem0 interface for agents.
    
    Provides simplified methods for agents to manage their
    long-term memory using Mem0.
    """
    
    def __init__(self, agent_id: str) -> None:
        """Initialize agent memory.
        
        Args:
            agent_id: The agent's unique identifier.
        """
        self.agent_id = agent_id
        self._client = Mem0Client()
    
    def learn(
        self,
        content: str,
        category: str = "general",
        importance: str = "medium",
    ) -> str:
        """Learn and store new information.
        
        Args:
            content: What to learn.
            category: Learning category.
            importance: Importance level (low, medium, high, critical).
            
        Returns:
            Memory ID.
        """
        metadata = {
            "category": category,
            "importance": importance,
            "agent_id": self.agent_id,
        }
        
        return self._client.add(content, user_id=self.agent_id, metadata=metadata)
    
    def recall(
        self,
        query: str,
        limit: int = 5,
    ) -> list[MemoryRecord]:
        """Recall relevant memories.
        
        Args:
            query: What to recall.
            limit: Maximum number of memories.
            
        Returns:
            List of relevant memories.
        """
        return self._client.search(query, user_id=self.agent_id, limit=limit)
    
    def forget(self, memory_id: str) -> None:
        """Forget a specific memory."""
        self._client.delete(memory_id)
    
    def forget_all(self) -> None:
        """Forget all memories."""
        self._client.delete_all(self.agent_id)
    
    def get_history(self) -> list[MemoryRecord]:
        """Get all memories."""
        return self._client.get_all(self.agent_id)
