"""Profile related endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.clients.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.schemas.profile import (
    ProfileUpdateRequest,
    StudentProfileResponse,
    UserProfile,
)
from app.schemas.user import CurrentUser
from app.services.profile import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _get_service(supabase=Depends(get_supabase_client)) -> ProfileService:
    return ProfileService(supabase)


@router.get("/me", response_model=UserProfile)
def get_profile_me(
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(_get_service),
) -> UserProfile:
    return service.get_profile(current_user.id)


@router.put("/me", response_model=UserProfile)
def update_profile_me(
    payload: ProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(_get_service),
) -> UserProfile:
    return service.update_profile(current_user.id, payload)


@router.get("/students/{student_id}", response_model=StudentProfileResponse)
def get_student_profile(
    student_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(_get_service),
) -> StudentProfileResponse:
    if current_user.role not in {"teacher", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="教師権限が必要です",
        )
    return service.get_student_detail(student_id)
