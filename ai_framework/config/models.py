"""
Configuration Models

This module provides Pydantic models for all configuration components:
- Database configuration
- LLM provider configurations
- Agent and memory settings
- API and security configurations
- Monitoring and caching settings
"""

from typing import Any

from pydantic import BaseModel, Field, validator
from pydantic.types import SecretStr

# Constants to replace magic numbers
MIN_PORT = 1
MAX_PORT = 65535
MIN_SECRET_KEY_LENGTH = 32
DEFAULT_POOL_SIZE = 10
DEFAULT_MAX_OVERFLOW = 20
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RATE_LIMIT = 100
DEFAULT_COST_LIMIT = 10.0


class DatabaseConfig(BaseModel):
    """Database configuration."""
    enabled: bool = Field(default=True, description="Enable database")
    type: str = Field(default="sqlite", description="Database type")
    host: str | None = Field(default=None, description="Database host")
    port: int | None = Field(default=None, description="Database port")
    username: str | None = Field(default=None, description="Database username")
    password: SecretStr | None = Field(default=None, description="Database password")
    database: str | None = Field(default=None, description="Database name")
    path: str | None = Field(default="ai_framework.db", description="Database file path")
    pool_size: int = Field(default=DEFAULT_POOL_SIZE, description="Connection pool size")
    max_overflow: int = Field(default=DEFAULT_MAX_OVERFLOW, description="Maximum overflow connections")
    echo: bool = Field(default=False, description="Echo SQL statements")

    @validator("type")
    def validate_database_type(cls, v):
        """Validate database type."""
        valid_types = ["sqlite", "postgresql", "mysql"]
        if v not in valid_types:
            raise ValueError(f"Database type must be one of: {valid_types}")
        return v


class ModelConfig(BaseModel):
    """Individual model configuration."""
    name: str = Field(description="Model name")
    enabled: bool = Field(default=True, description="Enable model")
    max_tokens: int = Field(default=4096, description="Maximum tokens")
    temperature: float = Field(default=0.7, description="Model temperature")
    top_p: float = Field(default=0.9, description="Top-p sampling")
    frequency_penalty: float = Field(default=0.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, description="Presence penalty")
    stop_sequences: list[str] = Field(default_factory=list, description="Stop sequences")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    enabled: bool = Field(default=False, description="Enable OpenAI")
    api_key: SecretStr | None = Field(default=None, description="OpenAI API key")
    organization: str | None = Field(default=None, description="OpenAI organization")
    base_url: str | None = Field(default=None, description="OpenAI base URL")
    models: list[ModelConfig] = Field(default_factory=list, description="Available models")
    rate_limit: int = Field(default=100, description="Rate limit per minute")
    cost_limit: float = Field(default=10.0, description="Cost limit per hour")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

    @validator("models", pre=True, always=True)
    def set_default_models(cls, v):
        """Set default models if none provided."""
        if not v:
            return [
                ModelConfig(name="gpt-4", max_tokens=8192),
                ModelConfig(name="gpt-4-turbo", max_tokens=128000),
                ModelConfig(name="gpt-3.5-turbo", max_tokens=4096)
            ]
        return v


class AnthropicConfig(BaseModel):
    """Anthropic configuration."""
    enabled: bool = Field(default=False, description="Enable Anthropic")
    api_key: SecretStr | None = Field(default=None, description="Anthropic API key")
    base_url: str | None = Field(default=None, description="Anthropic base URL")
    models: list[ModelConfig] = Field(default_factory=list, description="Available models")
    rate_limit: int = Field(default=30, description="Rate limit per minute")
    cost_limit: float = Field(default=10.0, description="Cost limit per hour")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

    @validator("models", pre=True, always=True)
    def set_default_models(cls, v):
        """Set default models if none provided."""
        if not v:
            return [
                ModelConfig(name="claude-3.5-sonnet-20241022", max_tokens=4096),
                ModelConfig(name="claude-3.5-haiku-20240307", max_tokens=4096)
            ]
        return v


