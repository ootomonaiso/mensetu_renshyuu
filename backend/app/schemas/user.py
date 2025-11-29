"""User related schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class CurrentUser(BaseModel):
    """情報を付加した現在のユーザーコンテキスト."""

    id: str
    email: EmailStr | str
    role: str
    name: str | None = None
    school_name: str | None = None
