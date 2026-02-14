"""
Cross-Encoder Re-ranking for AURORA-DEV.

Re-ranks initial vector search results using a cross-encoder
model for higher-quality relevance scoring.

Gap B9: Cross-encoder re-ranking for VectorStore search.
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import CrossEncoder as _CrossEncoder

    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.debug("sentence-transformers not installed; cross-encoder disabled")


class CrossEncoderReranker:
    """Re-ranks search results using a cross-encoder model.
    
    Cross-encoders process query-document pairs jointly,
    producing more accurate relevance scores than bi-encoder
    similarity search alone.
    
    Example:
        >>> reranker = CrossEncoderReranker()
        >>> results = reranker.rerank(
        ...     query="authentication middleware",
        ...     candidates=[
        ...         {"text": "JWT auth handler", "id": "doc1"},
        ...         {"text": "Database migrations", "id": "doc2"},
        ...     ],
        ...     top_k=5,
        ... )
    """
    
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    def __init__(
        self,
        model_name: Optional[str] = None,
    ) -> None:
        self._model_name = model_name or self.DEFAULT_MODEL
        self._model: Any = None
        
        if CROSS_ENCODER_AVAILABLE:
            try:
                self._model = _CrossEncoder(self._model_name)
                logger.info(f"Cross-encoder loaded: {self._model_name}")
            except Exception as e:
                logger.warning(f"Failed to load cross-encoder: {e}")
    
    @property
    def is_available(self) -> bool:
        """Whether the cross-encoder model is loaded."""
        return self._model is not None
    
    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int = 5,
        text_key: str = "text",
    ) -> list[dict[str, Any]]:
        """Re-rank candidates using cross-encoder scores.
        
        Args:
            query: Search query.
            candidates: Initial search results (must have `text_key` field).
            top_k: Number of results to return.
            text_key: Key for text content in each candidate dict.
            
        Returns:
            Re-ranked candidates with updated scores.
        """
        if not candidates:
            return []
        
        if not self.is_available:
            # Fallback: return candidates as-is
            logger.debug("Cross-encoder not available, returning original order")
            return candidates[:top_k]
        
        # Build query-document pairs
        pairs = [
            (query, c.get(text_key, c.get("content", "")))
            for c in candidates
        ]
        
        try:
            scores = self._model.predict(pairs)
            
            # Combine scores with candidates
            scored = list(zip(candidates, scores))
            scored.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for candidate, score in scored[:top_k]:
                reranked = dict(candidate)
                reranked["rerank_score"] = float(score)
                reranked["original_score"] = candidate.get("score", 0.0)
                results.append(reranked)
            
            return results
            
        except Exception as e:
            logger.warning(f"Cross-encoder reranking failed: {e}")
            return candidates[:top_k]
    
    def rerank_search_results(
        self,
        query: str,
        results: list[Any],
        top_k: int = 5,
    ) -> list[Any]:
        """Re-rank SearchResult objects.
        
        Args:
            query: Search query.
            results: List of SearchResult objects with .content attribute.
            top_k: Number of results.
            
        Returns:
            Re-ranked SearchResult list.
        """
        if not results or not self.is_available:
            return results[:top_k]
        
        pairs = [(query, getattr(r, "content", str(r))) for r in results]
        
        try:
            scores = self._model.predict(pairs)
            scored = sorted(
                zip(results, scores),
                key=lambda x: x[1],
                reverse=True,
            )
            return [r for r, _ in scored[:top_k]]
        except Exception as e:
            logger.warning(f"Cross-encoder reranking failed: {e}")
            return results[:top_k]
