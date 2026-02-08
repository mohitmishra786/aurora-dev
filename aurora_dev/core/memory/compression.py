"""
Memory compression module for AURORA-DEV.

Provides summarization and compression of context
to reduce token usage while preserving key information.

Example usage:
    >>> compressor = MemoryCompressor()
    >>> result = await compressor.compress(
    ...     content="Long detailed context...",
    ...     strategy=CompressionStrategy.SUMMARIZE,
    ... )
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class CompressionStrategy(Enum):
    """Strategies for memory compression."""
    
    SUMMARIZE = "summarize"  # Generate summary
    EXTRACT_KEY_POINTS = "extract_key_points"  # Extract bullet points
    DEDUPLICATE = "deduplicate"  # Remove duplicate information
    HIERARCHICAL = "hierarchical"  # Multi-level summarization
    NONE = "none"  # No compression


@dataclass
class CompressionResult:
    """Result of a compression operation."""
    
    original_content: str
    compressed_content: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: CompressionStrategy
    key_points: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryEntry:
    """A memory entry that can be compressed."""
    
    id: str
    content: str
    summary: Optional[str] = None
    key_points: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    importance: float = 0.5
    is_compressed: bool = False
    original_token_count: int = 0
    
    def content_hash(self) -> str:
        """Get hash of content for deduplication."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


