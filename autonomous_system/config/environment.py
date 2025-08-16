"""
Environment Configuration Manager
Production-ready configuration with environment-specific settings
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseSettings, Field

# Load environment variables
load_dotenv()

class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    type: str = Field(default="sqlite", description="Database type: sqlite, postgresql, mysql")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="autonomous_system", description="Database name")
    user: str = Field(default="autonomous_user", description="Database user")
    password: str = Field(default="", description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")

    class Config:
        env_prefix = "DB_"

class SecuritySettings(BaseSettings):
    """Security configuration settings"""
    jwt_secret: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiry: int = Field(default=3600, description="JWT expiry in seconds")
    refresh_token_expiry: int = Field(default=86400, description="Refresh token expiry in seconds")
    password_min_length: int = Field(default=12, description="Minimum password length")
    password_complexity: bool = Field(default=True, description="Enable password complexity")
    max_login_attempts: int = Field(default=5, description="Max failed login attempts")
    lockout_duration: int = Field(default=900, description="Account lockout duration in seconds")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")

    class Config:
        env_prefix = "SECURITY_"

class AISettings(BaseSettings):
    """AI model configuration settings"""
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_organization: str = Field(default="", description="OpenAI organization")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    default_model: str = Field(default="gpt-4", description="Default AI model")
    max_tokens: int = Field(default=4000, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="AI model temperature")

    class Config:
        env_prefix = "AI_"

class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings"""
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")
    grafana_enabled: bool = Field(default=True, description="Enable Grafana dashboards")
    grafana_port: int = Field(default=3000, description="Grafana port")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json, text")
    log_file: str = Field(default="/app/logs/autonomous_system.log", description="Log file path")
    max_log_size: str = Field(default="100MB", description="Maximum log file size")
    log_backup_count: int = Field(default=5, description="Number of log backups")

    class Config:
        env_prefix = "MONITORING_"

class PerformanceSettings(BaseSettings):
    """Performance and optimization settings"""
    max_concurrent_tasks: int = Field(default=10, description="Maximum concurrent tasks")
    task_timeout: int = Field(default=3600, description="Task timeout in seconds")
    worker_processes: int = Field(default=4, description="Number of worker processes")
    memory_limit: str = Field(default="2GB", description="Memory limit per task")
    cpu_limit: float = Field(default=1.0, description="CPU limit per task")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    class Config:
        env_prefix = "PERFORMANCE_"

class SystemSettings(BaseSettings):
    """System configuration settings"""
    name: str = Field(default="Autonomous Task Solver", description="System name")
    version: str = Field(default="1.0.0", description="System version")
    environment: str = Field(default="production", description="Environment: dev, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")
    data_path: str = Field(default="/app/data", description="Data storage path")
    logs_path: str = Field(default="/app/logs", description="Logs storage path")
    config_path: str = Field(default="/app/config", description="Configuration path")
    temp_path: str = Field(default="/tmp", description="Temporary files path")

    class Config:
        env_prefix = "SYSTEM_"