class OllamaConfig(BaseModel):
    """Ollama configuration."""
    enabled: bool = Field(default=False, description="Enable Ollama")
    base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    models: list[ModelConfig] = Field(default_factory=list, description="Available models")
    rate_limit: int = Field(default=1000, description="Rate limit per minute")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    gpu_layers: int | None = Field(default=None, description="GPU layers to use")

    @validator("models", pre=True, always=True)
    def set_default_models(cls, v):
        """Set default models if none provided."""
        if not v:
            return [
                ModelConfig(name="llama3.1:8b", max_tokens=4096),
                ModelConfig(name="llama3.1:70b", max_tokens=8192),
                ModelConfig(name="codellama:13b", max_tokens=8192),
                ModelConfig(name="mistral:7b", max_tokens=4096)
            ]
        return v


class OSS20BConfig(BaseModel):
    """OSS-20B configuration."""
    enabled: bool = Field(default=False, description="Enable OSS-20B")
    model_path: str = Field(default="microsoft/DialoGPT-large", description="Model path")
    model_variant: str = Field(default="base", description="Model variant")
    quantization: str = Field(default="int4", description="Quantization level")
    max_memory: dict[str, str] | None = Field(default=None, description="Memory limits")
    device_map: str = Field(default="auto", description="Device mapping")
    torch_dtype: str = Field(default="auto", description="Torch data type")
    use_cache: bool = Field(default=True, description="Use model cache")
    low_cpu_mem_usage: bool = Field(default=True, description="Low CPU memory usage")
    trust_remote_code: bool = Field(default=True, description="Trust remote code")
    max_length: int = Field(default=2048, description="Maximum sequence length")
    temperature: float = Field(default=0.7, description="Model temperature")
    top_p: float = Field(default=0.9, description="Top-p sampling")
    top_k: int = Field(default=50, description="Top-k sampling")
    repetition_penalty: float = Field(default=1.1, description="Repetition penalty")
    do_sample: bool = Field(default=True, description="Enable sampling")

    @validator("quantization")
    def validate_quantization(cls, v):
        """Validate quantization level."""
        valid_levels = ["fp16", "int8", "int4", "nf4"]
        if v not in valid_levels:
            raise ValueError(f"Quantization must be one of: {valid_levels}")
        return v


class RoutingConfig(BaseModel):
    """Model routing configuration."""
    enabled: bool = Field(default=True, description="Enable intelligent routing")
    default_provider: str = Field(default="openai", description="Default provider")
    fallback_provider: str = Field(default="ollama", description="Fallback provider")
    routing_strategy: str = Field(default="performance", description="Routing strategy")
    cost_optimization: bool = Field(default=True, description="Enable cost optimization")
    performance_tracking: bool = Field(default=True, description="Track performance")
    ab_testing: bool = Field(default=False, description="Enable A/B testing")
    learning_enabled: bool = Field(default=True, description="Enable learning")
    routing_rules: dict[str, Any] = Field(default_factory=dict, description="Custom routing rules")

    @validator("routing_strategy")
    def validate_routing_strategy(cls, v):
        """Validate routing strategy."""
        valid_strategies = ["performance", "cost", "quality", "speed", "balanced"]
        if v not in valid_strategies:
            raise ValueError(f"Routing strategy must be one of: {valid_strategies}")
        return v


class AgentConfig(BaseModel):
    """Agent configuration."""
    enabled: bool = Field(default=True, description="Enable agents")
    max_concurrent_agents: int = Field(default=10, description="Maximum concurrent agents")
    agent_timeout: int = Field(default=300, description="Agent timeout in seconds")
    health_check_interval: int = Field(default=30, description="Health check interval")
    auto_cleanup: bool = Field(default=True, description="Auto cleanup inactive agents")
    agent_types: list[str] = Field(default_factory=list, description="Enabled agent types")

    @validator("agent_types", pre=True, always=True)
    def set_default_agent_types(cls, v):
        """Set default agent types if none provided."""
        if not v:
            return ["research", "analysis", "automation", "security", "content", "reporting"]
        return v