class MemoryCompressor:
    """
    Compresses and summarizes memory content.
    
    Reduces token usage while preserving key information
    through various compression strategies.
    """
    
    # Compression targets by age
    AGE_THRESHOLDS = {
        1: CompressionStrategy.NONE,  # < 1 hour: keep full
        24: CompressionStrategy.EXTRACT_KEY_POINTS,  # < 24 hours: key points
        168: CompressionStrategy.SUMMARIZE,  # < 1 week: summarize
        720: CompressionStrategy.HIERARCHICAL,  # < 1 month: deep compression
    }
    
    def __init__(
        self,
        target_compression_ratio: float = 0.3,
        min_content_length: int = 100,
    ):
        """
        Initialize memory compressor.
        
        Args:
            target_compression_ratio: Target ratio (0.3 = 30% of original).
            min_content_length: Minimum content length to compress.
        """
        self.target_compression_ratio = target_compression_ratio
        self.min_content_length = min_content_length
        self._logger = get_logger(__name__)
        self._dedup_cache: dict[str, str] = {}
    
    async def compress(
        self,
        content: str,
        strategy: CompressionStrategy = CompressionStrategy.SUMMARIZE,
        context: Optional[str] = None,
        llm_client: Optional[Any] = None,
    ) -> CompressionResult:
        """
        Compress content using specified strategy.
        
        Args:
            content: Content to compress.
            strategy: Compression strategy.
            context: Optional context for better compression.
            llm_client: Optional LLM client for AI-powered compression.
            
        Returns:
            CompressionResult with compressed content.
        """
        original_tokens = self._estimate_tokens(content)
        
        # Skip if too short
        if len(content) < self.min_content_length:
            return CompressionResult(
                original_content=content,
                compressed_content=content,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.NONE,
            )
        
        if strategy == CompressionStrategy.NONE:
            return CompressionResult(
                original_content=content,
                compressed_content=content,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                strategy_used=strategy,
            )
        
        elif strategy == CompressionStrategy.EXTRACT_KEY_POINTS:
            compressed, key_points = await self._extract_key_points(content, llm_client)
            
        elif strategy == CompressionStrategy.SUMMARIZE:
            compressed = await self._summarize(content, context, llm_client)
            key_points = []
            
        elif strategy == CompressionStrategy.DEDUPLICATE:
            compressed = await self._deduplicate(content)
            key_points = []
            
        elif strategy == CompressionStrategy.HIERARCHICAL:
            compressed, key_points = await self._hierarchical_compress(content, llm_client)
            
        else:
            compressed = content
            key_points = []
        
        compressed_tokens = self._estimate_tokens(compressed)
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        
        self._logger.info(
            f"Compressed: {original_tokens} -> {compressed_tokens} tokens "
            f"(ratio: {ratio:.2f})"
        )
        
        return CompressionResult(
            original_content=content,
            compressed_content=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=ratio,
            strategy_used=strategy,
            key_points=key_points,
        )
    
    async def compress_by_age(
        self,
        entry: MemoryEntry,
        llm_client: Optional[Any] = None,
    ) -> CompressionResult:
        """
        Compress memory entry based on its age.
        
        Older memories get more aggressive compression.
        """
        age_hours = (datetime.now() - entry.created_at).total_seconds() / 3600
        
        # Determine strategy based on age
        strategy = CompressionStrategy.NONE
        for hours, strat in sorted(self.AGE_THRESHOLDS.items()):
            if age_hours < hours:
                strategy = strat
                break
        else:
            strategy = CompressionStrategy.HIERARCHICAL
        
        return await self.compress(entry.content, strategy, llm_client=llm_client)
    
    async def _extract_key_points(
        self,
        content: str,
        llm_client: Optional[Any] = None,
    ) -> tuple[str, list[str]]:
        """Extract key points from content."""
        if llm_client:
            # Use LLM for extraction
            prompt = f"""Extract the key points from this content as a bullet list:

{content}

Respond with only the bullet points, one per line starting with -.
Keep it under 10 points. Focus on actionable information."""
            
            try:
                response = llm_client.messages.create(
                    model="claude-haiku-4-20250514",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.content[0].text
                key_points = [
                    line.strip("- ").strip()
                    for line in text.split("\n")
                    if line.strip().startswith("-")
                ]
                compressed = "\n".join(f"- {p}" for p in key_points)
                return compressed, key_points
            except Exception as e:
                self._logger.error(f"LLM extraction failed: {e}")
        
        # Fallback: simple extraction
        key_points = self._extract_key_sentences(content, max_sentences=5)
        compressed = "\n".join(f"- {p}" for p in key_points)
        return compressed, key_points
    
    async def _summarize(
        self,
        content: str,
        context: Optional[str] = None,
        llm_client: Optional[Any] = None,
    ) -> str:
        """Summarize content."""
        if llm_client:
            ctx_part = f"\nContext: {context}\n" if context else ""
            prompt = f"""Summarize this content concisely, keeping essential information:
{ctx_part}
Content:
{content}

Keep the summary under 100 words. Focus on key decisions, outcomes, and important details."""
            
            try:
                response = llm_client.messages.create(
                    model="claude-haiku-4-20250514",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text.strip()
            except Exception as e:
                self._logger.error(f"LLM summarization failed: {e}")
        
        # Fallback: simple truncation with key sentences
        sentences = self._extract_key_sentences(content, max_sentences=3)
        return " ".join(sentences)
    
    async def _deduplicate(self, content: str) -> str:
        """Remove duplicate information from content."""
        lines = content.split("\n")
        seen_hashes: set[str] = set()
        unique_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Hash the line (normalized)
            normalized = " ".join(line.lower().split())
            line_hash = hashlib.sha256(normalized.encode()).hexdigest()[:8]
            
            if line_hash not in seen_hashes:
                seen_hashes.add(line_hash)
                unique_lines.append(line)
        
        return "\n".join(unique_lines)
    
    async def _hierarchical_compress(
        self,
        content: str,
        llm_client: Optional[Any] = None,
    ) -> tuple[str, list[str]]:
        """
        Apply hierarchical compression.
        
        Creates a multi-level summary:
        1. High-level overview
        2. Key decisions/outcomes
        3. Important details
        """
        if llm_client:
            prompt = f"""Create a hierarchical summary of this content:

{content}

Format:
## Overview
(1-2 sentences)

## Key Points
- point 1
- point 2
- point 3

## Important Details
(any critical specifics to remember)

Be very concise."""
            
            try:
                response = llm_client.messages.create(
                    model="claude-haiku-4-20250514",
                    max_tokens=400,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.content[0].text.strip()
                key_points = [
                    line.strip("- ").strip()
                    for line in text.split("\n")
                    if line.strip().startswith("-")
                ]
                return text, key_points
            except Exception as e:
                self._logger.error(f"LLM hierarchical compression failed: {e}")
        
        # Fallback
        key_points = self._extract_key_sentences(content, max_sentences=5)
        overview = key_points[0] if key_points else ""
        compressed = f"Overview: {overview}\n\nKey Points:\n"
        compressed += "\n".join(f"- {p}" for p in key_points[1:])
        
        return compressed, key_points
    
    def _extract_key_sentences(
        self,
        content: str,
        max_sentences: int = 5,
    ) -> list[str]:
        """
        Extract key sentences using simple heuristics.
        
        Scores sentences by:
        - Position (first sentences more important)
        - Length (medium length preferred)
        - Keywords (certain words indicate importance)
        """
        import re
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        # Score sentences
        importance_words = {
            "important", "key", "critical", "must", "need", "require",
            "decision", "conclusion", "result", "outcome", "error",
            "fixed", "resolved", "implemented", "created", "updated",
        }
        
        scored = []
        for i, sentence in enumerate(sentences):
            score = 0.0
            
            # Position score (first sentences matter more)
            score += max(0, 1.0 - (i * 0.1))
            
            # Length score (medium length preferred)
            word_count = len(sentence.split())
            if 10 <= word_count <= 30:
                score += 0.5
            elif word_count < 5:
                score -= 0.3
            
            # Keyword score
            words = set(sentence.lower().split())
            matches = words & importance_words
            score += len(matches) * 0.2
            
            scored.append((score, sentence))
        
        # Sort by score and take top sentences
        scored.sort(reverse=True)
        return [s for _, s in scored[:max_sentences]]
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (~4 chars per token)."""
        return len(text) // 4


class MemoryArchiver:
    """
    Archives old memories with compression.
    
    Periodically scans memory entries and applies
    appropriate compression based on age and access patterns.
    """
    
    def __init__(
        self,
        compressor: Optional[MemoryCompressor] = None,
        archive_after_hours: int = 24,
    ):
        """Initialize archiver."""
        self.compressor = compressor or MemoryCompressor()
        self.archive_after_hours = archive_after_hours
        self._logger = get_logger(__name__)
    
    async def process_entries(
        self,
        entries: list[MemoryEntry],
        llm_client: Optional[Any] = None,
    ) -> list[MemoryEntry]:
        """
        Process entries for archival.
        
        Returns updated entries with compression applied where appropriate.
        """
        processed = []
        
        for entry in entries:
            age_hours = (datetime.now() - entry.created_at).total_seconds() / 3600
            
            # Skip recently accessed or already compressed
            if entry.is_compressed:
                processed.append(entry)
                continue
            
            # Check if should compress
            if age_hours >= self.archive_after_hours:
                result = await self.compressor.compress_by_age(entry, llm_client)
                
                entry.summary = result.compressed_content
                entry.key_points = result.key_points
                entry.is_compressed = True
                entry.original_token_count = result.original_tokens
                
                self._logger.debug(
                    f"Archived entry {entry.id}: {result.compression_ratio:.2%} compression"
                )
            
            processed.append(entry)
        
        return processed
