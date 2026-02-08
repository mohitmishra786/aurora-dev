"""
Infrastructure package for AURORA-DEV.

Provides database, cache, messaging, and container execution infrastructure.
"""
from aurora_dev.infrastructure import cache, database

# Lazy import for docker_runner to avoid import errors if docker is not installed
def get_docker_runner():
    """Get DockerRunner instance (lazy import)."""
    from aurora_dev.infrastructure.docker_runner import get_runner
    return get_runner()

__all__ = [
    "database",
    "cache",
    "get_docker_runner",
]
