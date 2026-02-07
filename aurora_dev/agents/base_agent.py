"""
Base Agent implementation for AURORA-DEV.

This module provides the foundational BaseAgent class that all specialized
agents inherit from. Includes Claude API integration, error handling,
retry logic, token tracking, and response caching.
"""
import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid

from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError

from aurora_dev.core.config import get_settings
from aurora_dev.core.logging import get_agent_logger


class AgentRole(Enum):
    """Enumeration of agent roles/types."""
    
    # Tier 1: Orchestration
    MAESTRO = "maestro"
    MEMORY_COORDINATOR = "memory_coordinator"
    
    # Tier 2: Planning & Research
    ARCHITECT = "architect"
    RESEARCH = "research"
    PRODUCT_ANALYST = "product_analyst"
    
    # Tier 3: Implementation
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    INTEGRATION = "integration"
    
    # Tier 4: Quality Assurance
    TEST_ENGINEER = "test_engineer"
    SECURITY_AUDITOR = "security_auditor"
    CODE_REVIEWER = "code_reviewer"
    VALIDATOR = "validator"
    
    # Tier 5: DevOps
    DEVOPS = "devops"
    DOCUMENTATION = "documentation"
    MONITORING = "monitoring"


class AgentStatus(Enum):
    """Agent execution status."""
    
    IDLE = "idle"
    INITIALIZING = "initializing"
    WORKING = "working"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class TokenUsage:
    """Token usage tracking for API calls."""
    
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens
    
    def add(self, other: "TokenUsage") -> None:
        """Add another token usage to this one."""
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_creation_tokens += other.cache_creation_tokens
        self.cache_read_tokens += other.cache_read_tokens
    
    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class AgentResponse:
    """Response from an agent execution."""
    
    content: str
    token_usage: TokenUsage
    model: str
    stop_reason: str
    execution_time_ms: float
    from_cache: bool = False
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return self.error is None


