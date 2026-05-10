"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the service."""

    app_name: str = "AI Mail Assistant"
    app_env: str = "local"
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_mail_assistant"
    )
    llm_provider: Literal["fake", "openai"] = "fake"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