class EnvironmentConfig:
    """Main environment configuration manager"""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config_data = self._load_config()

        # Initialize settings
        self.database = DatabaseSettings(**self.config_data.get("database", {}))
        self.security = SecuritySettings(**self.config_data.get("security", {}))
        self.ai = AISettings(**self.config_data.get("ai", {}))
        self.monitoring = MonitoringSettings(**self.config_data.get("monitoring", {}))
        self.performance = PerformanceSettings(**self.config_data.get("performance", {}))
        self.system = SystemSettings(**self.config_data.get("system", {}))

        # Validate configuration
        self._validate_config()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Check multiple possible locations
        possible_paths = [
            "config/config.yaml",
            "autonomous_system/config/config.yaml",
            "/app/config/config.yaml",
            os.path.expanduser("~/.autonomous_system/config.yaml"),
            "/etc/autonomous_system/config.yaml"
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path

        # Return default path
        return "config/config.yaml"

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file and environment"""
        config = {}

        # Load from YAML file if it exists
        if Path(self.config_path).exists():
            try:
                with open(self.config_path) as f:
                    config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_path}: {e}")

        # Override with environment variables
        config.update(self._load_env_config())

        return config

    def _load_env_config(self) -> dict[str, Any]:
        """Load configuration from environment variables"""
        config = {}

        # Database
        if os.getenv("DB_TYPE"):
            config.setdefault("database", {})
            config["database"]["type"] = os.getenv("DB_TYPE")
        if os.getenv("DB_HOST"):
            config.setdefault("database", {})
            config["database"]["host"] = os.getenv("DB_HOST")
        if os.getenv("DB_PORT"):
            config.setdefault("database", {})
            config["database"]["port"] = int(os.getenv("DB_PORT"))

        # Security
        if os.getenv("SECURITY_JWT_SECRET"):
            config.setdefault("security", {})
            config["security"]["jwt_secret"] = os.getenv("SECURITY_JWT_SECRET")

        # AI
        if os.getenv("AI_OPENAI_API_KEY"):
            config.setdefault("ai", {})
            config["ai"]["openai_api_key"] = os.getenv("AI_OPENAI_API_KEY")
        if os.getenv("AI_ANTHROPIC_API_KEY"):
            config.setdefault("ai", {})
            config["ai"]["anthropic_api_key"] = os.getenv("AI_ANTHROPIC_API_KEY")

        # System
        if os.getenv("SYSTEM_ENVIRONMENT"):
            config.setdefault("system", {})
            config["system"]["environment"] = os.getenv("SYSTEM_ENVIRONMENT")
        if os.getenv("SYSTEM_DEBUG"):
            config.setdefault("system", {})
            config["system"]["debug"] = os.getenv("SYSTEM_DEBUG").lower() == "true"

        return config

    def _validate_config(self):
        """Validate configuration settings"""
        # Check required settings for production
        if self.system.environment == "production":
            if not self.security.jwt_secret:
                raise ValueError("JWT secret is required in production")
            if self.security.jwt_secret == "your-secret-key-here":
                raise ValueError("Default JWT secret cannot be used in production")
            if self.system.debug:
                raise ValueError("Debug mode cannot be enabled in production")

        # Validate database settings
        if self.database.type == "postgresql":
            if not self.database.password:
                raise ValueError("Database password is required for PostgreSQL")

        # Validate AI settings
        if not any([self.ai.openai_api_key, self.ai.anthropic_api_key]):
            print("Warning: No AI API keys configured")

    def get_database_url(self) -> str:
        """Get database connection URL"""
        if self.database.type == "sqlite":
            return f"sqlite:///{self.database.name}.db"
        elif self.database.type == "postgresql":
            return f"postgresql://{self.database.user}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.name}"
        elif self.database.type == "mysql":
            return f"mysql://{self.database.user}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.name}"
        else:
            raise ValueError(f"Unsupported database type: {self.database.type}")

    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_password = os.getenv("REDIS_PASSWORD", "")

        if redis_password:
            return f"redis://:{redis_password}@{redis_host}:{redis_port}"
        else:
            return f"redis://{redis_host}:{redis_port}"

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "database": self.database.dict(),
            "security": self.security.dict(),
            "ai": self.ai.dict(),
            "monitoring": self.monitoring.dict(),
            "performance": self.performance.dict(),
            "system": self.system.dict()
        }

    def save_config(self, path: str | None = None):
        """Save configuration to file"""
        save_path = path or self.config_path

        # Ensure directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        # Save configuration
        with open(save_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)

    def reload_config(self):
        """Reload configuration from file"""
        self.config_data = self._load_config()

        # Reinitialize settings
        self.database = DatabaseSettings(**self.config_data.get("database", {}))
        self.security = SecuritySettings(**self.config_data.get("security", {}))
        self.ai = AISettings(**self.config_data.get("ai", {}))
        self.monitoring = MonitoringSettings(**self.config_data.get("monitoring", {}))
        self.performance = PerformanceSettings(**self.config_data.get("performance", {}))
        self.system = SystemSettings(**self.config_data.get("system", {}))

        # Revalidate
        self._validate_config()

# Global configuration instance
config = EnvironmentConfig()

# Convenience functions
def get_config() -> EnvironmentConfig:
    """Get global configuration instance"""
    return config

def get_database_settings() -> DatabaseSettings:
    """Get database settings"""
    return config.database

def get_security_settings() -> SecuritySettings:
    """Get security settings"""
    return config.security

def get_ai_settings() -> AISettings:
    """Get AI settings"""
    return config.ai

def get_monitoring_settings() -> MonitoringSettings:
    """Get monitoring settings"""
    return config.monitoring

def get_performance_settings() -> PerformanceSettings:
    """Get performance settings"""
    return config.performance

def get_system_settings() -> SystemSettings:
    """Get system settings"""
    return config.system

# Example usage
if __name__ == "__main__":
    # Print current configuration
    print("Current Configuration:")
    print("=====================")

    print(f"System: {config.system.name} v{config.system.version}")
    print(f"Environment: {config.system.environment}")
    print(f"Debug: {config.system.debug}")

    print(f"\nDatabase: {config.database.type} on {config.database.host}:{config.database.port}")
    print(f"Security: JWT expiry {config.security.jwt_expiry}s, Rate limit {config.security.rate_limit_requests}/min")
    print(f"AI: Default model {config.ai.default_model}")
    print(f"Monitoring: Log level {config.monitoring.log_level}")
    print(f"Performance: Max concurrent tasks {config.performance.max_concurrent_tasks}")

    # Save configuration
    config.save_config("config_generated.yaml")
    print("\nConfiguration saved to config_generated.yaml")
