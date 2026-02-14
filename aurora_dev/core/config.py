"""
Configuration management for AURORA-DEV.

This module provides centralized configuration management using Pydantic Settings.
All settings are loaded from environment variables and/or .env file.
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnthropicSettings(BaseSettings):
    """Anthropic API configuration."""

    model_config = SettingsConfigDict(env_prefix="ANTHROPIC_")

    api_key: str = Field(default="", description="Anthropic API key")


class RedisSettings(BaseSettings):
    """Redis connection configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
    )
    max_connections: int = Field(
        default=50,
        description="Maximum number of connections in the pool",
    )
    socket_timeout: float = Field(
        default=5.0,
        description="Socket timeout in seconds",
    )
    socket_connect_timeout: float = Field(
        default=5.0,
        description="Socket connect timeout in seconds",
    )


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="postgresql://aurora:dev_password@localhost:5432/aurora_dev",
        description="PostgreSQL connection URL",
    )
    pool_size: int = Field(
        default=10,
        description="Connection pool size",
    )
    max_overflow: int = Field(
        default=20,
        description="Maximum overflow connections",
    )
    pool_recycle: int = Field(
        default=3600,
        description="Connection recycle time in seconds",
    )
    echo: bool = Field(
        default=False,
        description="Echo SQL statements for debugging",
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    file: Optional[str] = Field(
        default=None,
        description="Log file path (None for console only)",
    )
    format: str = Field(
        default="json",
        description="Log format (json or text)",
    )
    include_timestamp: bool = Field(
        default=True,
        description="Include timestamp in log output",
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = v.upper()
        if normalized not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return normalized


class PineconeSettings(BaseSettings):
    """Pinecone Vector DB configuration."""

    model_config = SettingsConfigDict(env_prefix="PINECONE_")

    api_key: str = Field(
        default="",
        description="Pinecone API key",
    )
    index_name: str = Field(
        default="aurora-memory",
        description="Pinecone index name",
    )
    cloud: str = Field(
        default="aws",
        description="Cloud provider (aws, gcp, azure)",
    )
    region: str = Field(
        default="us-east-1",
        description="Cloud region",
    )
    dimension: int = Field(
        default=1536,
        description="Embedding dimension",
    )


class Mem0Settings(BaseSettings):
    """Mem0 memory service configuration."""

    model_config = SettingsConfigDict(env_prefix="MEM0_")

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for embeddings",
    )
    enabled: bool = Field(
        default=True,
        description="Enable Mem0 integration",
    )


class OpenAISettings(BaseSettings):
    """OpenAI API configuration for embeddings."""

    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    api_key: str = Field(
        default="",
        description="OpenAI API key for embeddings",
    )
    embedding_model: str = Field(
        default="text-embedding-3-large",
        description="OpenAI embedding model name",
    )
    embedding_dimension: int = Field(
        default=1536,
        description="Embedding output dimension",
    )


class GitHubSettings(BaseSettings):
    """GitHub API configuration for research."""

    model_config = SettingsConfigDict(env_prefix="GITHUB_")

    token: str = Field(
        default="",
        description="GitHub Personal Access Token",
    )
    api_base_url: str = Field(
        default="https://api.github.com",
        description="GitHub API base URL",
    )


class AgentSettings(BaseSettings):
    """Agent-specific configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    default_model: str = Field(
        default="claude-3-5-haiku-20241022",
        alias="DEFAULT_MODEL",
        description="Default Claude model to use",
    )
    max_retries: int = Field(
        default=3,
        alias="MAX_RETRIES",
        description="Maximum retry attempts for API calls",
    )
    default_timeout: int = Field(
        default=300,
        alias="DEFAULT_TIMEOUT",
        description="Default timeout in seconds for agent operations",
    )
    reflexion_max_attempts: int = Field(
        default=5,
        description="Maximum attempts for reflexion loops",
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Nested settings
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    pinecone: PineconeSettings = Field(default_factory=PineconeSettings)
    mem0: Mem0Settings = Field(default_factory=Mem0Settings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()