class MemoryConfig(BaseModel):
    """Memory configuration."""
    enabled: bool = Field(default=True, description="Enable memory management")
    max_memory_items: int = Field(default=10000, description="Maximum memory items")
    max_conversation_history: int = Field(default=1000, description="Maximum conversation history")
    context_window_size: int = Field(default=4096, description="Context window size")
    memory_compression_threshold: int = Field(default=1000, description="Compression threshold")
    cleanup_interval: int = Field(default=3600, description="Cleanup interval in seconds")
    memory_types: list[str] = Field(default_factory=list, description="Enabled memory types")

    @validator("memory_types", pre=True, always=True)
    def set_default_memory_types(cls, v):
        """Set default memory types if none provided."""
        if not v:
            return ["conversation", "entity", "fact", "relationship", "context", "semantic"]
        return v


class VectorDBConfig(BaseModel):
    """Vector database configuration."""
    enabled: bool = Field(default=False, description="Enable vector database")
    type: str = Field(default="chroma", description="Vector database type")
    host: str | None = Field(default=None, description="Vector database host")
    port: int | None = Field(default=None, description="Vector database port")
    username: str | None = Field(default=None, description="Vector database username")
    password: SecretStr | None = Field(default=None, description="Vector database password")
    database: str | None = Field(default=None, description="Vector database name")
    path: str | None = Field(default="vector_db", description="Vector database path")
    api_key: SecretStr | None = Field(default=None, description="API key for cloud services")
    collection_name: str = Field(default="ai_framework", description="Collection name")
    embedding_dimension: int = Field(default=1536, description="Embedding dimension")
    similarity_metric: str = Field(default="cosine", description="Similarity metric")

    @validator("type")
    def validate_vector_db_type(cls, v):
        """Validate vector database type."""
        valid_types = ["chroma", "pinecone", "weaviate"]
        if v not in valid_types:
            raise ValueError(f"Vector database type must be one of: {valid_types}")
        return v

    @validator("similarity_metric")
    def validate_similarity_metric(cls, v):
        """Validate similarity metric."""
        valid_metrics = ["cosine", "euclidean", "dot_product"]
        if v not in valid_metrics:
            raise ValueError(f"Similarity metric must be one of: {valid_metrics}")
        return v


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    enabled: bool = Field(default=True, description="Enable monitoring")
    metrics_collection: bool = Field(default=True, description="Collect metrics")
    health_checks: bool = Field(default=True, description="Enable health checks")
    performance_tracking: bool = Field(default=True, description="Track performance")
    cost_tracking: bool = Field(default=True, description="Track costs")
    alerting: bool = Field(default=False, description="Enable alerting")
    dashboard: bool = Field(default=True, description="Enable dashboard")
    retention_days: int = Field(default=30, description="Data retention in days")
    export_format: str = Field(default="json", description="Export format")

    @validator("export_format")
    def validate_export_format(cls, v):
        """Validate export format."""
        valid_formats = ["json", "csv", "prometheus"]
        if v not in valid_formats:
            raise ValueError(f"Export format must be one of: {valid_formats}")
        return v


