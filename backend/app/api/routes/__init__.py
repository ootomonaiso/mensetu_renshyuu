"""Route registrations for API v1."""

from fastapi import APIRouter

from app.api.routes import auth, health, profiles, sessions, upload

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(sessions.router)
api_router.include_router(upload.router)
