from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = Field(default="change-me", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    admin_username: str = Field(default="admin", env="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", env="ADMIN_PASSWORD")

    ci_env: bool = Field(default=False, env="CI_ENV")
    ci_cleanup_token: str | None = Field(default=None, env="CI_CLEANUP_TOKEN")
    sentry_dsn: str | None = Field(default=None, env="SENTRY_DSN")
    ci_env: bool = Field(default=False, env="CI_ENV")

    s3_endpoint_url: str | None = Field(default=None, env="S3_ENDPOINT_URL")
    s3_access_key: str | None = Field(default=None, env="S3_ACCESS_KEY")
    s3_secret_key: str | None = Field(default=None, env="S3_SECRET_KEY")
    s3_bucket: str | None = Field(default="artifacts", env="S3_BUCKET")

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
