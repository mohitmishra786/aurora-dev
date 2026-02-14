"""
Context Window Validator for AURORA-DEV.

Validates that prompts fit within model context windows before
sending API calls. Prevents truncation errors and wasted tokens.

Gap B7: Missing context window validation.
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Model context window limits (in tokens)
MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
    "claude-3-opus": 200_000,
    "claude-3-sonnet": 200_000,
    "claude-3-haiku": 200_000,
    "claude-3.5-sonnet": 200_000,
    "gemini-pro": 1_000_000,
    "gemini-1.5-pro": 1_000_000,
}

# Reserved tokens for completion output
DEFAULT_COMPLETION_RESERVE = 4_096


def estimate_tokens(text: str, model: str = "gpt-4o") -> int:
    """Estimate token count for a text string.
    
    Uses a simple heuristic (~4 chars per token for English text).
    For production, integrate tiktoken or model-specific tokenizers.
    
    Args:
        text: Input text.
        model: Model name (for future tokenizer selection).
        
    Returns:
        Estimated token count.
    """
    # Rough heuristic: 1 token ≈ 4 characters for English
    return max(1, len(text) // 4)


def estimate_messages_tokens(
    messages: list[dict[str, str]],
    model: str = "gpt-4o",
) -> int:
    """Estimate tokens for a list of chat messages.
    
    Args:
        messages: Chat messages with role/content.
        model: Model name.
        
    Returns:
        Estimated total token count.
    """
    total = 0
    for msg in messages:
        # Per-message overhead ≈ 4 tokens
        total += 4
        total += estimate_tokens(msg.get("content", ""), model)
        total += estimate_tokens(msg.get("role", ""), model)
    # Add priming tokens
    total += 3
    return total


class ContextWindowValidator:
    """Validates that prompts fit within model context windows.
    
    Example:
        >>> validator = ContextWindowValidator("gpt-4o")
        >>> if validator.fits(messages, max_completion=4096):
        ...     response = api.call(messages)
        >>> else:
        ...     messages = validator.truncate(messages, max_completion=4096)
    """
    
    def __init__(
        self,
        model: str = "gpt-4o",
        completion_reserve: int = DEFAULT_COMPLETION_RESERVE,
    ) -> None:
        self._model = model
        self._completion_reserve = completion_reserve
        self._context_limit = MODEL_CONTEXT_LIMITS.get(model, 128_000)
    
    @property
    def available_prompt_tokens(self) -> int:
        """Maximum tokens available for the prompt."""
        return self._context_limit - self._completion_reserve
    
    def fits(
        self,
        messages: list[dict[str, str]],
        max_completion: Optional[int] = None,
    ) -> bool:
        """Check if messages fit within the context window.
        
        Args:
            messages: Chat messages.
            max_completion: Override completion token reserve.
            
        Returns:
            True if messages fit.
        """
        reserve = max_completion or self._completion_reserve
        prompt_tokens = estimate_messages_tokens(messages, self._model)
        return prompt_tokens <= (self._context_limit - reserve)
    
    def get_usage_info(
        self,
        messages: list[dict[str, str]],
        max_completion: Optional[int] = None,
    ) -> dict[str, Any]:
        """Get detailed context window usage information.
        
        Args:
            messages: Chat messages.
            max_completion: Override completion token reserve.
            
        Returns:
            Usage details.
        """
        reserve = max_completion or self._completion_reserve
        prompt_tokens = estimate_messages_tokens(messages, self._model)
        available = self._context_limit - reserve
        
        return {
            "model": self._model,
            "context_limit": self._context_limit,
            "completion_reserve": reserve,
            "available_for_prompt": available,
            "estimated_prompt_tokens": prompt_tokens,
            "remaining": available - prompt_tokens,
            "utilization": f"{prompt_tokens / available:.1%}" if available > 0 else "N/A",
            "fits": prompt_tokens <= available,
        }
    
    def truncate(
        self,
        messages: list[dict[str, str]],
        max_completion: Optional[int] = None,
        keep_system: bool = True,
    ) -> list[dict[str, str]]:
        """Truncate messages to fit within context window.
        
        Strategy: Keep system message + last N messages that fit.
        
        Args:
            messages: Chat messages.
            max_completion: Override completion token reserve.
            keep_system: Whether to always keep system messages.
            
        Returns:
            Truncated messages.
        """
        if self.fits(messages, max_completion):
            return messages
        
        reserve = max_completion or self._completion_reserve
        available = self._context_limit - reserve
        
        # Separate system messages
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        # Calculate system message tokens
        system_tokens = sum(
            estimate_messages_tokens([m], self._model)
            for m in system_msgs
        ) if keep_system else 0
        
        remaining = available - system_tokens
        
        # Add messages from the end (most recent first)
        kept: list[dict[str, str]] = []
        for msg in reversed(other_msgs):
            msg_tokens = estimate_messages_tokens([msg], self._model)
            if remaining >= msg_tokens:
                kept.insert(0, msg)
                remaining -= msg_tokens
            else:
                break
        
        result = (system_msgs if keep_system else []) + kept
        
        logger.info(
            f"Truncated context: {len(messages)} -> {len(result)} messages "
            f"({estimate_messages_tokens(result, self._model)} tokens)"
        )
        
        return result
