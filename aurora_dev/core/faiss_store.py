"""
FAISS Local Vector Store for AURORA-DEV.

Provides a local vector store using FAISS for fast similarity
search without requiring external services like Pinecone.

Gap B12: FAISS as primary local vector store.
"""
import logging
import os
import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.debug("FAISS not installed; FAISSVectorStore will use numpy fallback")


@dataclass
class FAISSEntry:
    """An entry stored in the FAISS index."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class FAISSVectorStore:
    """Local vector store backed by FAISS.

    Falls back to brute-force numpy cosine similarity when FAISS
    is not installed.

    Example:
        >>> store = FAISSVectorStore(dimension=1536)
        >>> store.add("doc-1", embedding, text="Hello", metadata={})
        >>> results = store.search(query_embedding, top_k=5)
    """

    def __init__(
        self,
        dimension: int = 1536,
        index_type: str = "flat",
        persistence_path: Optional[str] = None,
    ) -> None:
        self._dimension = dimension
        self._entries: dict[str, FAISSEntry] = {}
        self._id_to_idx: dict[str, int] = {}
        self._idx_to_id: dict[int, str] = {}
        self._next_idx = 0
        self._persistence_path = persistence_path

        if FAISS_AVAILABLE:
            if index_type == "ivf":
                quantizer = faiss.IndexFlatIP(dimension)
                self._index: Any = faiss.IndexIVFFlat(
                    quantizer, dimension, min(16, max(1, self._next_idx)),
                )
            else:
                self._index = faiss.IndexFlatIP(dimension)
        else:
            self._index = None
            self._vectors: list[np.ndarray] = []

        if persistence_path and os.path.exists(persistence_path):
            self._load(persistence_path)

    def add(
        self,
        entry_id: str,
        embedding: list[float],
        text: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add or update an entry.

        Args:
            entry_id: Unique identifier.
            embedding: Vector embedding.
            text: Original text.
            metadata: Additional metadata.
        """
        vec = np.array(embedding, dtype=np.float32).reshape(1, -1)
        # L2-normalize for cosine similarity via inner product
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        entry = FAISSEntry(
            id=entry_id,
            text=text,
            metadata=metadata or {},
            embedding=embedding,
        )

        if entry_id in self._id_to_idx:
            # Update existing – FAISS doesn't support in-place update,
            # but we track the mapping; on search, we deduplicate.
            pass

        idx = self._next_idx
        self._id_to_idx[entry_id] = idx
        self._idx_to_id[idx] = entry_id
        self._entries[entry_id] = entry
        self._next_idx += 1

        if self._index is not None and FAISS_AVAILABLE:
            self._index.add(vec)
        else:
            self._vectors.append(vec.flatten())

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for similar entries.

        Args:
            query_embedding: Query vector.
            top_k: Number of results.

        Returns:
            List of results with id, text, metadata, score.
        """
        if not self._entries:
            return []

        vec = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        if self._index is not None and FAISS_AVAILABLE:
            k = min(top_k, self._index.ntotal)
            if k == 0:
                return []
            scores, indices = self._index.search(vec, k)
            results = []
            seen: set[str] = set()
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue
                entry_id = self._idx_to_id.get(int(idx))
                if entry_id and entry_id not in seen:
                    seen.add(entry_id)
                    entry = self._entries[entry_id]
                    results.append({
                        "id": entry_id,
                        "text": entry.text,
                        "metadata": entry.metadata,
                        "score": float(score),
                    })
            return results[:top_k]
        else:
            # Numpy fallback
            if not self._vectors:
                return []
            matrix = np.array(self._vectors)
            query_flat = vec.flatten()
            scores = matrix @ query_flat
            top_indices = np.argsort(-scores)[:top_k]
            results = []
            for idx in top_indices:
                entry_id = self._idx_to_id.get(int(idx))
                if entry_id:
                    entry = self._entries[entry_id]
                    results.append({
                        "id": entry_id,
                        "text": entry.text,
                        "metadata": entry.metadata,
                        "score": float(scores[idx]),
                    })
            return results

    def delete(self, entry_id: str) -> bool:
        """Remove an entry (marks as deleted; rebuild for cleanup).

        Args:
            entry_id: Entry to remove.

        Returns:
            True if found and removed.
        """
        if entry_id in self._entries:
            del self._entries[entry_id]
            # Note: FAISS doesn't support deletion without rebuild
            return True
        return False

    def count(self) -> int:
        """Get number of stored entries."""
        return len(self._entries)

    def save(self, path: Optional[str] = None) -> None:
        """Persist the index and entries to disk."""
        save_path = path or self._persistence_path
        if not save_path:
            return

        data = {
            "entries": self._entries,
            "id_to_idx": self._id_to_idx,
            "idx_to_id": self._idx_to_id,
            "next_idx": self._next_idx,
            "dimension": self._dimension,
        }

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        if FAISS_AVAILABLE and self._index is not None:
            faiss.write_index(self._index, str(Path(save_path).with_suffix(".faiss")))

        with open(save_path, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"FAISS store saved: {self.count()} entries -> {save_path}")

    def _load(self, path: str) -> None:
        """Load index and entries from disk."""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            self._entries = data["entries"]
            self._id_to_idx = data["id_to_idx"]
            self._idx_to_id = data["idx_to_id"]
            self._next_idx = data["next_idx"]
            self._dimension = data["dimension"]

            if FAISS_AVAILABLE:
                faiss_path = str(Path(path).with_suffix(".faiss"))
                if os.path.exists(faiss_path):
                    self._index = faiss.read_index(faiss_path)

            logger.info(f"FAISS store loaded: {self.count()} entries from {path}")
        except Exception as e:
            logger.warning(f"Failed to load FAISS store from {path}: {e}")
