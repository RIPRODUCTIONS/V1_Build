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
    jwt_secret: str = Field(default="change-me", validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", validation_alias="ADMIN_PASSWORD")
    admin_email: str | None = Field(default=None, validation_alias="ADMIN_EMAIL")

    ci_env: bool = Field(default=False, validation_alias="CI_ENV")
    ci_cleanup_token: str | None = Field(default=None, validation_alias="CI_CLEANUP_TOKEN")
    sentry_dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")
    alert_webhook_url: str | None = Field(default=None, validation_alias="ALERT_WEBHOOK_URL")
    slack_webhook_url: str | None = Field(default=None, validation_alias="SLACK_WEBHOOK_URL")
    email_smtp_host: str | None = Field(default=None, validation_alias="EMAIL_SMTP_HOST")
    email_smtp_port: int | None = Field(default=587, validation_alias="EMAIL_SMTP_PORT")
    email_username: str | None = Field(default=None, validation_alias="EMAIL_USERNAME")
    email_password: str | None = Field(default=None, validation_alias="EMAIL_PASSWORD")
    email_from: str | None = Field(default=None, validation_alias="EMAIL_FROM")
    email_to: str | None = Field(default=None, validation_alias="EMAIL_TO")

    s3_endpoint_url: str | None = Field(default=None, validation_alias="S3_ENDPOINT_URL")
    s3_access_key: str | None = Field(default=None, validation_alias="S3_ACCESS_KEY")
    s3_secret_key: str | None = Field(default=None, validation_alias="S3_SECRET_KEY")
    s3_bucket: str | None = Field(default="artifacts", validation_alias="S3_BUCKET")

    # Feature flags
    PROTOTYPE_BUILDER_ENABLED: bool = Field(default=True, validation_alias="PROTOTYPE_BUILDER_ENABLED")
    RESEARCH_ENABLED: bool = Field(default=False, validation_alias="RESEARCH_ENABLED")
    RESEARCH_CACHE_TTL_S: int = Field(default=900, validation_alias="RESEARCH_CACHE_TTL_S")
    RESEARCH_CACHE_MAX_ITEMS: int = Field(default=512, validation_alias="RESEARCH_CACHE_MAX_ITEMS")
    RESEARCH_SEARCH_QPS: float = Field(default=2.0, validation_alias="RESEARCH_SEARCH_QPS")
    RESEARCH_FETCH_RPS: float = Field(default=2.0, validation_alias="RESEARCH_FETCH_RPS")
    RESEARCH_FETCH_TIMEOUT_S: int = Field(default=6, validation_alias="RESEARCH_FETCH_TIMEOUT_S")
    RESEARCH_FETCH_MAX_BYTES: int = Field(default=2_000_000, validation_alias="RESEARCH_FETCH_MAX_BYTES")
    # Aliases for alternative env variable names
    RESEARCH_CACHE_TTL_SECONDS: int = Field(default=3600, validation_alias="RESEARCH_CACHE_TTL_SECONDS")
    RESEARCH_TOKENS_PER_SECOND: float = Field(default=2.0, validation_alias="RESEARCH_TOKENS_PER_SECOND")
    RESEARCH_BURST: int = Field(default=5, validation_alias="RESEARCH_BURST")
    RESEARCH_OFFLINE_FIXTURES_DIR: str = Field(
        default="tools/web_research/fixtures", validation_alias="RESEARCH_OFFLINE_FIXTURES_DIR"
    )

    # LLM routing (local-first defaults)
    LLM_PRIMARY: str = Field(
        default="lmstudio", validation_alias="LLM_PRIMARY"
    )  # lmstudio|ollama|vllm|openai|anthropic
    LLM_FALLBACK: str = Field(default="none", validation_alias="LLM_FALLBACK")  # none|ollama|openai|anthropic
    OPENAI_API_KEY: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    ANTHROPIC_API_KEY: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-latest", validation_alias="ANTHROPIC_MODEL")
    OLLAMA_HOST: str = Field(default="http://127.0.0.1:11434", validation_alias="OLLAMA_HOST")
    OLLAMA_MODEL: str = Field(default="llama3.1:8b", validation_alias="OLLAMA_MODEL")
    LMSTUDIO_BASE_URL: str = Field(default="http://127.0.0.1:1234/v1", validation_alias="LMSTUDIO_BASE_URL")
    LMSTUDIO_MODEL: str = Field(default="local-model", validation_alias="LMSTUDIO_MODEL")
    VLLM_BASE_URL: str = Field(default="http://127.0.0.1:8001/v1", validation_alias="VLLM_BASE_URL")
    VLLM_MODEL: str = Field(default="local-model", validation_alias="VLLM_MODEL")
    LLM_POLICY: str = Field(default="70b, 405b, 8x7b, 8x22b, 405m, 8b", validation_alias="LLM_POLICY")
    LLM_TIMEOUT_S: float = Field(default=10.0, validation_alias="LLM_TIMEOUT_S")
    LLM_RETRIES: int = Field(default=0, validation_alias="LLM_RETRIES")
    LLM_CB_FAIL_THRESHOLD: int = Field(default=3, validation_alias="LLM_CB_FAIL_THRESHOLD")
    LLM_CB_RESET_S: float = Field(default=30.0, validation_alias="LLM_CB_RESET_S")

    # Caching/Queue
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # Celery queues for automation
    CELERY_BROKER_URL: str = Field(default="redis://127.0.0.1:6379/1", validation_alias="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://127.0.0.1:6379/2", validation_alias="CELERY_RESULT_BACKEND"
    )

    # Integrations / OAuth
    GOOGLE_CLIENT_ID: str | None = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = Field(default=None, validation_alias="GOOGLE_CLIENT_SECRET")
    GOOGLE_CALENDAR_SYNC: bool = Field(default=False, validation_alias="GOOGLE_CALENDAR_SYNC")
    INTEGRATION_VAULT_KEY: str | None = Field(default=None, validation_alias="INTEGRATION_VAULT_KEY")

    # Additional optional integrations to satisfy references across the codebase
    OP_CLI: str | None = Field(default=None, validation_alias="OP_CLI")
    NOTION_TOKEN: str | None = Field(default=None, validation_alias="NOTION_TOKEN")
    NOTION_DB_PROMPTS: str | None = Field(default=None, validation_alias="NOTION_DB_PROMPTS")
    NOTION_DB_VAULT: str | None = Field(default=None, validation_alias="NOTION_DB_VAULT")
    NOTION_DB_RUNS: str | None = Field(default=None, validation_alias="NOTION_DB_RUNS")
    GOOGLE_MAPS_API_KEY: str | None = Field(default=None, validation_alias="GOOGLE_MAPS_API_KEY")

    # Automation feature flags
    AUTOMATION_ENGINE_ENABLED: bool = Field(default=False, validation_alias="AUTOMATION_ENGINE_ENABLED")
    AUTOMATION_LEARNING_ENABLED: bool = Field(default=False, validation_alias="AUTOMATION_LEARNING_ENABLED")
    AUTOMATION_SUGGESTIONS_ENABLED: bool = Field(default=False, validation_alias="AUTOMATION_SUGGESTIONS_ENABLED")

    # Webhook/DLQ/Retry config
    WEBHOOK_BASE_URL: str = Field(default="http://localhost:8000", validation_alias="WEBHOOK_BASE_URL")
    WEBHOOK_SECRET: str | None = Field(default=None, validation_alias="GMAIL_WEBHOOK_SECRET")
    DLQ_MAX_ITEMS_PER_QUEUE: int = Field(default=1000, validation_alias="DLQ_MAX_ITEMS_PER_QUEUE")
    DLQ_RETENTION_DAYS: int = Field(default=7, validation_alias="DLQ_RETENTION_DAYS")
    DLQ_ALERT_THRESHOLD: int = Field(default=100, validation_alias="DLQ_ALERT_THRESHOLD")
    DLQ_AUTO_RETRY_ENABLED: bool = Field(default=True, validation_alias="DLQ_AUTO_RETRY_ENABLED")
    DLQ_AUTO_RETRY_MAX_ATTEMPTS: int = Field(default=3, validation_alias="DLQ_AUTO_RETRY_MAX_ATTEMPTS")
    GOOGLE_API_MAX_RETRIES: int = Field(default=3, validation_alias="GOOGLE_API_MAX_RETRIES")
    GOOGLE_API_BACKOFF_MULTIPLIER: float = Field(default=2.0, validation_alias="GOOGLE_API_BACKOFF_MULTIPLIER")
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, validation_alias="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = Field(default=30, validation_alias="CIRCUIT_BREAKER_RECOVERY_TIMEOUT")

    # Operator System feature flags and tuning
    OPERATOR_WEB_ENABLED: bool = Field(default=False, validation_alias="OPERATOR_WEB_ENABLED")
    OPERATOR_DESKTOP_ENABLED: bool = Field(default=False, validation_alias="OPERATOR_DESKTOP_ENABLED")
    OPERATOR_MAX_CONCURRENT_TASKS: int = Field(default=3, validation_alias="OPERATOR_MAX_CONCURRENT_TASKS")
    OPERATOR_TASK_TIMEOUT_S: int = Field(default=3600, validation_alias="OPERATOR_TASK_TIMEOUT")
    OPERATOR_MONITORING_ENABLED: bool = Field(default=True, validation_alias="OPERATOR_MONITORING_ENABLED")
    OPERATOR_WEB_REAL: bool = Field(default=False, validation_alias="OPERATOR_WEB_REAL")
    OPERATOR_AI_ENABLED: bool = Field(default=False, validation_alias="OPERATOR_AI_ENABLED")
    OPERATOR_ALLOWED_DOMAINS: str = Field(default="*", validation_alias="OPERATOR_ALLOWED_DOMAINS")
    ROI_HOURLY_RATE_USD: float = Field(default=50.0, validation_alias="ROI_HOURLY_RATE_USD")
    ROI_SUCCESS_RATE_THRESHOLD: float = Field(default=0.8, validation_alias="ROI_SUCCESS_RATE_THRESHOLD")

    # Observability / Grafana (optional)
    GRAFANA_BASE_URL: str | None = Field(default=None, validation_alias="GRAFANA_BASE_URL")
    GRAFANA_DASHBOARD_UID: str | None = Field(default=None, validation_alias="GRAFANA_DASHBOARD_UID")

    # Stripe (optional)
    STRIPE_SECRET_KEY: str | None = Field(default=None, validation_alias="STRIPE_SECRET_KEY")

    # System event bus consumer
    SYSTEM_EVENT_CONSUMER_ENABLED: bool = Field(default=False, validation_alias="SYSTEM_EVENT_CONSUMER_ENABLED")
    EVENT_BUS_CONSUMER_GROUP: str = Field(default="system:cg", validation_alias="EVENT_BUS_CONSUMER_GROUP")
    EVENT_BUS_CONSUMER_NAME: str = Field(default="api-1", validation_alias="EVENT_BUS_CONSUMER_NAME")
    EVENT_PROCESSED_CAP: int = Field(default=10000, validation_alias="EVENT_PROCESSED_CAP")

    # Note: Pydantic v2 uses model_config; do not also define class Config


def get_settings() -> Settings:
    return Settings()
