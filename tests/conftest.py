"""
Pytest configuration and fixtures for AURORA-DEV tests.

This module provides shared fixtures for database, Redis, and configuration testing.
"""
import os
import pytest
from typing import Generator
from unittest.mock import patch


# Set test environment before any imports
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "True"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["LOG_FORMAT"] = "text"


@pytest.fixture(scope="session")
def test_settings():
    """
    Create test settings with overridden values.
    
    This fixture patches the settings to use test-specific configuration.
    """
    from aurora_dev.core.config import Settings
    
    test_env = {
        "ENVIRONMENT": "test",
        "DEBUG": "True",
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "text",
        "DATABASE_URL": "postgresql://aurora:dev_password@localhost:5432/aurora_dev_test",
        "REDIS_URL": "redis://localhost:6379/1",  # Use DB 1 for tests
    }
    
    with patch.dict(os.environ, test_env):
        settings = Settings()
        yield settings


@pytest.fixture(scope="function")
def mock_settings(test_settings):
    """
    Mock get_settings to return test settings.
    
    Use this fixture when you need to control settings in a test.
    """
    from aurora_dev.core import config
    
    with patch.object(config, "get_settings", return_value=test_settings):
        # Clear the cache
        config.get_settings.cache_clear()
        yield test_settings
        config.get_settings.cache_clear()


@pytest.fixture(scope="function")
def db_session(test_settings):
    """
    Create a database session for testing.
    
    This fixture creates all tables before the test and drops them after.
    Requires PostgreSQL to be running.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from aurora_dev.infrastructure.database.models import Base
    
    # Use test database
    engine = create_engine(test_settings.database.url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture(scope="function")
def redis_client(test_settings):
    """
    Create a Redis client for testing.
    
    This fixture uses a separate Redis database (DB 1) for tests
    and flushes it after each test.
    Requires Redis to be running.
    """
    import redis
    
    client = redis.Redis.from_url(
        test_settings.redis.url,
        decode_responses=True,
    )
    
    # Flush the test database before test
    client.flushdb()
    
    try:
        yield client
    finally:
        # Flush after test
        client.flushdb()
        client.close()


@pytest.fixture(scope="function")
def logger():
    """Create a test logger."""
    from aurora_dev.core.logging import get_logger
    
    return get_logger("test")


@pytest.fixture(scope="function")
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing",
        "repository_url": "https://github.com/test/project",
    }


@pytest.fixture(scope="function")
def sample_task_data():
    """Sample task data for testing."""
    return {
        "name": "Test Task",
        "description": "A test task for unit testing",
        "priority": 5,
        "complexity_score": 3,
        "estimated_duration_seconds": 3600,
    }
