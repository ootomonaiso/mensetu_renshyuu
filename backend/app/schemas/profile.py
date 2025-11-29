"""Profile schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Achievement(BaseModel):
    title: str
    description: str
    date: str | None = None


class Certification(BaseModel):
    name: str
    date: str | None = None
    score: str | None = None


class StudentProfileData(BaseModel):
    grade: str | None = None
    class_name: str | None = None
    target_industry: str | None = None
    target_company: str | None = None
    target_position: str | None = None
    club_activity: str | None = None
    achievements: List[Achievement] | None = None
    certifications: List[Certification] | None = None
    strengths: List[str] | None = None
    weaknesses: List[str] | None = None
    notes: str | None = None


class UserProfile(BaseModel):
    id: str
    user_id: str
    role: str
    name: str | None = None
    school_name: str | None = None
    student_profile: StudentProfileData | None = None


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, description="表示名")
    school_name: str | None = None
    student_profile: StudentProfileData | None = None


class StudentProfileResponse(BaseModel):
    id: str
    name: str
    grade: str | None = None
    target_industry: str | None = None
    target_company: str | None = None
    target_position: str | None = None
    session_count: int | None = None
    avg_score: float | None = None
    last_session_date: str | None = None
