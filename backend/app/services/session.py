"""Service layer for interview session operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from supabase import Client

from app.schemas.session import (
    SessionCreateRequest,
    SessionDetailResponse,
    SessionListResponse,
    SessionProcessingLogRequest,
    SessionProcessingLogResponse,
    SessionResponse,
    SessionStatus,
)
from app.schemas.user import CurrentUser


def render_processing_markdown(payload: SessionProcessingLogRequest) -> str:
    """Render Markdown log text from structured payload."""

    if payload.raw_markdown:
        return payload.raw_markdown.strip()

    lines: list[str] = [f"# {payload.title.strip()}", "", payload.summary.strip(), ""]

    if payload.metrics:
        lines.extend(["## 指標サマリ", "", "|項目|値|コメント|", "|---|---|---|"])
        for metric in payload.metrics:
            value = f"{metric.value}{metric.unit or ''}"
            comment = metric.comment or ""
            lines.append(f"|{metric.label}|{value}|{comment}|")
        lines.append("")

    for section in payload.sections:
        lines.extend([f"## {section.heading}", "", section.body.strip(), ""])

    if payload.timeline:
        lines.extend(["## タイムライン", "", "|タイム|イベント|詳細|", "|---|---|---|"])
        for entry in payload.timeline:
            timestamp = entry.timestamp
            if isinstance(timestamp, (float, int)):
                timestamp_str = f"{timestamp:.1f}s"
            else:
                timestamp_str = str(timestamp)
            lines.append(f"|{timestamp_str}|{entry.label}|{entry.detail or ''}|")
        lines.append("")

    markdown = "\n".join(line.rstrip() for line in lines if line is not None)
    return markdown.strip() + "\n"


class SessionService:
    """Encapsulate Supabase interactions for session resources."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def create_session(
        self,
        *,
        student_id: str,
        teacher_id: str | None,
        payload: SessionCreateRequest,
    ) -> SessionDetailResponse:
        insert_payload = payload.model_dump(exclude={"student_id"})
        insert_payload["student_id"] = student_id
        insert_payload["teacher_id"] = teacher_id
        insert_payload.setdefault("status", "recording")

        response = (
            self.supabase.table("interview_sessions")
            .insert(insert_payload)
            .select("*")
            .single()
            .execute()
        )
        if response.data is None:
            raise ValueError("セッションの作成に失敗しました")
        return SessionDetailResponse.model_validate(response.data)

    def list_sessions(
        self,
        *,
        requester: CurrentUser,
        student_id: str | None,
        status: SessionStatus | None,
        limit: int,
        offset: int,
    ) -> SessionListResponse:
        student_filter = self._resolve_student_scope(requester, student_id)

        query = self.supabase.table("interview_sessions").select(
            "id, student_id, teacher_id, title, session_type, target_company, target_position, status, audio_duration, created_at, updated_at",
            count="exact",
        )
        if student_filter is not None:
            query = query.eq("student_id", student_filter)
        if status is not None:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True).range(
            offset, offset + max(limit - 1, 0)
        )
        response = query.execute()
        rows = response.data or []
        total = getattr(response, "count", None) or len(rows)

        return SessionListResponse(
            sessions=[SessionResponse.model_validate(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_session(self, *, session_id: str, requester: CurrentUser) -> SessionDetailResponse:
        row = (
            self.supabase.table("interview_sessions")
            .select("*")
            .eq("id", session_id)
            .single()
            .execute()
        ).data
        if row is None:
            raise ValueError("セッションが見つかりません")

        self._ensure_can_view(row, requester)
        return SessionDetailResponse.model_validate(row)

    def delete_session(self, *, session_id: str, requester: CurrentUser) -> None:
        row = (
            self.supabase.table("interview_sessions")
            .select("id, student_id, teacher_id")
            .eq("id", session_id)
            .single()
            .execute()
        ).data
        if row is None:
            raise ValueError("セッションが見つかりません")
        self._ensure_can_modify(row, requester)
        self.supabase.table("interview_sessions").delete().eq("id", session_id).execute()

    # ------------------------------------------------------------------
    # Processing Log
    # ------------------------------------------------------------------
    def create_processing_log(
        self,
        *,
        session_id: str,
        payload: SessionProcessingLogRequest,
        requester: CurrentUser | None,
    ) -> SessionProcessingLogResponse:
        row = (
            self.supabase.table("interview_sessions")
            .select("id, student_id, teacher_id")
            .eq("id", session_id)
            .single()
            .execute()
        ).data
        if row is None:
            raise ValueError("セッションが見つかりません")
        if requester is not None:
            self._ensure_can_modify(row, requester)

        markdown = render_processing_markdown(payload)
        timeline_payload = [entry.model_dump() for entry in payload.timeline] or None
        update_data: dict[str, Any] = {
            "transcript": markdown,
            "transcript_with_timestamps": timeline_payload,
        }
        if payload.mark_as_completed:
            update_data["status"] = "completed"
            update_data["ended_at"] = datetime.now(tz=timezone.utc).isoformat()

        updated = (
            self.supabase.table("interview_sessions")
            .update(update_data)
            .eq("id", session_id)
            .select("id, student_id, teacher_id, title, session_type, target_company, target_position, status, audio_duration, created_at, updated_at, transcript, transcript_with_timestamps")
            .single()
            .execute()
        ).data
        if updated is None:
            raise ValueError("ログの更新に失敗しました")

        detail = SessionDetailResponse.model_validate(updated)
        return SessionProcessingLogResponse(
            session_id=session_id,
            status=detail.status,
            markdown=markdown,
            updated_at=detail.updated_at,
        )

    def request_processing(self, session_id: str, requester: CurrentUser) -> None:
        row = (
            self.supabase.table("interview_sessions")
            .select("id, student_id, teacher_id")
            .eq("id", session_id)
            .single()
            .execute()
        ).data
        if row is None:
            raise ValueError("セッションが見つかりません")
        self._ensure_can_modify(row, requester)
        self._set_status(session_id, "processing")

    def mark_failed(self, session_id: str) -> None:
        self._set_status(session_id, "failed")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_student_scope(
        requester: CurrentUser, requested_student_id: str | None
    ) -> str | None:
        if requester.role == "student":
            return requester.id
        if requested_student_id:
            return requested_student_id
        return None

    @staticmethod
    def _ensure_can_view(row: dict[str, Any], requester: CurrentUser) -> None:
        if requester.role == "student" and row.get("student_id") != requester.id:
            raise PermissionError("自分のセッションのみ閲覧できます")
        if requester.role not in {"student", "teacher", "admin"}:
            raise PermissionError("権限がありません")

    @staticmethod
    def _ensure_can_modify(row: dict[str, Any], requester: CurrentUser) -> None:
        if requester.role == "student" and row.get("student_id") != requester.id:
            raise PermissionError("自分のセッションのみ更新できます")
        if requester.role in {"teacher", "admin"}:
            return
        if requester.role != "student":
            raise PermissionError("権限がありません")

    def _set_status(self, session_id: str, status: SessionStatus) -> None:
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        self.supabase.table("interview_sessions").update({"status": status, "updated_at": timestamp}).eq("id", session_id).execute()