class ResponseCache:
    """Simple in-memory response cache for deterministic queries."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600) -> None:
        """
        Initialize the response cache.
        
        Args:
            max_size: Maximum number of cached responses.
            ttl_seconds: Time-to-live for cached entries in seconds.
        """
        self._cache: dict[str, tuple[AgentResponse, float]] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
    
    def _generate_key(self, messages: list[dict], system: str, model: str) -> str:
        """Generate a cache key from the request parameters."""
        content = json.dumps({
            "messages": messages,
            "system": system,
            "model": model,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(
        self, messages: list[dict], system: str, model: str
    ) -> Optional[AgentResponse]:
        """Get a cached response if available and not expired."""
        key = self._generate_key(messages, system, model)
        if key in self._cache:
            response, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl_seconds:
                return response
            else:
                del self._cache[key]
        return None
    
    def set(
        self, messages: list[dict], system: str, model: str, response: AgentResponse
    ) -> None:
        """Cache a response."""
        if len(self._cache) >= self._max_size:
            # Remove oldest entry
            oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        key = self._generate_key(messages, system, model)
        self._cache[key] = (response, time.time())
    
    def clear(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()


class BaseAgent(ABC):
    """
    Abstract base class for all AURORA-DEV agents.
    
    Provides common functionality including:
    - Claude API integration with configurable models
    - Error handling with retry logic and exponential backoff
    - Token usage tracking
    - Response caching for deterministic queries
    - Structured logging with agent context
    
    Subclasses must implement:
    - role: The agent's role/type
    - system_prompt: The agent's system prompt
    - execute(): Main execution logic
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        model: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        enable_cache: bool = True,
    ) -> None:
        """
        Initialize the base agent.
        
        Args:
            name: Human-readable agent name.
            model: Claude model to use (defaults to config).
            project_id: Associated project ID.
            session_id: Session identifier for tracking.
            enable_cache: Whether to enable response caching.
        """
        self._settings = get_settings()
        self._agent_id = str(uuid.uuid4())
        self._name = name or f"{self.role.value}-{self._agent_id[:8]}"
        self._model = model or self._settings.agent.default_model
        self._project_id = project_id
        self._session_id = session_id or str(uuid.uuid4())
        
        # Initialize Claude client
        self._client = Anthropic(api_key=self._settings.anthropic.api_key)
        
        # Token tracking
        self._total_usage = TokenUsage()
        self._request_count = 0
        
        # Response cache
        self._cache = ResponseCache() if enable_cache else None
        
        # Status tracking
        self._status = AgentStatus.IDLE
        self._created_at = datetime.now(timezone.utc)
        self._last_activity_at: Optional[datetime] = None
        
        # Logger with context
        self._logger = get_agent_logger(
            agent_name=self.role.value,
            agent_id=self._agent_id,
            session_id=self._session_id,
        )
        
        self._logger.info(
            f"Agent initialized: {self._name}",
            extra={"model": self._model, "project_id": project_id},
        )
    
    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """Return the agent's role."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the agent's system prompt."""
        pass
    
    @property
    def agent_id(self) -> str:
        """Return the unique agent ID."""
        return self._agent_id
    
    @property
    def name(self) -> str:
        """Return the agent name."""
        return self._name
    
    @property
    def model(self) -> str:
        """Return the model being used."""
        return self._model
    
    @property
    def status(self) -> AgentStatus:
        """Return current agent status."""
        return self._status
    
    @property
    def total_usage(self) -> TokenUsage:
        """Return total token usage."""
        return self._total_usage
    
    @property
    def request_count(self) -> int:
        """Return total number of API requests made."""
        return self._request_count
    
    def _set_status(self, status: AgentStatus) -> None:
        """Update agent status."""
        old_status = self._status
        self._status = status
        self._last_activity_at = datetime.now(timezone.utc)
        self._logger.debug(
            f"Status changed: {old_status.value} -> {status.value}"
        )
    
    def _call_api(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> AgentResponse:
        """
        Make a synchronous API call to Claude.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            use_cache: Whether to use response cache.
            
        Returns:
            AgentResponse with content and metadata.
        """
        # Check cache first
        if use_cache and self._cache:
            cached = self._cache.get(messages, self.system_prompt, self._model)
            if cached:
                self._logger.debug("Cache hit for request")
                cached.from_cache = True
                return cached
        
        start_time = time.time()
        settings = self._settings.agent
        last_error: Optional[Exception] = None
        
        for attempt in range(settings.max_retries + 1):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=self.system_prompt,
                    messages=messages,
                )
                
                # Extract token usage
                usage = TokenUsage(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
                
                # Handle cache tokens if present
                if hasattr(response.usage, "cache_creation_input_tokens"):
                    usage.cache_creation_tokens = (
                        response.usage.cache_creation_input_tokens or 0
                    )
                if hasattr(response.usage, "cache_read_input_tokens"):
                    usage.cache_read_tokens = (
                        response.usage.cache_read_input_tokens or 0
                    )
                
                # Update tracking
                self._total_usage.add(usage)
                self._request_count += 1
                
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Extract content
                content = ""
                if response.content:
                    content = response.content[0].text
                
                agent_response = AgentResponse(
                    content=content,
                    token_usage=usage,
                    model=self._model,
                    stop_reason=response.stop_reason or "unknown",
                    execution_time_ms=execution_time_ms,
                )
                
                # Cache the response
                if use_cache and self._cache:
                    self._cache.set(
                        messages, self.system_prompt, self._model, agent_response
                    )
                
                self._logger.info(
                    f"API call successful",
                    extra={
                        "tokens": usage.total_tokens,
                        "execution_time_ms": execution_time_ms,
                        "attempt": attempt + 1,
                    },
                )
                
                return agent_response
                
            except RateLimitError as e:
                last_error = e
                wait_time = min(2 ** attempt * 5, 60)  # Max 60 seconds
                self._logger.warning(
                    f"Rate limit hit, waiting {wait_time}s before retry",
                    extra={"attempt": attempt + 1},
                )
                time.sleep(wait_time)
                
            except APIConnectionError as e:
                last_error = e
                wait_time = min(2 ** attempt * 2, 30)
                self._logger.warning(
                    f"API connection error, waiting {wait_time}s before retry",
                    extra={"attempt": attempt + 1, "error": str(e)},
                )
                time.sleep(wait_time)
                
            except APIError as e:
                last_error = e
                self._logger.error(
                    f"API error: {e.message}",
                    extra={"status_code": e.status_code, "attempt": attempt + 1},
                )
                # Don't retry on client errors (4xx)
                if e.status_code and 400 <= e.status_code < 500:
                    break
                wait_time = min(2 ** attempt * 2, 30)
                time.sleep(wait_time)
        
        # All retries failed
        execution_time_ms = (time.time() - start_time) * 1000
        error_msg = str(last_error) if last_error else "Unknown error"
        
        self._logger.error(
            f"API call failed after {settings.max_retries + 1} attempts",
            extra={"error": error_msg},
        )
        
        return AgentResponse(
            content="",
            token_usage=TokenUsage(),
            model=self._model,
            stop_reason="error",
            execution_time_ms=execution_time_ms,
            error=error_msg,
        )
    
    async def _call_api_async(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> AgentResponse:
        """
        Make an async API call to Claude.
        
        This wraps the sync call in an executor for now.
        Can be upgraded to use async client when needed.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            use_cache: Whether to use response cache.
            
        Returns:
            AgentResponse with content and metadata.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._call_api(messages, max_tokens, temperature, use_cache),
        )
    
    def chat(
        self,
        message: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AgentResponse:
        """
        Send a single message and get a response.
        
        Args:
            message: The user message to send.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            
        Returns:
            AgentResponse with content and metadata.
        """
        self._set_status(AgentStatus.WORKING)
        try:
            response = self._call_api(
                messages=[{"role": "user", "content": message}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response
        finally:
            self._set_status(AgentStatus.IDLE)
    
    async def chat_async(
        self,
        message: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AgentResponse:
        """
        Send a single message asynchronously.
        
        Args:
            message: The user message to send.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            
        Returns:
            AgentResponse with content and metadata.
        """
        self._set_status(AgentStatus.WORKING)
        try:
            response = await self._call_api_async(
                messages=[{"role": "user", "content": message}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response
        finally:
            self._set_status(AgentStatus.IDLE)
    
    @abstractmethod
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """
        Execute the agent's main task.
        
        Subclasses must implement this method with their specific logic.
        
        Args:
            task: Task definition dictionary.
            
        Returns:
            AgentResponse with execution results.
        """
        pass
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get agent statistics.
        
        Returns:
            Dictionary with agent statistics.
        """
        return {
            "agent_id": self._agent_id,
            "name": self._name,
            "role": self.role.value,
            "model": self._model,
            "status": self._status.value,
            "request_count": self._request_count,
            "token_usage": self._total_usage.to_dict(),
            "created_at": self._created_at.isoformat(),
            "last_activity_at": (
                self._last_activity_at.isoformat()
                if self._last_activity_at else None
            ),
            "project_id": self._project_id,
            "session_id": self._session_id,
        }
    
    def reset_stats(self) -> None:
        """Reset token usage and request count statistics."""
        self._total_usage = TokenUsage()
        self._request_count = 0
        self._logger.info("Agent statistics reset")
    
    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"name={self._name!r}, "
            f"role={self.role.value!r}, "
            f"status={self._status.value!r}"
            f")>"
        )
