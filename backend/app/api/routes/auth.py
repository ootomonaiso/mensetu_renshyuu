"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import (
    SignUpRequest,
    SignInRequest,
    RefreshTokenRequest,
    AuthResponse,
)
from app.services.auth import AuthService
from app.clients.supabase import get_supabase_client

router = APIRouter(prefix="/auth", tags=["認証"])


@router.post("/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def sign_up(
    data: SignUpRequest,
    supabase=Depends(get_supabase_client),
):
    """ユーザー登録"""
    try:
        auth_service = AuthService(supabase)
        result = await auth_service.sign_up(data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"登録に失敗しました: {str(e)}",
        )


@router.post("/login", response_model=dict)
async def sign_in(
    data: SignInRequest,
    supabase=Depends(get_supabase_client),
):
    """ログイン"""
    try:
        auth_service = AuthService(supabase)
        result = await auth_service.sign_in(data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"認証に失敗しました: {str(e)}",
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    data: RefreshTokenRequest,
    supabase=Depends(get_supabase_client),
):
    """トークンリフレッシュ"""
    try:
        auth_service = AuthService(supabase)
        result = await auth_service.refresh_token(data.refresh_token)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"トークンリフレッシュに失敗しました: {str(e)}",
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(supabase=Depends(get_supabase_client)):
    """ログアウト"""
    try:
        auth_service = AuthService(supabase)
        await auth_service.sign_out()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ログアウトに失敗しました: {str(e)}",
        )
