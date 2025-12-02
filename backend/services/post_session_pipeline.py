"""Post-session analysis pipeline for realtime recordings."""
from __future__ import annotations

import asyncio
import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np

from backend.services.audio_analysis import analyze_audio_features, calculate_actual_speech_rate
from backend.services.transcription import transcribe_audio
from backend.services.voice_emotion import analyze_voice_emotion, get_emotion_feedback
from backend.services.ai_analysis import analyze_with_gemini
from backend.services.report import generate_markdown_report

logger = logging.getLogger(__name__)


async def run_post_session_pipeline(
    session_id: str,
    recording_info: Dict[str, Any],
    reports_dir: Path,
) -> Dict[str, Any]:
    """Execute offline analysis once realtime session finishes."""

    audio_path = recording_info.get("audio_path")
    video_path = recording_info.get("video_path")
    session_dir = recording_info.get("session_dir")

    transcript = {}
    audio_features = {}
    voice_emotion = {}
    ai_result = {}
    video_result = {}
    emotion_feedback = ""

    if audio_path and Path(audio_path).exists():
        transcript = await asyncio.to_thread(transcribe_audio, audio_path)
        audio_features = await asyncio.to_thread(analyze_audio_features, audio_path)
        voice_emotion = await asyncio.to_thread(analyze_voice_emotion, audio_path)
        emotion_feedback = get_emotion_feedback(voice_emotion)

        try:
            speech_rate = calculate_actual_speech_rate(
                transcript.get("text", ""),
                audio_features.get("duration", 0) or transcript.get("duration", 0) or 0,
            )
            audio_features["speech_rate"] = speech_rate
        except Exception as exc:  # pragma: no cover - fallback
            logger.warning("話速計算に失敗しました: %s", exc)
    else:
        logger.warning("音声ファイルが見つからないため、音声分析をスキップします")

    if transcript.get("text"):
        ai_result = await asyncio.to_thread(
            analyze_with_gemini,
            transcript.get("text", ""),
            audio_features,
        )

    if video_path and Path(video_path).exists():
        video_result = await analyze_video_for_report(video_path, session_dir, reports_dir, session_id)
    else:
        video_result = {
            "available": False,
            "message": "映像が記録されていないため、ボーン解析は省略されました",
        }

    filename = Path(audio_path).name if audio_path else f"{session_id}.wav"
    report_payload = {
        "filename": filename,
        "transcription": transcript or {"text": ""},
        "audio": audio_features,
        "ai": ai_result,
        "emotion": voice_emotion,
        "emotion_feedback": emotion_feedback,
        "video": video_result,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_filename = f"live_{session_id}.md"
    report_path = reports_dir / report_filename

    await asyncio.to_thread(generate_markdown_report, report_payload, str(report_path))

    return {
        "report_path": str(report_path),
        "report_url": f"/reports/{report_filename}",
        "transcript": transcript,
        "audio": audio_features,
        "emotion": voice_emotion,
        "ai": ai_result,
        "video": video_result,
    }


async def analyze_video_for_report(
    video_path: str,
    session_dir: Optional[str],
    reports_dir: Path,
    session_id: str,
    sample_interval: int = 5,
    max_samples: int = 60,
) -> Dict[str, Any]:
    """Run lightweight pose/eye-contact estimation on recorded video."""
    try:
        from backend.services.video_processors import PoseAnalyzer, EyeContactAnalyzer
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("MediaPipe 利用不可のため映像分析をスキップします: %s", exc)
        return {
            "available": False,
            "message": "MediaPipe が未インストールのため映像分析を実行できませんでした",
        }

    pose_analyzer = PoseAnalyzer()
    eye_analyzer = EyeContactAnalyzer()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning("動画を開けませんでした: %s", video_path)
        return {
            "available": False,
            "message": "録画データを開けなかったため映像分析をスキップしました",
        }

    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    frame_interval = max(1, int(fps * sample_interval))

    pose_scores = []
    eye_scores = []
    overlay_b64 = None
    frames_processed = 0
    frame_index = 0

    while frames_processed < max_samples:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval != 0:
            frame_index += 1
            continue

        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        pose_result, eye_result = await asyncio.gather(
            pose_analyzer.analyze(frame_bytes),
            eye_analyzer.analyze(frame_bytes),
        )

        if pose_result and pose_result.get("score") is not None:
            pose_scores.append(pose_result["score"])
            overlay_b64 = pose_result.get("overlay_image") or overlay_b64

        if eye_result and eye_result.get("score") is not None:
            eye_scores.append(eye_result["score"])

        frames_processed += 1
        frame_index += 1

    cap.release()

    if not pose_scores and not eye_scores:
        return {
            "available": False,
            "message": "映像から有効な骨格ポイントを取得できませんでした",
        }

    overlay_url = None
    if overlay_b64:
        overlay_path = reports_dir / f"{session_id}_pose.jpg"
        with open(overlay_path, "wb") as fout:
            fout.write(base64.b64decode(overlay_b64))
        overlay_url = f"/reports/{overlay_path.name}"

    return {
        "available": True,
        "message": "録画データから骨格・視線を解析しました",
        "posture_score": int(np.mean(pose_scores)) if pose_scores else None,
        "eye_contact_score": int(np.mean(eye_scores)) if eye_scores else None,
        "frames_analyzed": frames_processed,
        "overlay_image": overlay_url,
    }
