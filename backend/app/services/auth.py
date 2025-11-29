"""Authentication service."""

from supabase import Client
from app.schemas.auth import SignUpRequest, SignInRequest


class AuthService:
    """認証サービス"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def sign_up(self, data: SignUpRequest):
        """ユーザー登録"""
        # Supabase Auth でユーザー作成
        auth_response = self.supabase.auth.sign_up(
            {"email": data.email, "password": data.password}
        )

        if auth_response.user is None:
            raise ValueError("ユーザー登録に失敗しました")

        # user_profiles テーブルにプロフィール作成
        profile_data = {
            "user_id": auth_response.user.id,
            "role": data.role,
            "name": data.name,
        }

        self.supabase.table("user_profiles").insert(profile_data).execute()

        return {
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "role": data.role,
            },
            "session": {
                "access_token": auth_response.session.access_token
                if auth_response.session
                else None,
                "refresh_token": auth_response.session.refresh_token
                if auth_response.session
                else None,
                "expires_in": auth_response.session.expires_in
                if auth_response.session
                else 3600,
            },
        }

    async def sign_in(self, data: SignInRequest):
        """ログイン"""
        auth_response = self.supabase.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )

        if auth_response.user is None or auth_response.session is None:
            raise ValueError("認証に失敗しました")

        # プロフィール取得
        profile_response = (
            self.supabase.table("user_profiles")
            .select("role")
            .eq("user_id", auth_response.user.id)
            .single()
            .execute()
        )

        return {
            "session": {
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "expires_in": auth_response.session.expires_in,
            },
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "role": profile_response.data.get("role") if profile_response.data else None,
            },
        }

    async def refresh_token(self, refresh_token: str):
        """トークンリフレッシュ"""
        auth_response = self.supabase.auth.refresh_session(refresh_token)

        if auth_response.session is None:
            raise ValueError("トークンリフレッシュに失敗しました")

        return {
            "access_token": auth_response.session.access_token,
            "expires_in": auth_response.session.expires_in,
        }

    async def sign_out(self):
        """ログアウト"""
        self.supabase.auth.sign_out()