class SecurityConfig(BaseModel):
    """Security configuration."""
    enabled: bool = Field(default=True, description="Enable security features")
    enable_auth: bool = Field(default=False, description="Enable authentication")
    secret_key: SecretStr | None = Field(default=None, description="Secret key")
    jwt_secret: SecretStr | None = Field(default=None, description="JWT secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration: int = Field(default=3600, description="JWT expiration in seconds")
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: list[str] = Field(default_factory=list, description="CORS origins")
    rate_limiting_enabled: bool = Field(default=True, description="Enable rate limiting")
    max_requests_per_minute: int = Field(default=100, description="Max requests per minute")
    encryption_enabled: bool = Field(default=False, description="Enable encryption")
    encryption_key: SecretStr | None = Field(default=None, description="Encryption key")

    @validator("jwt_algorithm")
    def validate_jwt_algorithm(cls, v):
        """Validate JWT algorithm."""
        valid_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in valid_algorithms:
            raise ValueError(f"JWT algorithm must be one of: {valid_algorithms}")
        return v


class APIConfig(BaseModel):
    """API configuration."""
    enabled: bool = Field(default=True, description="Enable API")
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    workers: int = Field(default=4, description="Number of workers")
    timeout: int = Field(default=30, description="Request timeout")
    max_request_size: int = Field(default=10485760, description="Max request size in bytes")
    enable_docs: bool = Field(default=True, description="Enable API documentation")
    enable_redoc: bool = Field(default=True, description="Enable ReDoc")
    cors_origins: list[str] = Field(default_factory=list, description="CORS origins")
    rate_limit: int = Field(default=100, description="Rate limit per minute")

    @validator("port")
    def validate_port(cls, v):
        """Validate port number."""
        if v < MIN_PORT or v > MAX_PORT:
            raise ValueError(f"Port must be between {MIN_PORT} and {MAX_PORT}")
        return v


class WebSocketConfig(BaseModel):
    """WebSocket configuration."""
    enabled: bool = Field(default=False, description="Enable WebSocket")
    host: str = Field(default="0.0.0.0", description="WebSocket host")
    port: int = Field(default=8001, description="WebSocket port")
    max_connections: int = Field(default=1000, description="Maximum connections")
    ping_interval: int = Field(default=30, description="Ping interval in seconds")
    ping_timeout: int = Field(default=10, description="Ping timeout in seconds")
    close_timeout: int = Field(default=10, description="Close timeout in seconds")
    max_message_size: int = Field(default=1048576, description="Max message size in bytes")

    @validator("port")
    def validate_port(cls, v):
        """Validate port number."""
        if v < MIN_PORT or v > MAX_PORT:
            raise ValueError(f"Port must be between {MIN_PORT} and {MAX_PORT}")
        return v


class BackgroundTaskConfig(BaseModel):
    """Background task configuration."""
    enabled: bool = Field(default=True, description="Enable background tasks")
    max_workers: int = Field(default=10, description="Maximum worker threads")
    task_timeout: int = Field(default=300, description="Task timeout in seconds")
    max_queue_size: int = Field(default=1000, description="Maximum queue size")
    retry_attempts: int = Field(default=3, description="Retry attempts")
    retry_delay: int = Field(default=5, description="Retry delay in seconds")
    cleanup_interval: int = Field(default=3600, description="Cleanup interval in seconds")
    enable_monitoring: bool = Field(default=True, description="Enable task monitoring")


class RateLimitingConfig(BaseModel):
    """Rate limiting configuration."""
    enabled: bool = Field(default=True, description="Enable rate limiting")
    default_limit: int = Field(default=100, description="Default requests per minute")
    burst_limit: int = Field(default=200, description="Burst limit")
    storage_backend: str = Field(default="memory", description="Storage backend")
    redis_url: str | None = Field(default=None, description="Redis URL")
    enable_headers: bool = Field(default=True, description="Enable rate limit headers")
    retry_after_header: bool = Field(default=True, description="Enable retry-after header")

    @validator("storage_backend")
    def validate_storage_backend(cls, v):
        """Validate storage backend."""
        valid_backends = ["memory", "redis"]
        if v not in valid_backends:
            raise ValueError(f"Storage backend must be one of: {valid_backends}")
        return v


class CachingConfig(BaseModel):
    """Caching configuration."""
    enabled: bool = Field(default=True, description="Enable caching")
    backend: str = Field(default="memory", description="Cache backend")
    redis_url: str | None = Field(default=None, description="Redis URL")
    default_ttl: int = Field(default=3600, description="Default TTL in seconds")
    max_size: int = Field(default=1000, description="Maximum cache size")
    enable_compression: bool = Field(default=False, description="Enable compression")
    compression_threshold: int = Field(default=1024, description="Compression threshold")
    enable_stats: bool = Field(default=True, description="Enable cache statistics")

    @validator("backend")
    def validate_cache_backend(cls, v):
        """Validate cache backend."""
        valid_backends = ["memory", "redis"]
        if v not in valid_backends:
            raise ValueError(f"Cache backend must be one of: {valid_backends}")
        return v


class StorageConfig(BaseModel):
    """File storage configuration."""
    enabled: bool = Field(default=False, description="Enable file storage")
    backend: str = Field(default="local", description="Storage backend")
    local_path: str | None = Field(default=None, description="Local storage path")
    s3_bucket: str | None = Field(default=None, description="S3 bucket name")
    s3_access_key: SecretStr | None = Field(default=None, description="S3 access key")
    s3_secret_key: SecretStr | None = Field(default=None, description="S3 secret key")
    s3_region: str | None = Field(default=None, description="S3 region")
    s3_endpoint: str | None = Field(default=None, description="S3 endpoint")
    max_file_size: int = Field(default=104857600, description="Max file size in bytes")
    allowed_extensions: list[str] = Field(default_factory=list, description="Allowed file extensions")
    enable_compression: bool = Field(default=False, description="Enable file compression")

    @validator("backend")
    def validate_storage_backend(cls, v):
        """Validate storage backend."""
        valid_backends = ["local", "s3", "gcs", "azure"]
        if v not in valid_backends:
            raise ValueError(f"Storage backend must be one of: {valid_backends}")
        return v

    @validator("allowed_extensions", pre=True, always=True)
    def set_default_extensions(cls, v):
        """Set default allowed extensions if none provided."""
        if not v:
            return [".txt", ".json", ".csv", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"]
        return v


class ExternalServicesConfig(BaseModel):
    """External services configuration."""
    enabled: bool = Field(default=False, description="Enable external services")
    services: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Service configurations")
    timeout: int = Field(default=30, description="Default timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: int = Field(default=1, description="Retry delay in seconds")
    enable_circuit_breaker: bool = Field(default=True, description="Enable circuit breaker")
    circuit_breaker_threshold: int = Field(default=5, description="Circuit breaker threshold")
    circuit_breaker_timeout: int = Field(default=60, description="Circuit breaker timeout")

    def get_service_config(self, service_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific service."""
        return self.services.get(service_name)

    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled."""
        service_config = self.get_service_config(service_name)
        return service_config is not None and service_config.get("enabled", False)


# Configuration validation functions
def validate_provider_config(provider: str, config: dict[str, Any]) -> list[str]:
    """Validate provider configuration."""
    errors = []

    if provider == "openai" and config.get("enabled") and not config.get("api_key"):
        errors.append("OpenAI API key is required when enabled")

    elif provider == "anthropic" and config.get("enabled") and not config.get("api_key"):
        errors.append("Anthropic API key is required when enabled")

    elif provider == "ollama" and config.get("enabled") and not config.get("base_url"):
        errors.append("Ollama base URL is required when enabled")

    elif provider == "oss20b" and config.get("enabled") and not config.get("model_path"):
        errors.append("OSS-20B model path is required when enabled")

    return errors


def validate_database_config(config: dict[str, Any]) -> list[str]:
    """Validate database configuration."""
    errors = []

    if config.get("enabled"):
        db_type = config.get("type", "sqlite")

        if db_type in ["postgresql", "mysql"]:
            required_fields = ["host", "port", "username", "password", "database"]
            for field in required_fields:
                if not config.get(field):
                    errors.append(f"{field} is required for {db_type}")

        elif db_type == "sqlite":
            if not config.get("path"):
                errors.append("Path is required for SQLite")

    return errors


def validate_vector_db_config(config: dict[str, Any]) -> list[str]:
    """Validate vector database configuration."""
    errors = []

    if config.get("enabled"):
        db_type = config.get("type", "chroma")

        if db_type in ["pinecone", "weaviate"]:
            if not config.get("api_key"):
                errors.append(f"API key is required for {db_type}")

            if not config.get("host"):
                errors.append(f"Host is required for {db_type}")

    return errors


def validate_security_config(config: dict[str, Any]) -> list[str]:
    """Validate security configuration."""
    errors = []

    if config.get("enable_auth"):
        if not config.get("secret_key"):
            errors.append("Secret key is required when authentication is enabled")

        if config.get("secret_key") and len(str(config["secret_key"])) < MIN_SECRET_KEY_LENGTH:
            errors.append(f"Secret key must be at least {MIN_SECRET_KEY_LENGTH} characters long")

    return errors


def validate_api_config(config: dict[str, Any]) -> list[str]:
    """Validate API configuration."""
    errors = []

    if config.get("enabled"):
        port = config.get("port", 8000)
        if port < MIN_PORT or port > MAX_PORT:
            errors.append(f"API port must be between {MIN_PORT} and {MAX_PORT}")

    return errors
