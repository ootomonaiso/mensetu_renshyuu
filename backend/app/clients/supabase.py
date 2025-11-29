"""Supabase client helper functions."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from app.core.config import get_settings


class SupabaseNotConfiguredError(RuntimeError):
    """Raised when Supabase credentials are missing."""


@lru_cache
def get_supabase_client() -> Client:
    """Return a cached Supabase client instance."""

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise SupabaseNotConfiguredError(
            "Supabase URL / Service Role Key are not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def is_supabase_configured() -> bool:
    """Whether Supabase credentials exist (used for health checks)."""

    settings = get_settings()
    return bool(settings.supabase_url and settings.supabase_service_role_key)
