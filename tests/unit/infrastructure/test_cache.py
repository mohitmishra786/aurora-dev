"""Unit tests for cache infrastructure."""
from unittest.mock import MagicMock, patch

import pytest


class TestCacheConnection:
    """Tests for cache connection module."""

    def test_get_connection_pool_returns_pool(self, mock_settings):
        """Test that get_connection_pool returns a pool."""
        from aurora_dev.infrastructure.cache.connection import (
            get_connection_pool,
            close_pool,
        )
        
        pool = get_connection_pool()
        assert pool is not None
        
        # Cleanup
        close_pool()

    def test_get_redis_client_returns_client(self, mock_settings):
        """Test that get_redis_client returns a client."""
        from aurora_dev.infrastructure.cache.connection import (
            get_redis_client,
            close_pool,
        )
        
        client = get_redis_client()
        assert client is not None
        
        # Cleanup
        close_pool()

    def test_close_pool_clears_global(self, mock_settings):
        """Test that close_pool clears the global pool."""
        from aurora_dev.infrastructure.cache import connection
        from aurora_dev.infrastructure.cache.connection import (
            get_connection_pool,
            close_pool,
        )
        
        # Create pool
        get_connection_pool()
        assert connection._pool is not None
        
        # Close pool
        close_pool()
        assert connection._pool is None


class TestCacheUtilities:
    """Tests for cache utility functions."""

    @patch("aurora_dev.infrastructure.cache.connection.get_redis_client")
    def test_cache_set_calls_redis(self, mock_get_client):
        """Test cache_set calls Redis set."""
        from aurora_dev.infrastructure.cache.connection import cache_set
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        cache_set("test_key", "test_value")
        mock_client.set.assert_called_once_with("test_key", "test_value")

    @patch("aurora_dev.infrastructure.cache.connection.get_redis_client")
    def test_cache_set_with_expire(self, mock_get_client):
        """Test cache_set with expiration."""
        from aurora_dev.infrastructure.cache.connection import cache_set
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        cache_set("test_key", "test_value", expire_seconds=3600)
        mock_client.setex.assert_called_once_with("test_key", 3600, "test_value")

    @patch("aurora_dev.infrastructure.cache.connection.get_redis_client")
    def test_cache_get_calls_redis(self, mock_get_client):
        """Test cache_get calls Redis get."""
        from aurora_dev.infrastructure.cache.connection import cache_get
        
        mock_client = MagicMock()
        mock_client.get.return_value = "test_value"
        mock_get_client.return_value = mock_client
        
        result = cache_get("test_key")
        
        mock_client.get.assert_called_once_with("test_key")
        assert result == "test_value"

    @patch("aurora_dev.infrastructure.cache.connection.get_redis_client")
    def test_cache_delete_calls_redis(self, mock_get_client):
        """Test cache_delete calls Redis delete."""
        from aurora_dev.infrastructure.cache.connection import cache_delete
        
        mock_client = MagicMock()
        mock_client.delete.return_value = 1
        mock_get_client.return_value = mock_client
        
        result = cache_delete("test_key")
        
        mock_client.delete.assert_called_once_with("test_key")
        assert result is True

    @patch("aurora_dev.infrastructure.cache.connection.get_redis_client")
    def test_cache_exists_calls_redis(self, mock_get_client):
        """Test cache_exists calls Redis exists."""
        from aurora_dev.infrastructure.cache.connection import cache_exists
        
        mock_client = MagicMock()
        mock_client.exists.return_value = 1
        mock_get_client.return_value = mock_client
        
        result = cache_exists("test_key")
        
        mock_client.exists.assert_called_once_with("test_key")
        assert result is True


class TestCacheHealthCheck:
    """Tests for cache health check."""

    @patch("aurora_dev.infrastructure.cache.connection.get_redis_client")
    def test_check_health_returns_true_on_success(self, mock_get_client):
        """Test health check returns True when Redis is accessible."""
        from aurora_dev.infrastructure.cache.connection import check_health
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        result = check_health()
        
        mock_client.ping.assert_called_once()
        assert result is True

    @patch("aurora_dev.infrastructure.cache.connection.get_redis_client")
    def test_check_health_returns_false_on_failure(self, mock_get_client):
        """Test health check returns False when Redis fails."""
        import redis
        from aurora_dev.infrastructure.cache.connection import check_health
        
        mock_client = MagicMock()
        mock_client.ping.side_effect = redis.RedisError("Connection failed")
        mock_get_client.return_value = mock_client
        
        result = check_health()
        
        assert result is False
