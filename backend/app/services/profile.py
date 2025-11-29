"""Profile service handling Supabase interactions."""

from __future__ import annotations

from typing import Any, Dict, List

from supabase import Client

from app.schemas.profile import (
    ProfileUpdateRequest,
    StudentProfileData,
    StudentProfileResponse,
    UserProfile,
)


class ProfileService:
    """Service layer for profile operations."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _get_user_profile_row(self, user_id: str) -> Dict[str, Any]:
        response = (
            self.supabase.table("user_profiles")
            .select("id, user_id, role, name, school_name")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if response.data is None:
            raise ValueError("ユーザープロフィールが見つかりません")
        return response.data

    def _get_student_profile_row(self, user_id: str) -> Dict[str, Any] | None:
        response = (
            self.supabase.table("student_profiles")
            .select(
                "user_id, grade, class_name, target_industry, target_company, target_position, club_activity, achievements, certifications, strengths, weaknesses, notes"
            )
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    def get_profile(self, user_id: str) -> UserProfile:
        user_profile = self._get_user_profile_row(user_id)
        student_profile = None
        if user_profile.get("role") == "student":
            student_profile = self._get_student_profile_row(user_id)

        return UserProfile(
            **user_profile,
            student_profile=StudentProfileData(**student_profile)
            if student_profile
            else None,
        )

    def update_profile(self, user_id: str, payload: ProfileUpdateRequest) -> UserProfile:
        update_data: Dict[str, Any] = {}
        if payload.name is not None:
            update_data["name"] = payload.name
        if payload.school_name is not None:
            update_data["school_name"] = payload.school_name

        if update_data:
            (
                self.supabase.table("user_profiles")
                .update(update_data)
                .eq("user_id", user_id)
                .execute()
            )

        if payload.student_profile is not None:
            student_data = payload.student_profile.model_dump(exclude_none=True)
            student_data["user_id"] = user_id
            (
                self.supabase.table("student_profiles")
                .upsert(student_data, on_conflict="user_id")
                .execute()
            )

        return self.get_profile(user_id)

    def get_student_detail(self, student_id: str) -> StudentProfileResponse:
        user_profile = self._get_user_profile_row(student_id)
        student_profile = self._get_student_profile_row(student_id)

        session_count = 0
        avg_score = None
        last_session_date = None

        try:
            sessions_resp = (
                self.supabase.table("interview_sessions")
                .select("id, created_at")
                .eq("student_id", student_id)
                .order("created_at", desc=True)
                .execute()
            )
            sessions = sessions_resp.data or []
            session_count = len(sessions)
            if sessions:
                last_session_date = sessions[0].get("created_at")

            if sessions:
                session_ids = [row["id"] for row in sessions]
                evaluations_resp = (
                    self.supabase.table("evaluations")
                    .select("session_id, total_score")
                    .in_("session_id", session_ids)
                    .execute()
                )
                evaluations = [row for row in (evaluations_resp.data or []) if row.get("total_score") is not None]
                if evaluations:
                    avg_score = sum(row["total_score"] for row in evaluations) / len(evaluations)
        except Exception:  # pragma: no cover - Supabase may not yet have tables
            pass

        return StudentProfileResponse(
            id=user_profile["user_id"],
            name=user_profile["name"],
            grade=student_profile.get("grade") if student_profile else None,
            target_industry=student_profile.get("target_industry") if student_profile else None,
            target_company=student_profile.get("target_company") if student_profile else None,
            target_position=student_profile.get("target_position") if student_profile else None,
            session_count=session_count,
            avg_score=avg_score,
            last_session_date=last_session_date,
        )
