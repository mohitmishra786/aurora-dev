"""
Circuit breaker middleware for AURORA-DEV.

Implements the circuit breaker pattern to prevent
cascading failures when dependencies fail.

Example usage:
    from aurora_dev.middleware.circuit_breaker import circuit_breaker
    
    @circuit_breaker(failure_threshold=5, recovery_timeout=30)
    async def call_external_api():
        ...
"""
import asyncio
import functools
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitMetrics:
    """Metrics for a circuit."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0


@dataclass
class CircuitConfig:
    """Configuration for circuit breaker."""
    
    failure_threshold: int = 5  # Failures to open circuit
    success_threshold: int = 3  # Successes to close circuit
    recovery_timeout: float = 30.0  # Seconds in open state
    half_open_max_calls: int = 3  # Max calls in half-open state
    
    # Exceptions to track
    tracked_exceptions: tuple = field(default_factory=lambda: (Exception,))
    
    # Fallback
    fallback_value: Optional[Any] = None
    fallback_function: Optional[Callable] = None


class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failures exceeded threshold, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitConfig] = None,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit identifier.
            config: Circuit configuration.
        """
        self.name = name
        self.config = config or CircuitConfig()
        self._state = CircuitState.CLOSED
        self._metrics = CircuitMetrics()
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
        self._logger = get_logger(__name__)
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def metrics(self) -> CircuitMetrics:
        """Get circuit metrics."""
        return self._metrics
    
    async def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute.
            *args: Function arguments.
            **kwargs: Function keyword arguments.
            
        Returns:
            Function result or fallback.
            
        Raises:
            CircuitOpenError: If circuit is open.
        """
        async with self._lock:
            # Check state and possibly transition
            await self._check_state_transition()
            
            if self._state == CircuitState.OPEN:
                return await self._handle_open()
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    return await self._handle_open()
                self._half_open_calls += 1
        
        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self._record_success()
            return result
            
        except self.config.tracked_exceptions as e:
            await self._record_failure(e)
            raise
    
    async def _check_state_transition(self) -> None:
        """Check if state should transition."""
        now = time.time()
        
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._metrics.last_failure_time:
                elapsed = now - self._metrics.last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    await self._transition_to(CircuitState.HALF_OPEN)
    
    async def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        if new_state == self._state:
            return
        
        old_state = self._state
        self._state = new_state
        self._metrics.state_changes += 1
        
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
        
        self._logger.info(
            f"Circuit '{self.name}' transitioned: {old_state.value} -> {new_state.value}"
        )
    
    async def _record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self._metrics.total_requests += 1
            self._metrics.successful_requests += 1
            self._metrics.consecutive_failures = 0
            self._metrics.last_success_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Check if enough successes to close
                half_open_successes = self._half_open_calls
                if half_open_successes >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
    
    async def _record_failure(self, error: Exception) -> None:
        """Record a failed call."""
        async with self._lock:
            now = time.time()
            self._metrics.total_requests += 1
            self._metrics.failed_requests += 1
            self._metrics.consecutive_failures += 1
            self._metrics.last_failure_time = now
            
            self._logger.warning(
                f"Circuit '{self.name}' failure: {error}"
            )
            
            # Check if should open circuit
            if self._state == CircuitState.CLOSED:
                if self._metrics.consecutive_failures >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)
            
            elif self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                await self._transition_to(CircuitState.OPEN)
    
    async def _handle_open(self) -> Any:
        """Handle request when circuit is open."""
        # Use fallback if available
        if self.config.fallback_function:
            return await self.config.fallback_function()
        
        if self.config.fallback_value is not None:
            return self.config.fallback_value
        
        raise CircuitOpenError(
            f"Circuit '{self.name}' is open, requests blocked"
        )
    
    async def reset(self) -> None:
        """Reset circuit to closed state."""
        async with self._lock:
            self._metrics = CircuitMetrics()
            self._half_open_calls = 0
            await self._transition_to(CircuitState.CLOSED)
    
    def get_status(self) -> dict[str, Any]:
        """Get circuit status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "metrics": {
                "total_requests": self._metrics.total_requests,
                "successful_requests": self._metrics.successful_requests,
                "failed_requests": self._metrics.failed_requests,
                "consecutive_failures": self._metrics.consecutive_failures,
                "state_changes": self._metrics.state_changes,
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
            },
        }


class CircuitOpenError(Exception):
    """Raised when circuit is open."""
    pass


# Global circuit registry
_circuits: dict[str, CircuitBreaker] = {}


def get_circuit(name: str) -> Optional[CircuitBreaker]:
    """Get a circuit breaker by name."""
    return _circuits.get(name)


def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    success_threshold: int = 3,
    recovery_timeout: float = 30.0,
    fallback: Optional[Callable] = None,
):
    """
    Decorator to apply circuit breaker to a function.
    
    Usage:
        @circuit_breaker(failure_threshold=5, recovery_timeout=30)
        async def call_api():
            ...
    """
    def decorator(func):
        circuit_name = name or func.__name__
        
        config = CircuitConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            recovery_timeout=recovery_timeout,
            fallback_function=fallback,
        )
        
        cb = CircuitBreaker(circuit_name, config)
        _circuits[circuit_name] = cb
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await cb.execute(func, *args, **kwargs)
        
        # Attach circuit for introspection
        wrapper._circuit = cb
        return wrapper
    
    return decorator


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that applies circuit breaking to all requests.
    """
    
    def __init__(
        self,
        app,
        circuit: Optional[CircuitBreaker] = None,
    ):
        """Initialize middleware."""
        super().__init__(app)
        self.circuit = circuit or CircuitBreaker("api_main")
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request through circuit breaker."""
        async def _process():
            return await call_next(request)
        
        try:
            return await self.circuit.execute(_process)
        
        except CircuitOpenError:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service unavailable",
                    "detail": "System is currently experiencing issues. Please retry later.",
                    "circuit_state": self.circuit.state.value,
                },
                headers={"Retry-After": str(int(self.circuit.config.recovery_timeout))},
            )
