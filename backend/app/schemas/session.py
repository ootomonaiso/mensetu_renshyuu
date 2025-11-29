"""Session related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SessionType = Literal["practice", "mock", "real"]
SessionStatus = Literal["recording", "processing", "completed", "failed"]


class SessionBase(BaseModel):
    """Common fields shared between session responses."""

    title: str = Field(..., description="セッションタイトル")
    session_type: SessionType = Field(..., description="practice/mock/real")
    target_company: str | None = Field(default=None)
    target_position: str | None = Field(default=None)

    model_config = ConfigDict(extra="ignore")


class SessionCreateRequest(SessionBase):
    student_id: str | None = Field(
        default=None,
        description="教師が代理作成する場合のみ指定。生徒は無視される",
    )


class SessionResponse(SessionBase):
    id: str
    student_id: str
    teacher_id: str | None = None
    status: SessionStatus = "recording"
    audio_duration: int | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class SessionDetailResponse(SessionResponse):
    transcript: str | None = None
    transcript_with_timestamps: list[dict] | None = None


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int


class SessionMetric(BaseModel):
    label: str
    value: str | float | int
    unit: str | None = None
    comment: str | None = None


class SessionLogSection(BaseModel):
    heading: str
    body: str


class SessionTimelineEntry(BaseModel):
    timestamp: float | int | str
    label: str
    detail: str | None = None


class SessionProcessingLogRequest(BaseModel):
    title: str = Field(..., description="ログタイトル")
    summary: str = Field(..., description="要約 (Markdown可)")
    metrics: list[SessionMetric] = Field(default_factory=list)
    sections: list[SessionLogSection] = Field(default_factory=list)
    timeline: list[SessionTimelineEntry] = Field(default_factory=list)
    raw_markdown: str | None = Field(
        default=None, description="既に整形済みのMarkdownがある場合に指定"
    )
    mark_as_completed: bool = Field(
        default=True, description="処理完了扱いにしてステータスを更新する"
    )


class SessionProcessingLogResponse(BaseModel):
    session_id: str
    status: SessionStatus
    markdown: str
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class SessionProcessingRequest(BaseModel):
    transcript: str | None = None
    highlights: list[str] | None = None
    notes: str | None = None
    audio_features: dict[str, float | int | str] | None = None
    timeline: list[SessionTimelineEntry] | None = None


class SessionProcessingJobResponse(BaseModel):
    task_id: str
    status: str = "queued"
