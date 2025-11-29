"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.clients.supabase import is_supabase_configured
from app.core.config import get_settings
from app.models import DependencyStatus, HealthResponse

router = APIRouter()


@router.get(
    "/ping",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """Return application health and dependency status."""

    settings = get_settings()
    supabase_ready = is_supabase_configured()

    dependencies = [
        DependencyStatus(
            name="supabase",
            healthy=supabase_ready,
            detail=(
                "Credentials loaded"
                if supabase_ready
                else "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not configured"
            ),
        )
    ]

    return HealthResponse(
        status="ok",
        environment=settings.environment,
        version=settings.version,
        dependencies=dependencies,
    )
