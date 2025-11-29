"""Authentication-related dependencies."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.clients.supabase import get_supabase_client
from app.schemas.user import CurrentUser

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    supabase=Depends(get_supabase_client),
) -> CurrentUser:
    """Resolve the currently authenticated user via Supabase."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが必要です",
        )

    token = credentials.credentials
    try:
        auth_response = supabase.auth.get_user(token)
    except Exception as exc:  # pragma: no cover - Supabase client raises generic errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークン検証に失敗しました",
        ) from exc

    if auth_response.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証済みユーザーが見つかりません",
        )

    user = auth_response.user
    profile_response = (
        supabase.table("user_profiles")
        .select("id, user_id, role, name, school_name")
        .eq("user_id", user.id)
        .single()
        .execute()
    )

    if profile_response.data is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="プロフィールが未登録のためアクセスできません",
        )

    user_profile = profile_response.data

    return CurrentUser(
        id=user.id,
        email=user.email or "",
        role=user_profile.get("role", "student"),
        name=user_profile.get("name"),
        school_name=user_profile.get("school_name"),
    )
