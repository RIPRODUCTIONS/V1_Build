from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # In pydantic v2, allow extra keys in env/.env to avoid validation errors
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    jwt_secret: str = Field(default="change-me", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    admin_username: str = Field(default="admin", env="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", env="ADMIN_PASSWORD")

    ci_env: bool = Field(default=False, env="CI_ENV")
    ci_cleanup_token: str | None = Field(default=None, env="CI_CLEANUP_TOKEN")
    sentry_dsn: str | None = Field(default=None, env="SENTRY_DSN")

    s3_endpoint_url: str | None = Field(default=None, env="S3_ENDPOINT_URL")
    s3_access_key: str | None = Field(default=None, env="S3_ACCESS_KEY")
    s3_secret_key: str | None = Field(default=None, env="S3_SECRET_KEY")
    s3_bucket: str | None = Field(default="artifacts", env="S3_BUCKET")

    # Feature flags
    PROTOTYPE_BUILDER_ENABLED: bool = Field(default=True, env="PROTOTYPE_BUILDER_ENABLED")

    # LLM routing (local-first defaults)
    LLM_PRIMARY: str = Field(
        default="ollama", env="LLM_PRIMARY"
    )  # ollama|lmstudio|vllm|openai|anthropic
    LLM_FALLBACK: str = Field(default="none", env="LLM_FALLBACK")  # none|ollama|openai|anthropic
    OPENAI_API_KEY: str | None = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    ANTHROPIC_API_KEY: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-latest", env="ANTHROPIC_MODEL")
    OLLAMA_HOST: str = Field(default="http://127.0.0.1:11434", env="OLLAMA_HOST")
    OLLAMA_MODEL: str = Field(default="llama3.1:8b", env="OLLAMA_MODEL")
    LLM_TIMEOUT_S: float = Field(default=10.0, env="LLM_TIMEOUT_S")
    LLM_RETRIES: int = Field(default=0, env="LLM_RETRIES")
    LLM_CB_FAIL_THRESHOLD: int = Field(default=3, env="LLM_CB_FAIL_THRESHOLD")
    LLM_CB_RESET_S: float = Field(default=30.0, env="LLM_CB_RESET_S")

    # Caching/Queue
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Celery queues for automation
    CELERY_BROKER_URL: str = Field(default="redis://127.0.0.1:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://127.0.0.1:6379/2", env="CELERY_RESULT_BACKEND"
    )

    # Note: Pydantic v2 uses model_config; do not also define class Config


def get_settings() -> Settings:
    return Settings()
