"""Unit tests for configuration management."""
import os
from unittest.mock import patch

import pytest


class TestSettings:
    """Tests for Settings configuration class."""

    def test_settings_loads_defaults(self):
        """Test that settings loads with default values."""
        from aurora_dev.core.config import Settings
        
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(
                _env_file=None,  # Don't load .env file
            )
            
            assert settings.debug is False
            assert settings.environment == "development"

    def test_settings_loads_from_env(self):
        """Test that settings loads from environment variables."""
        from aurora_dev.core.config import Settings
        
        test_env = {
            "DEBUG": "True",
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "WARNING",
            "DEFAULT_MODEL": "claude-haiku-4-20250514",
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings(_env_file=None)
            
            assert settings.debug is True
            assert settings.environment == "production"
            assert settings.logging.level == "WARNING"
            assert settings.agent.default_model == "claude-haiku-4-20250514"

    def test_is_development_property(self):
        """Test is_development property."""
        from aurora_dev.core.config import Settings
        
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.is_development is True
            assert settings.is_production is False

    def test_is_production_property(self):
        """Test is_production property."""
        from aurora_dev.core.config import Settings
        
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.is_production is True
            assert settings.is_development is False

    def test_log_level_validation(self):
        """Test that invalid log levels raise validation error."""
        from aurora_dev.core.config import LoggingSettings
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            LoggingSettings(level="INVALID")

    def test_log_level_normalized_to_uppercase(self):
        """Test that log level is normalized to uppercase."""
        from aurora_dev.core.config import LoggingSettings
        
        settings = LoggingSettings(level="debug")
        assert settings.level == "DEBUG"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self):
        """Test that get_settings returns a Settings instance."""
        from aurora_dev.core.config import Settings, get_settings
        
        # Clear cache first
        get_settings.cache_clear()
        
        settings = get_settings()
        assert isinstance(settings, Settings)
        
        # Clean up
        get_settings.cache_clear()

    def test_get_settings_is_cached(self):
        """Test that get_settings returns the same instance."""
        from aurora_dev.core.config import get_settings
        
        # Clear cache first
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
        
        # Clean up
        get_settings.cache_clear()


class TestRedisSettings:
    """Tests for Redis settings."""

    def test_redis_url_default(self):
        """Test Redis URL default value."""
        from aurora_dev.core.config import RedisSettings
        
        settings = RedisSettings()
        assert settings.url == "redis://localhost:6379"
        assert settings.max_connections == 50

    def test_redis_url_from_env(self):
        """Test Redis settings from environment."""
        from aurora_dev.core.config import RedisSettings
        
        with patch.dict(os.environ, {
            "REDIS_URL": "redis://custom:6380",
            "REDIS_MAX_CONNECTIONS": "100",
        }):
            settings = RedisSettings()
            assert settings.url == "redis://custom:6380"
            assert settings.max_connections == 100


class TestDatabaseSettings:
    """Tests for database settings."""

    def test_database_url_default(self):
        """Test database URL default value."""
        from aurora_dev.core.config import DatabaseSettings
        
        settings = DatabaseSettings()
        assert "postgresql://" in settings.url
        assert settings.pool_size == 10

    def test_database_settings_from_env(self):
        """Test database settings from environment."""
        from aurora_dev.core.config import DatabaseSettings
        
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://test:test@db:5432/testdb",
            "DATABASE_POOL_SIZE": "20",
        }):
            settings = DatabaseSettings()
            assert settings.url == "postgresql://test:test@db:5432/testdb"
            assert settings.pool_size == 20
