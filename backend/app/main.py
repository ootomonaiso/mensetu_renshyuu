"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)


def create_application() -> FastAPI:
    """Instantiate the FastAPI application."""

    app = FastAPI(title=settings.project_name, version=settings.version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


def get_app() -> FastAPI:  # pragma: no cover - convenience for ASGI servers
    """Return application instance (for tooling)."""

    return create_application()


app = create_application()
