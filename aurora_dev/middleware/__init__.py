"""
AURORA-DEV Middleware Package.

Production hardening middleware for the API:
- Rate limiting
- Circuit breakers
- Authentication/Authorization
- Request logging
"""
from aurora_dev.middleware.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    rate_limit_middleware,
)
from aurora_dev.middleware.circuit_breaker import (
    CircuitBreakerMiddleware,
    CircuitState,
    circuit_breaker,
)
from aurora_dev.middleware.auth import (
    AuthMiddleware,
    JWTHandler,
    User,
    get_current_user,
)

__all__ = [
    # Rate limiting
    "RateLimiter",
    "RateLimitConfig",
    "rate_limit_middleware",
    # Circuit breaker
    "CircuitBreakerMiddleware",
    "CircuitState",
    "circuit_breaker",
    # Authentication
    "AuthMiddleware",
    "JWTHandler",
    "User",
    "get_current_user",
]
