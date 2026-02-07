"""
Cache infrastructure package for AURORA-DEV.

Exports Redis connection and cache utilities.
"""
from aurora_dev.infrastructure.cache.connection import (
    cache_delete,
    cache_exists,
    cache_expire,
    cache_get,
    cache_set,
    check_health,
    close_pool,
    get_connection_pool,
    get_redis_client,
)

__all__ = [
    "get_connection_pool",
    "get_redis_client",
    "check_health",
    "close_pool",
    "cache_set",
    "cache_get",
    "cache_delete",
    "cache_exists",
    "cache_expire",
]
