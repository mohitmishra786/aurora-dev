"""
Rate limiting middleware for AURORA-DEV API.

Provides request rate limiting with multiple strategies:
- Per-IP limits
- Per-user limits
- Per-endpoint limits
- Token bucket algorithm

Example usage:
    from aurora_dev.middleware.rate_limiter import RateLimiter, rate_limit_middleware
    
    limiter = RateLimiter()
    app.add_middleware(rate_limit_middleware, limiter=limiter)
"""
import time
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class LimitStrategy(Enum):
    """Rate limiting strategies."""
    
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    strategy: LimitStrategy = LimitStrategy.TOKEN_BUCKET
    
    # Per-endpoint overrides
    endpoint_limits: dict[str, int] = field(default_factory=dict)
    
    # Exemptions
    exempt_paths: list[str] = field(default_factory=lambda: ["/health", "/docs", "/openapi.json"])
    exempt_ips: list[str] = field(default_factory=list)


@dataclass
class RateLimitState:
    """State for a single rate limit bucket."""
    
    tokens: float
    last_update: float
    request_count: int = 0
    window_start: float = 0.0


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Implements token bucket algorithm with configurable
    refill rate and burst capacity.
    """
    
    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
    ):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limit configuration.
        """
        self.config = config or RateLimitConfig()
        self._buckets: dict[str, RateLimitState] = {}
        self._lock = asyncio.Lock()
        self._logger = get_logger(__name__)
        
        # Calculate refill rate (tokens per second)
        self._refill_rate = self.config.requests_per_minute / 60.0
    
    async def is_allowed(
        self,
        key: str,
        cost: int = 1,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Rate limit key (IP, user ID, etc.).
            cost: Token cost for this request.
            
        Returns:
            Tuple of (is_allowed, headers_dict).
        """
        async with self._lock:
            now = time.time()
            
            # Get or create bucket
            if key not in self._buckets:
                self._buckets[key] = RateLimitState(
                    tokens=self.config.burst_size,
                    last_update=now,
                    window_start=now,
                )
            
            bucket = self._buckets[key]
            
            # Refill tokens based on elapsed time
            elapsed = now - bucket.last_update
            refill = elapsed * self._refill_rate
            bucket.tokens = min(
                self.config.burst_size,
                bucket.tokens + refill,
            )
            bucket.last_update = now
            
            # Check if allowed
            if bucket.tokens >= cost:
                bucket.tokens -= cost
                bucket.request_count += 1
                
                headers = self._get_headers(bucket)
                return True, headers
            
            # Calculate retry delay
            tokens_needed = cost - bucket.tokens
            retry_after = tokens_needed / self._refill_rate
            
            headers = self._get_headers(bucket)
            headers["Retry-After"] = str(int(retry_after) + 1)
            
            self._logger.warning(f"Rate limit exceeded for key: {key}")
            
            return False, headers
    
    async def check_endpoint_limit(
        self,
        endpoint: str,
        key: str,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check rate limit for a specific endpoint.
        
        Uses endpoint-specific limits if configured.
        """
        endpoint_key = f"{key}:{endpoint}"
        
        # Use endpoint-specific limit if configured
        if endpoint in self.config.endpoint_limits:
            limit = self.config.endpoint_limits[endpoint]
            temp_config = RateLimitConfig(requests_per_minute=limit)
            temp_limiter = RateLimiter(temp_config)
            return await temp_limiter.is_allowed(endpoint_key)
        
        return await self.is_allowed(endpoint_key)
    
    def _get_headers(self, bucket: RateLimitState) -> dict[str, str]:
        """Generate rate limit headers."""
        return {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(int(bucket.tokens)),
            "X-RateLimit-Reset": str(int(bucket.last_update + 60)),
        }
    
    def is_exempt(self, path: str, ip: str) -> bool:
        """Check if request is exempt from rate limiting."""
        if path in self.config.exempt_paths:
            return True
        if ip in self.config.exempt_ips:
            return True
        return False
    
    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        async with self._lock:
            if key in self._buckets:
                del self._buckets[key]
    
    async def get_status(self, key: str) -> Optional[dict[str, Any]]:
        """Get current rate limit status for a key."""
        bucket = self._buckets.get(key)
        if not bucket:
            return None
        
        return {
            "key": key,
            "tokens_remaining": bucket.tokens,
            "requests_made": bucket.request_count,
            "limit": self.config.requests_per_minute,
            "burst_size": self.config.burst_size,
        }


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    # Check forwarded headers
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check real IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection
    if request.client:
        return request.client.host
    
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    """
    
    def __init__(
        self,
        app,
        limiter: Optional[RateLimiter] = None,
        key_func: Optional[Callable[[Request], str]] = None,
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application.
            limiter: Rate limiter instance.
            key_func: Function to extract rate limit key from request.
        """
        super().__init__(app)
        self.limiter = limiter or RateLimiter()
        self.key_func = key_func or get_client_ip
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request through rate limiting."""
        # Get client identifier
        key = self.key_func(request)
        path = request.url.path
        ip = get_client_ip(request)
        
        # Check exemptions
        if self.limiter.is_exempt(path, ip):
            return await call_next(request)
        
        # Check rate limit
        allowed, headers = await self.limiter.is_allowed(key)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": "Too many requests. Please slow down.",
                    "retry_after": headers.get("Retry-After", "60"),
                },
                headers=headers,
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        for header, value in headers.items():
            response.headers[header] = value
        
        return response


def rate_limit_middleware(
    limiter: Optional[RateLimiter] = None,
) -> RateLimitMiddleware:
    """
    Create rate limit middleware.
    
    Usage:
        app.add_middleware(RateLimitMiddleware, limiter=RateLimiter())
    """
    return lambda app: RateLimitMiddleware(app, limiter=limiter)


# Decorator for endpoint-specific limits
def rate_limit(
    requests_per_minute: int = 30,
):
    """
    Decorator to apply rate limiting to a specific endpoint.
    
    Usage:
        @app.get("/expensive")
        @rate_limit(requests_per_minute=10)
        async def expensive_operation():
            ...
    """
    def decorator(func):
        func._rate_limit = requests_per_minute
        return func
    return decorator
