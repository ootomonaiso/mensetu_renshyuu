"""System level response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DependencyStatus(BaseModel):
    """Represents health status of a downstream dependency."""

    name: str
    healthy: bool
    detail: str | None = None


class HealthResponse(BaseModel):
    """API health check response."""

    status: str = Field(default="ok")
    environment: str
    version: str
    dependencies: list[DependencyStatus] = Field(default_factory=list)
