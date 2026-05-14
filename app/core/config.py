"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings loaded from environment variables."""

    app_name: str = Field(default="Book Generation System", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/bookgen",
        alias="DATABASE_URL",
    )
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    artifacts_dir: str = Field(default="artifacts", alias="ARTIFACTS_DIR")
    serper_api_key: str = Field(default="", alias="SERPER_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_model: str = Field(default="gemma-4-26b-a4b-it", alias="GOOGLE_MODEL")
    google_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        alias="GOOGLE_BASE_URL",
    )
    google_max_retries: int = Field(default=3, alias="GOOGLE_MAX_RETRIES")
    google_retry_delay_seconds: float = Field(default=1.5, alias="GOOGLE_RETRY_DELAY_SECONDS")
    teams_webhook_url: str = Field(default="", alias="TEAMS_WEBHOOK_URL")
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    notification_email_to: str = Field(default="", alias="NOTIFICATION_EMAIL_TO")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def artifacts_path(self) -> Path:
        """Resolve the artifact output directory."""
        return Path(self.artifacts_dir)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
