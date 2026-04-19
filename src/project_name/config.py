"""Application configuration via pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str | None = None  # only needed for direct API usage; Claude Code CLI handles auth automatically
    model_name: str = "claude-sonnet-4-6"
    database_url: str = "sqlite:///./dev.db"
    qdrant_url: str = "http://localhost:6333"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
