"""Application settings management using Pydantic."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration loaded from env variables/.env file."""

    environment: str = Field(default="local", alias="ENVIRONMENT")
    project_name: str = Field(default="圧勝面接API", alias="PROJECT_NAME")
    version: str = Field(default="0.1.0", alias="APP_VERSION")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    allowed_origins_str: str = Field(
        default="http://localhost:5173", alias="ALLOWED_ORIGINS"
    )

    @property
    def allowed_origins(self) -> List[str]:
        """Parse allowed origins from string."""
        return [
            origin.strip()
            for origin in self.allowed_origins_str.split(",")
            if origin.strip()
        ]

    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_anon_key: str | None = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str | None = Field(
        default=None, alias="SUPABASE_SERVICE_ROLE_KEY"
    )
    supabase_jwt_secret: str | None = Field(default=None, alias="SUPABASE_JWT_SECRET")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
