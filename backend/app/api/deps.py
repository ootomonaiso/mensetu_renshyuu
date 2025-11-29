"""Common FastAPI dependencies."""

from app.core.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Dependency that returns application settings."""

    return get_settings()
