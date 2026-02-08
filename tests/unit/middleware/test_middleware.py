"""
Tests for production hardening middleware.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock


class TestRateLimiter:
    """Tests for rate limiter."""
    
    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig default values."""
        from aurora_dev.middleware.rate_limiter import RateLimitConfig
        
        config = RateLimitConfig()
        
        assert config.requests_per_minute == 60
        assert config.burst_size == 10
        assert "/health" in config.exempt_paths
    
    def test_rate_limiter_init(self):
        """Test RateLimiter initialization."""
        from aurora_dev.middleware.rate_limiter import RateLimiter, RateLimitConfig
        
        config = RateLimitConfig(requests_per_minute=30)
        limiter = RateLimiter(config)
        
        assert limiter.config.requests_per_minute == 30
    
    @pytest.mark.asyncio
    async def test_is_allowed_first_request(self):
        """Test that first request is allowed."""
        from aurora_dev.middleware.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        allowed, headers = await limiter.is_allowed("test-client")
        
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario."""
        from aurora_dev.middleware.rate_limiter import RateLimiter, RateLimitConfig
        
        config = RateLimitConfig(burst_size=2, requests_per_minute=1)
        limiter = RateLimiter(config)
        
        # Use up burst
        await limiter.is_allowed("test-client")
        await limiter.is_allowed("test-client")
        
        # Should be rate limited
        allowed, headers = await limiter.is_allowed("test-client")
        
        assert allowed is False
        assert "Retry-After" in headers
    
    def test_is_exempt_path(self):
        """Test exemption for paths."""
        from aurora_dev.middleware.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        assert limiter.is_exempt("/health", "127.0.0.1") is True
        assert limiter.is_exempt("/api/v1/tasks", "127.0.0.1") is False


class TestCircuitBreaker:
    """Tests for circuit breaker."""
    
    def test_circuit_state_enum(self):
        """Test CircuitState enum values."""
        from aurora_dev.middleware.circuit_breaker import CircuitState
        
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"
    
    def test_circuit_breaker_init(self):
        """Test CircuitBreaker initialization."""
        from aurora_dev.middleware.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker("test-circuit")
        
        assert cb.name == "test-circuit"
        assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution through circuit."""
        from aurora_dev.middleware.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker("test")
        
        async def success_func():
            return "success"
        
        result = await cb.execute(success_func)
        
        assert result == "success"
        assert cb.metrics.successful_requests == 1
    
    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self):
        """Test circuit opens after threshold failures."""
        from aurora_dev.middleware.circuit_breaker import (
            CircuitBreaker, CircuitConfig, CircuitState
        )
        
        config = CircuitConfig(failure_threshold=2)
        cb = CircuitBreaker("test", config)
        
        async def failing_func():
            raise Exception("Test failure")
        
        # Cause failures up to threshold
        for _ in range(2):
            try:
                await cb.execute(failing_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN
    
    def test_get_status(self):
        """Test circuit status reporting."""
        from aurora_dev.middleware.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker("test-circuit")
        status = cb.get_status()
        
        assert status["name"] == "test-circuit"
        assert status["state"] == "closed"
        assert "metrics" in status


class TestAuth:
    """Tests for authentication middleware."""
    
    def test_user_role_enum(self):
        """Test UserRole enum values."""
        from aurora_dev.middleware.auth import UserRole
        
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.DEVELOPER.value == "developer"
    
    def test_user_has_permission_admin(self):
        """Test admin has all permissions."""
        from aurora_dev.middleware.auth import User, UserRole
        
        admin = User(
            id="1",
            username="admin",
            email="admin@test.com",
            role=UserRole.ADMIN,
        )
        
        assert admin.has_permission("anything") is True
        assert admin.has_permission("projects:delete") is True
    
    def test_user_has_permission_developer(self):
        """Test developer permissions."""
        from aurora_dev.middleware.auth import User, UserRole
        
        dev = User(
            id="2",
            username="dev",
            email="dev@test.com",
            role=UserRole.DEVELOPER,
        )
        
        assert dev.has_permission("projects:read") is True
        assert dev.has_permission("projects:write") is True
    
    def test_jwt_handler_create_token(self):
        """Test JWT token creation."""
        from aurora_dev.middleware.auth import JWTHandler, User, UserRole
        
        handler = JWTHandler(secret_key="test-secret-key")
        
        user = User(
            id="1",
            username="test",
            email="test@example.com",
            role=UserRole.DEVELOPER,
        )
        
        token = handler.create_access_token(user)
        
        assert token is not None
        assert len(token.split(".")) == 3  # JWT format
    
    def test_jwt_handler_verify_token(self):
        """Test JWT token verification."""
        from aurora_dev.middleware.auth import JWTHandler, User, UserRole
        
        handler = JWTHandler(secret_key="test-secret-key")
        
        user = User(
            id="1",
            username="test",
            email="test@example.com",
            role=UserRole.DEVELOPER,
        )
        
        token = handler.create_access_token(user)
        payload = handler.verify_token(token)
        
        assert payload is not None
        assert payload.sub == "1"
        assert payload.username == "test"
    
    def test_password_hasher(self):
        """Test password hashing."""
        from aurora_dev.middleware.auth import PasswordHasher
        
        password = "test-password-123"
        hashed = PasswordHasher.hash_password(password)
        
        assert PasswordHasher.verify_password(password, hashed) is True
        assert PasswordHasher.verify_password("wrong", hashed) is False
