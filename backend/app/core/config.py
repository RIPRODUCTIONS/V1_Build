from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # In pydantic v2, allow extra keys in env/.env to avoid validation errors
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    jwt_secret: str = Field(default='change-me', env='JWT_SECRET')
    jwt_algorithm: str = Field(default='HS256', env='JWT_ALGORITHM')
    jwt_issuer: str | None = Field(default=None, env='JWT_ISSUER')
    jwt_audience: str | None = Field(default=None, env='JWT_AUDIENCE')
    jwt_leeway_seconds: int = Field(default=0, env='JWT_LEEWAY_SECONDS')
    jwt_verify_exp: bool = Field(default=True, env='JWT_VERIFY_EXP')
    jwt_verify_iat: bool = Field(default=True, env='JWT_VERIFY_IAT')
    jwt_verify_nbf: bool = Field(default=True, env='JWT_VERIFY_NBF')
    access_token_expire_minutes: int = Field(default=60, env='ACCESS_TOKEN_EXPIRE_MINUTES')

    admin_username: str = Field(default='admin', env='ADMIN_USERNAME')
    admin_password: str = Field(default='admin', env='ADMIN_PASSWORD')

    ci_env: bool = Field(default=False, env='CI_ENV')
    ci_cleanup_token: str | None = Field(default=None, env='CI_CLEANUP_TOKEN')
    sentry_dsn: str | None = Field(default=None, env='SENTRY_DSN')

    s3_endpoint_url: str | None = Field(default=None, env='S3_ENDPOINT_URL')
    s3_access_key: str | None = Field(default=None, env='S3_ACCESS_KEY')
    s3_secret_key: str | None = Field(default=None, env='S3_SECRET_KEY')
    s3_bucket: str | None = Field(default='artifacts', env='S3_BUCKET')

    # Feature flags
    PROTOTYPE_BUILDER_ENABLED: bool = Field(default=True, env='PROTOTYPE_BUILDER_ENABLED')
    RESEARCH_ENABLED: bool = Field(default=False, env='RESEARCH_ENABLED')
    RESEARCH_CACHE_TTL_S: int = Field(default=900, env='RESEARCH_CACHE_TTL_S')
    RESEARCH_CACHE_MAX_ITEMS: int = Field(default=512, env='RESEARCH_CACHE_MAX_ITEMS')
    RESEARCH_SEARCH_QPS: float = Field(default=2.0, env='RESEARCH_SEARCH_QPS')
    RESEARCH_FETCH_RPS: float = Field(default=2.0, env='RESEARCH_FETCH_RPS')
    RESEARCH_FETCH_TIMEOUT_S: int = Field(default=6, env='RESEARCH_FETCH_TIMEOUT_S')
    RESEARCH_FETCH_MAX_BYTES: int = Field(default=2_000_000, env='RESEARCH_FETCH_MAX_BYTES')
    # Aliases for alternative env variable names
    RESEARCH_CACHE_TTL_SECONDS: int = Field(default=3600, env='RESEARCH_CACHE_TTL_SECONDS')
    RESEARCH_TOKENS_PER_SECOND: float = Field(default=2.0, env='RESEARCH_TOKENS_PER_SECOND')
    RESEARCH_BURST: int = Field(default=5, env='RESEARCH_BURST')
    RESEARCH_OFFLINE_FIXTURES_DIR: str = Field(
        default='tools/web_research/fixtures', env='RESEARCH_OFFLINE_FIXTURES_DIR'
    )

    # Additional feature flags for hardening rollouts
    FEATURE_LEGACY_RUNS: bool = Field(default=True, env='FEATURE_LEGACY_RUNS')
    FEATURE_STRICT_CSP: bool = Field(default=False, env='FEATURE_STRICT_CSP')

    # LLM routing (local-first defaults)
    LLM_PRIMARY: str = Field(
        default='lmstudio', env='LLM_PRIMARY'
    )  # lmstudio|ollama|vllm|openai|anthropic
    LLM_FALLBACK: str = Field(default='none', env='LLM_FALLBACK')  # none|ollama|openai|anthropic
    OPENAI_API_KEY: str | None = Field(default=None, env='OPENAI_API_KEY')
    OPENAI_MODEL: str = Field(default='gpt-4o-mini', env='OPENAI_MODEL')
    ANTHROPIC_API_KEY: str | None = Field(default=None, env='ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL: str = Field(default='claude-3-5-sonnet-latest', env='ANTHROPIC_MODEL')
    OLLAMA_HOST: str = Field(default='http://127.0.0.1:11434', env='OLLAMA_HOST')
    OLLAMA_MODEL: str = Field(default='llama3.1:8b', env='OLLAMA_MODEL')
    LMSTUDIO_BASE_URL: str = Field(default='http://127.0.0.1:1234/v1', env='LMSTUDIO_BASE_URL')
    LMSTUDIO_MODEL: str = Field(default='local-model', env='LMSTUDIO_MODEL')
    VLLM_BASE_URL: str = Field(default='http://127.0.0.1:8001/v1', env='VLLM_BASE_URL')
    VLLM_MODEL: str = Field(default='local-model', env='VLLM_MODEL')
    LLM_POLICY: str = Field(default='70b, 405b, 8x7b, 8x22b, 405m, 8b', env='LLM_POLICY')
    LLM_TIMEOUT_S: float = Field(default=10.0, env='LLM_TIMEOUT_S')
    LLM_RETRIES: int = Field(default=0, env='LLM_RETRIES')
    LLM_CB_FAIL_THRESHOLD: int = Field(default=3, env='LLM_CB_FAIL_THRESHOLD')
    LLM_CB_RESET_S: float = Field(default=30.0, env='LLM_CB_RESET_S')

    # Caching/Queue
    REDIS_URL: str = Field(default='redis://localhost:6379/0', env='REDIS_URL')
    ALLOW_START_WITHOUT_REDIS: bool = Field(default=True, env='ALLOW_START_WITHOUT_REDIS')
    CELERY_EAGER: bool = Field(default=True, env='CELERY_EAGER')

    # Security toggle for read RBAC on selected endpoints
    SECURE_MODE: bool = Field(default=False, env='SECURE_MODE')

    # Celery queues for automation
    CELERY_BROKER_URL: str = Field(default='redis://127.0.0.1:6379/1', env='CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND: str = Field(
        default='redis://127.0.0.1:6379/2', env='CELERY_RESULT_BACKEND'
    )

    # Autonomous Mode Configuration
    AUTONOMOUS_MODE: bool = Field(default=False, env='AUTONOMOUS_MODE')
    AUTONOMOUS_IDEA_CRON: str = Field(
        default='0 8 * * *', env='AUTONOMOUS_IDEA_CRON'
    )  # daily 08:00
    AUTONOMOUS_TOPIC: str = Field(default='emerging+automation', env='AUTONOMOUS_TOPIC')
    NOTIFY_EMAIL_TO: str = Field(default='', env='NOTIFY_EMAIL_TO')

    # Development/Startup Configuration
    DISABLE_STARTUP_HOOKS: bool = Field(default=False, env='DISABLE_STARTUP_HOOKS')
    SKIP_DB_INIT: bool = Field(default=False, env='SKIP_DB_INIT')

    # Note: Pydantic v2 uses model_config; do not also define class Config


def get_settings() -> Settings:
    return Settings()
