"""
Settings Configuration

This module provides comprehensive configuration management for the AI framework:
- Environment variable loading
- Configuration file support
- Validation and defaults
- Type-safe configuration access
"""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import Field, validator

from .models import (
    AgentConfig,
    AnthropicConfig,
    APIConfig,
    BackgroundTaskConfig,
    CachingConfig,
    DatabaseConfig,
    ExternalServicesConfig,
    MemoryConfig,
    MonitoringConfig,
    OllamaConfig,
    OpenAIConfig,
    OSS20BConfig,
    RateLimitingConfig,
    RoutingConfig,
    SecurityConfig,
    StorageConfig,
    VectorDBConfig,
    WebSocketConfig,
)

# Constants to replace magic numbers
MIN_PORT = 1
MAX_PORT = 65535
MIN_SECRET_KEY_LENGTH = 32
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BATCH_SIZE = 100
MIN_SUCCESS_RATE = 85.0
EMERGENCY_THRESHOLD = 90


class Settings(BaseSettings):
    """Main settings configuration for the AI framework."""

    # Application settings
    app_name: str = Field(default="AI Framework", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database settings
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # LLM Provider settings
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    oss20b: OSS20BConfig = Field(default_factory=OSS20BConfig)

    # Model routing settings
    routing: RoutingConfig = Field(default_factory=RoutingConfig)

    # Agent settings
    agents: AgentConfig = Field(default_factory=AgentConfig)

    # Memory settings
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

    # Vector database settings
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)

    # Monitoring settings
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Security settings
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # API settings
    api: APIConfig = Field(default_factory=APIConfig)

    # WebSocket settings
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)

    # Background task settings
    background_tasks: BackgroundTaskConfig = Field(default_factory=BackgroundTaskConfig)

    # Rate limiting settings
    rate_limiting: RateLimitingConfig = Field(default_factory=RateLimitingConfig)

    # Caching settings
    caching: CachingConfig = Field(default_factory=CachingConfig)

    # File storage settings
    storage: StorageConfig = Field(default_factory=StorageConfig)

    # External service settings
    external_services: ExternalServicesConfig = Field(default_factory=ExternalServicesConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("database")
    def validate_database(cls, v):
        """Validate database configuration."""
        if v.type not in ["sqlite", "postgresql", "mysql"]:
            raise ValueError(f"Unsupported database type: {v.type}")
        return v

    @validator("openai")
    def validate_openai(cls, v):
        """Validate OpenAI configuration."""
        if v.enabled and not v.api_key:
            raise ValueError("OpenAI API key is required when OpenAI is enabled")
        return v

    @validator("anthropic")
    def validate_anthropic(cls, v):
        """Validate Anthropic configuration."""
        if v.enabled and not v.api_key:
            raise ValueError("Anthropic API key is required when Anthropic is enabled")
        return v

    @validator("ollama")
    def validate_ollama(cls, v):
        """Validate Ollama configuration."""
        if v.enabled and not v.base_url:
            raise ValueError("Ollama base URL is required when Ollama is enabled")
        return v

    @validator("oss20b")
    def validate_oss20b(cls, v):
        """Validate OSS-20B configuration."""
        if v.enabled and not v.model_path:
            raise ValueError("OSS-20B model path is required when OSS-20B is enabled")
        return v

    @validator("vector_db")
    def validate_vector_db(cls, v):
        """Validate vector database configuration."""
        if v.enabled and v.type not in ["chroma", "pinecone", "weaviate"]:
            raise ValueError(f"Unsupported vector database type: {v.type}")
        return v

    @validator("security")
    def validate_security(cls, v):
        """Validate security configuration."""
        if v.enable_auth and not v.secret_key:
            raise ValueError("Secret key is required when authentication is enabled")
        return v

    def get_provider_config(self, provider: str) -> dict[str, Any]:
        """Get configuration for a specific provider."""
        provider_configs = {
            "openai": self.openai.dict(),
            "anthropic": self.anthropic.dict(),
            "ollama": self.ollama.dict(),
            "oss20b": self.oss20b.dict()
        }
        return provider_configs.get(provider, {})

    def is_provider_enabled(self, provider: str) -> bool:
        """Check if a provider is enabled."""
        provider_configs = {
            "openai": self.openai.enabled,
            "anthropic": self.anthropic.enabled,
            "ollama": self.ollama.enabled,
            "oss20b": self.oss20b.enabled
        }
        return provider_configs.get(provider, False)

    def get_enabled_providers(self) -> list[str]:
        """Get list of enabled providers."""
        return [provider for provider in ["openai", "anthropic", "ollama", "oss20b"]
                if self.is_provider_enabled(provider)]

    def get_model_config(self, provider: str, model: str) -> dict[str, Any] | None:
        """Get configuration for a specific model."""
        provider_config = self.get_provider_config(provider)
        models = provider_config.get("models", [])

        for model_config in models:
            if model_config.get("name") == model:
                return model_config
        return None

    def get_rate_limit(self, provider: str) -> int:
        """Get rate limit for a provider."""
        provider_config = self.get_provider_config(provider)
        return provider_config.get("rate_limit", 100)

    def get_cost_limit(self, provider: str) -> float:
        """Get cost limit for a provider."""
        provider_config = self.get_provider_config(provider)
        return provider_config.get("cost_limit", 10.0)

    def get_timeout(self, provider: str) -> int:
        """Get timeout for a provider."""
        provider_config = self.get_provider_config(provider)
        return provider_config.get("timeout", 30)

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return self.dict()

    def save_to_file(self, file_path: str | Path):
        """Save settings to a file."""
        file_path = Path(file_path)

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save
        config_dict = self.to_dict()

        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> "Settings":
        """Load settings from a file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path) as f:
            config_dict = json.load(f)

        return cls(**config_dict)

    def merge_with_file(self, file_path: str | Path):
        """Merge settings with a file."""
        file_path = Path(file_path)

        if not file_path.exists():
            return

        with open(file_path) as f:
            file_config = json.load(f)

        # Update current settings with file config
        for key, value in file_config.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate_all(self) -> list[str]:
        """Validate all configuration and return list of errors."""
        errors = []

        try:
            # Validate database connection
            if self.database.enabled:
                # Add database-specific validation here
                pass
        except Exception as e:
            errors.append(f"Database validation failed: {e}")

        try:
            # Validate vector database
            if self.vector_db.enabled:
                # Add vector database-specific validation here
                pass
        except Exception as e:
            errors.append(f"Vector database validation failed: {e}")

        try:
            # Validate API configuration
            if (self.api.enabled and
                (self.api.port < MIN_PORT or self.api.port > MAX_PORT)):
                errors.append(f"API port must be between {MIN_PORT} and {MAX_PORT}")
        except Exception as e:
            errors.append(f"API validation failed: {e}")

        try:
            # Validate security configuration
            if (self.security.enable_auth and
                len(self.security.secret_key) < MIN_SECRET_KEY_LENGTH):
                errors.append(f"Secret key must be at least {MIN_SECRET_KEY_LENGTH} characters long")
        except Exception as e:
            errors.append(f"Security validation failed: {e}")

        return errors

    def get_environment_info(self) -> dict[str, Any]:
        """Get information about the current environment."""
        return {
            "python_version": os.sys.version,
            "platform": os.sys.platform,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "config_file": os.getenv("CONFIG_FILE", "Not specified"),
            "debug_mode": self.debug,
            "log_level": self.log_level
        }

    def get_feature_flags(self) -> dict[str, bool]:
        """Get current feature flags."""
        return {
            "openai_enabled": self.openai.enabled,
            "anthropic_enabled": self.anthropic.enabled,
            "ollama_enabled": self.ollama.enabled,
            "oss20b_enabled": self.oss20b.enabled,
            "vector_db_enabled": self.vector_db.enabled,
            "monitoring_enabled": self.monitoring.enabled,
            "auth_enabled": self.security.enable_auth,
            "api_enabled": self.api.enabled,
            "websocket_enabled": self.websocket.enabled,
            "background_tasks_enabled": self.background_tasks.enabled
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def reload_settings() -> Settings:
    """Reload settings and clear cache."""
    get_settings.cache_clear()
    return get_settings()


def create_default_config(file_path: str | Path = "config.json"):
    """Create a default configuration file."""
    settings = Settings()
    settings.save_to_file(file_path)
    return file_path


def validate_config_file(file_path: str | Path) -> list[str]:
    """Validate a configuration file and return list of errors."""
    try:
        settings = Settings.load_from_file(file_path)
        return settings.validate_all()
    except Exception as e:
        return [f"Configuration file validation failed: {e}"]


def get_config_summary() -> dict[str, Any]:
    """Get a summary of the current configuration."""
    settings = get_settings()

    return {
        "app_info": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "log_level": settings.log_level
        },
        "providers": {
            "enabled": settings.get_enabled_providers(),
            "total_configured": len([p for p in ["openai", "anthropic", "ollama", "oss20b"]
                                   if settings.get_provider_config(p)])
        },
        "features": settings.get_feature_flags(),
        "environment": settings.get_environment_info(),
        "validation_errors": settings.validate_all()
    }
