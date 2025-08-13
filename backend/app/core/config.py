import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env for local/dev only. Never load .env in production.
def _is_production() -> bool:
    return os.getenv("ENV", "").lower() in {"production", "prod"}

if not _is_production():  # pragma: no cover - convenience for local dev
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        # Dotenv is optional in dev
        pass


class Settings(BaseSettings):
    # In pydantic v2, allow extra keys; do not rely on env_file (we preload via dotenv in dev)
    model_config = SettingsConfigDict(extra="ignore")
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
    RESEARCH_ENABLED: bool = Field(default=False, env="RESEARCH_ENABLED")
    RESEARCH_CACHE_TTL_S: int = Field(default=900, env="RESEARCH_CACHE_TTL_S")
    RESEARCH_CACHE_MAX_ITEMS: int = Field(default=512, env="RESEARCH_CACHE_MAX_ITEMS")
    RESEARCH_SEARCH_QPS: float = Field(default=2.0, env="RESEARCH_SEARCH_QPS")
    RESEARCH_FETCH_RPS: float = Field(default=2.0, env="RESEARCH_FETCH_RPS")
    RESEARCH_FETCH_TIMEOUT_S: int = Field(default=6, env="RESEARCH_FETCH_TIMEOUT_S")
    RESEARCH_FETCH_MAX_BYTES: int = Field(default=2_000_000, env="RESEARCH_FETCH_MAX_BYTES")
    # Aliases for alternative env variable names
    RESEARCH_CACHE_TTL_SECONDS: int = Field(default=3600, env="RESEARCH_CACHE_TTL_SECONDS")
    RESEARCH_TOKENS_PER_SECOND: float = Field(default=2.0, env="RESEARCH_TOKENS_PER_SECOND")
    RESEARCH_BURST: int = Field(default=5, env="RESEARCH_BURST")
    RESEARCH_OFFLINE_FIXTURES_DIR: str = Field(
        default="tools/web_research/fixtures", env="RESEARCH_OFFLINE_FIXTURES_DIR"
    )

    # LLM routing (local-first defaults)
    LLM_PRIMARY: str = Field(
        default="lmstudio", env="LLM_PRIMARY"
    )  # lmstudio|ollama|vllm|openai|anthropic
    LLM_FALLBACK: str = Field(default="none", env="LLM_FALLBACK")  # none|ollama|openai|anthropic
    OPENAI_API_KEY: str | None = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    ANTHROPIC_API_KEY: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-latest", env="ANTHROPIC_MODEL")
    OLLAMA_HOST: str = Field(default="http://127.0.0.1:11434", env="OLLAMA_HOST")
    OLLAMA_MODEL: str = Field(default="llama3.1:8b", env="OLLAMA_MODEL")
    LMSTUDIO_BASE_URL: str = Field(default="http://127.0.0.1:1234/v1", env="LMSTUDIO_BASE_URL")
    LMSTUDIO_MODEL: str = Field(default="local-model", env="LMSTUDIO_MODEL")
    VLLM_BASE_URL: str = Field(default="http://127.0.0.1:8001/v1", env="VLLM_BASE_URL")
    VLLM_MODEL: str = Field(default="local-model", env="VLLM_MODEL")
    LLM_POLICY: str = Field(default="70b, 405b, 8x7b, 8x22b, 405m, 8b", env="LLM_POLICY")
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

    # Integrations / OAuth
    GOOGLE_CLIENT_ID: str | None = Field(default=None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    GOOGLE_CALENDAR_SYNC: bool = Field(default=False, env="GOOGLE_CALENDAR_SYNC")
    INTEGRATION_VAULT_KEY: str | None = Field(default=None, env="INTEGRATION_VAULT_KEY")

    # Automation feature flags
    AUTOMATION_ENGINE_ENABLED: bool = Field(default=False, env="AUTOMATION_ENGINE_ENABLED")
    AUTOMATION_LEARNING_ENABLED: bool = Field(default=False, env="AUTOMATION_LEARNING_ENABLED")
    AUTOMATION_SUGGESTIONS_ENABLED: bool = Field(default=False, env="AUTOMATION_SUGGESTIONS_ENABLED")

    # Webhook/DLQ/Retry config
    WEBHOOK_BASE_URL: str = Field(default="http://localhost:8000", env="WEBHOOK_BASE_URL")
    WEBHOOK_SECRET: str | None = Field(default=None, env="GMAIL_WEBHOOK_SECRET")
    DLQ_MAX_ITEMS_PER_QUEUE: int = Field(default=1000, env="DLQ_MAX_ITEMS_PER_QUEUE")
    DLQ_RETENTION_DAYS: int = Field(default=7, env="DLQ_RETENTION_DAYS")
    DLQ_ALERT_THRESHOLD: int = Field(default=100, env="DLQ_ALERT_THRESHOLD")
    DLQ_AUTO_RETRY_ENABLED: bool = Field(default=True, env="DLQ_AUTO_RETRY_ENABLED")
    DLQ_AUTO_RETRY_MAX_ATTEMPTS: int = Field(default=3, env="DLQ_AUTO_RETRY_MAX_ATTEMPTS")
    GOOGLE_API_MAX_RETRIES: int = Field(default=3, env="GOOGLE_API_MAX_RETRIES")
    GOOGLE_API_BACKOFF_MULTIPLIER: float = Field(default=2.0, env="GOOGLE_API_BACKOFF_MULTIPLIER")
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = Field(default=30, env="CIRCUIT_BREAKER_RECOVERY_TIMEOUT")

    # Operator System feature flags and tuning
    OPERATOR_WEB_ENABLED: bool = Field(default=False, env="OPERATOR_WEB_ENABLED")
    OPERATOR_DESKTOP_ENABLED: bool = Field(default=False, env="OPERATOR_DESKTOP_ENABLED")
    OPERATOR_MAX_CONCURRENT_TASKS: int = Field(default=3, env="OPERATOR_MAX_CONCURRENT_TASKS")
    OPERATOR_TASK_TIMEOUT_S: int = Field(default=3600, env="OPERATOR_TASK_TIMEOUT")
    OPERATOR_MONITORING_ENABLED: bool = Field(default=True, env="OPERATOR_MONITORING_ENABLED")
    OPERATOR_WEB_REAL: bool = Field(default=False, env="OPERATOR_WEB_REAL")
    OPERATOR_AI_ENABLED: bool = Field(default=False, env="OPERATOR_AI_ENABLED")
    OPERATOR_ALLOWED_DOMAINS: str = Field(default="*", env="OPERATOR_ALLOWED_DOMAINS")
    ROI_HOURLY_RATE_USD: float = Field(default=50.0, env="ROI_HOURLY_RATE_USD")
    ROI_SUCCESS_RATE_THRESHOLD: float = Field(default=0.8, env="ROI_SUCCESS_RATE_THRESHOLD")

    # Observability / Grafana (optional)
    GRAFANA_BASE_URL: str | None = Field(default=None, env="GRAFANA_BASE_URL")
    GRAFANA_DASHBOARD_UID: str | None = Field(default=None, env="GRAFANA_DASHBOARD_UID")

    # Stripe (optional)
    STRIPE_SECRET_KEY: str | None = Field(default=None, env="STRIPE_SECRET_KEY")

    # System event bus consumer
    SYSTEM_EVENT_CONSUMER_ENABLED: bool = Field(default=False, env="SYSTEM_EVENT_CONSUMER_ENABLED")
    EVENT_BUS_CONSUMER_GROUP: str = Field(default="system:cg", env="EVENT_BUS_CONSUMER_GROUP")
    EVENT_BUS_CONSUMER_NAME: str = Field(default="api-1", env="EVENT_BUS_CONSUMER_NAME")
    EVENT_PROCESSED_CAP: int = Field(default=10000, env="EVENT_PROCESSED_CAP")

    # Note: Pydantic v2 uses model_config; do not also define class Config


def get_settings() -> Settings:
    return Settings()
