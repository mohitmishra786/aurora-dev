"""
Vector Store implementation using Pinecone.

Provides storage and retrieval of embeddings for agent memory,
enabling semantic search and context retrieval across sessions.
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Optional

import httpx

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from aurora_dev.core.config import get_settings
from aurora_dev.core.logging import get_logger

logger = get_logger(__name__)


# Module-level embedding cache to avoid redundant API calls
_embedding_cache: dict[str, list[float]] = {}
_EMBEDDING_CACHE_MAX_SIZE = 1000


@dataclass
class VectorEntry:
    """Represents a vector entry in the store.
    
    Attributes:
        id: Unique entry identifier.
        content: Original text content.
        embedding: Vector embedding (will be computed if not provided).
        metadata: Additional metadata for filtering.
        created_at: Entry creation timestamp.
    """
    
    id: str
    content: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dictionary format for Pinecone."""
        return {
            "id": self.id,
            "values": self.embedding,
            "metadata": {
                "content": self.content,
                "created_at": self.created_at.isoformat(),
                **self.metadata,
            },
        }


@dataclass
class SearchResult:
    """Result from a vector similarity search.
    
    Attributes:
        id: Entry identifier.
        content: Original text content.
        score: Similarity score (0-1).
        metadata: Entry metadata.
    """
    
    id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """Vector store for agent memory using Pinecone.
    
    Provides semantic storage and retrieval for agent context,
    enabling learning and context retention across sessions.
    
    Example:
        >>> store = VectorStore()
        >>> await store.store("user-preference", "User prefers dark mode", {"agent": "frontend"})
        >>> results = await store.search("What theme does the user prefer?", top_k=3)
    """
    
    def __init__(
        self,
        index_name: Optional[str] = None,
        namespace: str = "default",
    ) -> None:
        """Initialize the vector store.
        
        Args:
            index_name: Pinecone index name (defaults to config value).
            namespace: Namespace for organizing vectors.
        """
        if not PINECONE_AVAILABLE:
            raise ImportError(
                "Pinecone is not installed. "
                "Install it with: pip install pinecone-client"
            )
        
        self.settings = get_settings()
        self.index_name = index_name or self.settings.pinecone.index_name
        self.namespace = namespace
        
        # Initialize Pinecone client
        self._client = Pinecone(api_key=self.settings.pinecone.api_key)
        self._index = None
        
        logger.info(
            "VectorStore initialized",
            index_name=self.index_name,
            namespace=self.namespace,
        )
    
    def _get_index(self):
        """Get or create the Pinecone index."""
        if self._index is None:
            # Check if index exists
            existing_indexes = [idx.name for idx in self._client.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self._client.create_index(
                    name=self.index_name,
                    dimension=self.settings.pinecone.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=self.settings.pinecone.cloud,
                        region=self.settings.pinecone.region,
                    ),
                )
            
            self._index = self._client.Index(self.index_name)
        
        return self._index
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using OpenAI's embedding API.
        
        Uses text-embedding-3-large model with caching to avoid
        redundant API calls. Falls back to deterministic hash-based
        embeddings if the API is unavailable.
        """
        global _embedding_cache
        
        # Check cache first
        cache_key = hashlib.sha256(text.encode()).hexdigest()
        if cache_key in _embedding_cache:
            return _embedding_cache[cache_key]
        
        # Try OpenAI API
        api_key = self.settings.openai.api_key
        if not api_key:
            logger.warning(
                "OpenAI API key not configured, using hash-based fallback embeddings. "
                "Set OPENAI_API_KEY for real semantic search."
            )
            return self._fallback_embedding(text)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.settings.openai.embedding_model,
                        "input": text,
                        "dimensions": self.settings.openai.embedding_dimension,
                    },
                )
                response.raise_for_status()
                data = response.json()
                embedding = data["data"][0]["embedding"]
                
                # Cache the result
                if len(_embedding_cache) >= _EMBEDDING_CACHE_MAX_SIZE:
                    # Evict oldest entries (first 100)
                    keys_to_remove = list(_embedding_cache.keys())[:100]
                    for k in keys_to_remove:
                        del _embedding_cache[k]
                _embedding_cache[cache_key] = embedding
                
                return embedding
                
        except httpx.HTTPStatusError as e:
            logger.error(
                f"OpenAI embedding API error: {e.response.status_code}",
                detail=e.response.text[:200],
            )
            return self._fallback_embedding(text)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._fallback_embedding(text)
    
    def _fallback_embedding(self, text: str) -> list[float]:
        """Generate deterministic hash-based embedding as fallback.
        
        This produces consistent (not random) vectors based on content,
        which provides basic deduplication but NOT semantic similarity.
        """
        import struct
        dimension = self.settings.pinecone.dimension
        # Use SHA-512 repeatedly to fill the dimension
        result = []
        seed = text.encode()
        while len(result) < dimension:
            seed = hashlib.sha512(seed).digest()
            # Unpack 8 doubles from 64 bytes
            floats = struct.unpack('8d', seed)
            # Normalize to [-1, 1]
            for f in floats:
                if len(result) < dimension:
                    result.append((f % 2.0) - 1.0)
        return result[:dimension]
    
    async def store(
        self,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
        entry_id: Optional[str] = None,
    ) -> str:
        """Store content in the vector store.
        
        Args:
            content: Text content to store.
            metadata: Optional metadata for filtering.
            entry_id: Optional custom ID (auto-generated if not provided).
            
        Returns:
            The ID of the stored entry.
        """
        entry_id = entry_id or self._generate_id(content)
        embedding = await self._get_embedding(content)
        
        entry = VectorEntry(
            id=entry_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
        )
        
        index = self._get_index()
        index.upsert(
            vectors=[entry.to_dict()],
            namespace=self.namespace,
        )
        
        logger.debug(
            "Stored vector entry",
            entry_id=entry_id,
            content_length=len(content),
        )
        
        return entry_id
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """Search for similar content.
        
        Args:
            query: Search query text.
            top_k: Number of results to return.
            filter: Optional metadata filter.
            
        Returns:
            List of search results ordered by similarity.
        """
        query_embedding = await self._get_embedding(query)
        
        index = self._get_index()
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=self.namespace,
            filter=filter,
            include_metadata=True,
        )
        
        search_results = []
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            search_results.append(
                SearchResult(
                    id=match["id"],
                    content=metadata.pop("content", ""),
                    score=match["score"],
                    metadata=metadata,
                )
            )
        
        logger.debug(
            "Vector search completed",
            query_length=len(query),
            num_results=len(search_results),
        )
        
        return search_results
    
    async def delete(self, entry_ids: list[str]) -> None:
        """Delete entries from the vector store.
        
        Args:
            entry_ids: List of entry IDs to delete.
        """
        index = self._get_index()
        index.delete(ids=entry_ids, namespace=self.namespace)
        
        logger.debug(
            "Deleted vector entries",
            count=len(entry_ids),
        )
    
    async def clear_namespace(self) -> None:
        """Clear all entries in the current namespace."""
        index = self._get_index()
        index.delete(delete_all=True, namespace=self.namespace)
        
        logger.info(
            "Cleared vector namespace",
            namespace=self.namespace,
        )
    
    def get_stats(self) -> dict[str, Any]:
        """Get index statistics.
        
        Returns:
            Dictionary with index statistics.
        """
        index = self._get_index()
        stats = index.describe_index_stats()
        
        return {
            "total_vectors": stats.get("total_vector_count", 0),
            "namespaces": stats.get("namespaces", {}),
            "dimension": stats.get("dimension", 0),
        }


class AgentMemory:
    """High-level memory interface for agents.
    
    Provides simplified methods for agents to store and retrieve
    context, decisions, and learnings.
    """
    
    def __init__(
        self,
        agent_id: str,
        project_id: Optional[str] = None,
    ) -> None:
        """Initialize agent memory.
        
        Args:
            agent_id: The agent's unique identifier.
            project_id: Optional project context.
        """
        self.agent_id = agent_id
        self.project_id = project_id
        
        namespace = f"agent-{agent_id}"
        if project_id:
            namespace = f"{namespace}-{project_id}"
        
        self._store = VectorStore(namespace=namespace)
    
    async def remember(
        self,
        content: str,
        memory_type: str = "general",
        importance: int = 5,
    ) -> str:
        """Store a memory.
        
        Args:
            content: Memory content.
            memory_type: Type of memory (decision, learning, context).
            importance: Importance score (1-10).
            
        Returns:
            Memory ID.
        """
        metadata = {
            "agent_id": self.agent_id,
            "project_id": self.project_id,
            "memory_type": memory_type,
            "importance": importance,
        }
        
        return await self._store.store(content, metadata=metadata)
    
    async def recall(
        self,
        query: str,
        memory_type: Optional[str] = None,
        min_importance: int = 1,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Recall relevant memories.
        
        Args:
            query: Search query.
            memory_type: Optional filter by memory type.
            min_importance: Minimum importance threshold.
            limit: Maximum results to return.
            
        Returns:
            List of relevant memories.
        """
        filter_dict = {"importance": {"$gte": min_importance}}
        if memory_type:
            filter_dict["memory_type"] = memory_type
        
        return await self._store.search(query, top_k=limit, filter=filter_dict)
    
    async def forget(self, memory_ids: list[str]) -> None:
        """Delete specific memories.
        
        Args:
            memory_ids: List of memory IDs to delete.
        """
        await self._store.delete(memory_ids)
    
    async def clear_all(self) -> None:
        """Clear all memories for this agent."""
        await self._store.clear_namespace()
