"""
Redis cache connection management for AURORA-DEV.

This module provides Redis connection pooling, health checks,
and utility functions for cache operations.
"""
from typing import Optional

import redis
from redis import ConnectionPool, Redis

from aurora_dev.core.config import get_settings
from aurora_dev.core.logging import get_logger

logger = get_logger("cache")

# Global connection pool
_pool: ConnectionPool | None = None


def get_connection_pool() -> ConnectionPool:
    """
    Get or create the Redis connection pool.

    Returns:
        The Redis connection pool.
    """
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool.from_url(
            settings.redis.url,
            max_connections=settings.redis.max_connections,
            socket_timeout=settings.redis.socket_timeout,
            socket_connect_timeout=settings.redis.socket_connect_timeout,
            decode_responses=True,
        )
        logger.info(
            "Redis connection pool created",
            extra={"max_connections": settings.redis.max_connections},
        )
    return _pool


def get_redis_client() -> Redis:
    """
    Get a Redis client from the connection pool.

    Returns:
        A Redis client instance.
    """
    pool = get_connection_pool()
    return Redis(connection_pool=pool)


def check_health() -> bool:
    """
    Check Redis connectivity.

    Returns:
        True if Redis is accessible, False otherwise.
    """
    try:
        client = get_redis_client()
        client.ping()
        logger.debug("Redis health check passed")
        return True
    except redis.RedisError as e:
        logger.error(f"Redis health check failed: {e}")
        return False


def close_pool() -> None:
    """Close the Redis connection pool."""
    global _pool
    if _pool is not None:
        _pool.disconnect()
        _pool = None
        logger.info("Redis connection pool closed")


# Utility functions for common cache operations


def cache_set(
    key: str,
    value: str,
    expire_seconds: Optional[int] = None,
) -> bool:
    """
    Set a value in the cache.

    Args:
        key: The cache key.
        value: The value to cache.
        expire_seconds: Optional TTL in seconds.

    Returns:
        True if successful.
    """
    client = get_redis_client()
    if expire_seconds:
        return bool(client.setex(key, expire_seconds, value))
    return bool(client.set(key, value))


def cache_get(key: str) -> Optional[str]:
    """
    Get a value from the cache.

    Args:
        key: The cache key.

    Returns:
        The cached value or None if not found.
    """
    client = get_redis_client()
    return client.get(key)


def cache_delete(key: str) -> bool:
    """
    Delete a value from the cache.

    Args:
        key: The cache key.

    Returns:
        True if the key was deleted.
    """
    client = get_redis_client()
    return bool(client.delete(key))


def cache_exists(key: str) -> bool:
    """
    Check if a key exists in the cache.

    Args:
        key: The cache key.

    Returns:
        True if the key exists.
    """
    client = get_redis_client()
    return bool(client.exists(key))


def cache_expire(key: str, seconds: int) -> bool:
    """
    Set expiration on a key.

    Args:
        key: The cache key.
        seconds: TTL in seconds.

    Returns:
        True if expiration was set.
    """
    client = get_redis_client()
    return bool(client.expire(key, seconds))
