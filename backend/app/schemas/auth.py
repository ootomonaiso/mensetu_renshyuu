"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class SignUpRequest(BaseModel):
    """サインアップリクエスト"""

    email: EmailStr
    password: str
    name: str
    role: str  # "student" or "teacher"


class SignInRequest(BaseModel):
    """サインインリクエスト"""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """トークンリフレッシュリクエスト"""

    refresh_token: str


class AuthResponse(BaseModel):
    """認証レスポンス"""

    access_token: str
    refresh_token: str | None = None
    expires_in: int
    user: dict
