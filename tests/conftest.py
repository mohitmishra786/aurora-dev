"""
Pytest configuration and shared fixtures.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Generator


@pytest.fixture(scope="session")
def mock_anthropic_client() -> Generator:
    """
    Session-scoped mock for Anthropic client.
    
    Provides a consistent mock across all tests to avoid
    making actual API calls.
    """
    with patch("aurora_dev.agents.base_agent.Anthropic") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        
        # Standard successful response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Mock response")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.usage.cache_creation_input_tokens = 0
        mock_response.usage.cache_read_input_tokens = 0
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        
        yield mock


@pytest.fixture(scope="function")
def mock_redis() -> Generator:
    """
    Function-scoped mock for Redis client.
    
    Each test gets a fresh Redis mock to avoid state bleeding.
    """
    with patch("redis.Redis") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        
        # Basic key-value operations
        _store = {}
        
        def mock_get(key):
            return _store.get(key)
        
        def mock_set(key, value, *args, **kwargs):
            _store[key] = value
            return True
        
        def mock_delete(*keys):
            count = 0
            for key in keys:
                if key in _store:
                    del _store[key]
                    count += 1
            return count
        
        mock_client.get.side_effect = mock_get
        mock_client.set.side_effect = mock_set
        mock_client.delete.side_effect = mock_delete
        
        # Pub/sub
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub
        
        yield mock_client


@pytest.fixture
def sample_task_payload() -> dict:
    """Sample task payload for testing."""
    return {
        "task_id": "test-task-001",
        "operation": "implement",
        "agent_type": "backend",
        "parameters": {
            "component": "user_service",
            "requirements": ["CRUD", "validation"],
        },
        "context": {
            "project_id": "proj-123",
            "phase": "implementation",
        },
    }


@pytest.fixture
def sample_agent_config() -> dict:
    """Sample agent configuration for testing."""
    return {
        "name": "TestAgent",
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "temperature": 0.7,
        "enable_cache": True,
        "max_retries": 3,
    }


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "requires_redis: marks tests that require Redis"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marks tests that require API key"
    )
