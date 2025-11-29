"""Celery tasks for analysis and Markdown log generation."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from structlog import get_logger

from app.celery_app import celery_app
from app.clients.supabase import get_supabase_client
from app.schemas.session import (
    SessionLogSection,
    SessionMetric,
    SessionProcessingLogRequest,
    SessionTimelineEntry,
)
from app.services.session import SessionService

logger = get_logger(__name__)


@celery_app.task(name="analysis.process_audio", bind=True, max_retries=3)
def process_audio_analysis(
    self,
    session_id: str,
    audio_file_path: str,
    video_file_path: str | None = None,
    duration: int = 0,
) -> dict:
    """
    音声・動画分析処理タスク（バックグラウンド実行）

    - faster-whisper で文字起こし
    - librosa で音響分析
    - Gemini API で評価
    - 結果をMarkdownで整形してDBに保存
    """
    supabase = get_supabase_client()
    session_service = SessionService(supabase)

    try:
        # 遅延インポート（Celeryワーカー起動時のみ必要）
        from app.services.analysis import AudioAnalysisService
        from app.services.gemini import GeminiService

        audio_service = AudioAnalysisService()
        gemini_service = GeminiService()

        # 1. 文字起こし
        logger.info("transcription_started", session_id=session_id)
        transcript_data = audio_service.transcribe_audio(audio_file_path)

        # 2. 音響分析
        logger.info("acoustic_analysis_started", session_id=session_id)
        acoustic_data = audio_service.analyze_acoustic_features(audio_file_path)

        # 3. DB保存（transcript + audio_analysis）
        audio_service.save_audio_analysis(session_id, transcript_data, acoustic_data)

        # 4. Gemini評価
        logger.info("ai_evaluation_started", session_id=session_id)
        gemini_service.save_evaluation(session_id, transcript_data["transcript"])

        # 5. Markdownレポート生成
        logger.info("report_generation_started", session_id=session_id)
        markdown_log = session_service._render_processing_markdown(session_id)
        session_service.create_processing_log(session_id=session_id, markdown_content=markdown_log)

        # 一時ファイル削除
        Path(audio_file_path).unlink(missing_ok=True)
        if video_file_path:
            Path(video_file_path).unlink(missing_ok=True)

        logger.info("analysis_completed", session_id=session_id, task_id=self.request.id)
        return {"session_id": session_id, "status": "completed", "task_id": self.request.id}

    except Exception as exc:
        logger.exception("analysis_task_failed", session_id=session_id)
        session_service.mark_failed(session_id=session_id, error_message=str(exc))

        # 一時ファイル削除
        try:
            Path(audio_file_path).unlink(missing_ok=True)
            if video_file_path:
                Path(video_file_path).unlink(missing_ok=True)
        except Exception:
            pass

        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="analysis.process_session", bind=True)
def process_session_analysis(self, session_id: str, request_payload: Mapping[str, Any] | None = None) -> dict:
    """Generate Markdown processing logs for a session without handling binary media."""

    request_payload = request_payload or {}
    supabase = get_supabase_client()
    service = SessionService(supabase)

    session_response = (
        supabase.table("interview_sessions")
        .select("id, title, student_id, teacher_id, session_type, created_at")
        .eq("id", session_id)
        .single()
        .execute()
    )
    session_row = session_response.data
    if not session_row:
        logger.error("session_not_found", session_id=session_id)
        raise ValueError("セッションが見つかりません")

    try:
        payload = _build_log_payload(session_row, request_payload)
        result = service.create_processing_log(
            session_id=session_id,
            requester=None,
            payload=payload,
        )
        logger.info(
            "analysis_log_created",
            session_id=session_id,
            markdown_length=len(result.markdown),
            status=result.status,
        )
        return {"session_id": session_id, "status": result.status, "task_id": self.request.id}
    except Exception as exc:  # pragma: no cover - Celery runtime path
        logger.exception("analysis_task_failed", session_id=session_id)
        service.mark_failed(session_id)
        raise exc


def _build_log_payload(session_row: Mapping[str, Any], request_payload: Mapping[str, Any]) -> SessionProcessingLogRequest:
    title = f"{session_row.get('title', '面接')} 自動処理ログ"
    summary = _build_summary_text(session_row, request_payload)
    metrics = _build_metrics(request_payload.get("audio_features"))
    sections = _build_sections(request_payload)
    timeline = _build_timeline(request_payload.get("timeline"))

    return SessionProcessingLogRequest(
        title=title,
        summary=summary,
        metrics=metrics,
        sections=sections,
        timeline=timeline,
        mark_as_completed=True,
    )


def _build_summary_text(session_row: Mapping[str, Any], request_payload: Mapping[str, Any]) -> str:
    transcript = (request_payload.get("transcript") or "").strip()
    if transcript:
        lines = transcript.splitlines()
        head = lines[0][:120]
        return f"{head}\n\n- 自動生成日時: {datetime.now().isoformat(timespec='seconds')}"

    highlights = request_payload.get("highlights") or []
    if highlights:
        first = highlights[0]
        return f"{first}\n\n- 自動生成日時: {datetime.now().isoformat(timespec='seconds')}"

    return (
        f"{session_row.get('title', '面接セッション')} の結果をもとにした自動要約です。"
        f"\n\n- 自動生成日時: {datetime.now().isoformat(timespec='seconds')}"
    )


def _build_metrics(audio_features: Mapping[str, Any] | None) -> list[SessionMetric]:
    metrics: list[SessionMetric] = []
    if audio_features:
        for key, value in audio_features.items():
            metrics.append(
                SessionMetric(
                    label=_format_label(key),
                    value=_normalize_metric_value(value),
                    unit=_guess_unit(key),
                    comment="提供値",
                )
            )

    if metrics:
        return metrics

    return [
        SessionMetric(label="話速推定", value=165, unit="wpm", comment="暫定値"),
        SessionMetric(label="声量推定", value=-16, unit="LUFS", comment="参考値"),
    ]


def _build_sections(request_payload: Mapping[str, Any]) -> list[SessionLogSection]:
    sections: list[SessionLogSection] = []
    highlights = request_payload.get("highlights") or []
    if highlights:
        body = "\n".join(f"- {item}" for item in highlights)
        sections.append(SessionLogSection(heading="注目ポイント", body=body))

    notes = request_payload.get("notes")
    if notes:
        sections.append(SessionLogSection(heading="追加メモ", body=str(notes)))

    transcript = (request_payload.get("transcript") or "").strip()
    if transcript:
        excerpt = "\n".join(transcript.splitlines()[:5])
        sections.append(SessionLogSection(heading="文字起こし抜粋", body=excerpt))

    return sections


def _build_timeline(timeline_payload: Any) -> list[SessionTimelineEntry]:
    entries: list[SessionTimelineEntry] = []
    if not timeline_payload:
        return entries

    for entry in timeline_payload:
        try:
            entries.append(SessionTimelineEntry(**entry))
        except Exception:
            continue
    return entries


def _format_label(raw: str) -> str:
    return raw.replace("_", " ").title()


def _guess_unit(key: str) -> str | None:
    lowered = key.lower()
    if "rate" in lowered:
        return "wpm"
    if "volume" in lowered or "lufs" in lowered:
        return "LUFS"
    if "pitch" in lowered:
        return "Hz"
    if "duration" in lowered or "time" in lowered:
        return "s"
    return None


def _normalize_metric_value(value: Any) -> str | float | int:
    if isinstance(value, (int, float)):
        return value
    return str(value)
