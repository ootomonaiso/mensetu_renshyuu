"""音声・動画アップロードと分析処理"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.dependencies.auth import get_current_user
from app.schemas.user import CurrentUser
from app.services.session import SessionService
from app.clients.supabase import get_supabase_client
from app.tasks.analysis import process_audio_analysis

router = APIRouter(prefix="/sessions/{session_id}/upload", tags=["upload"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_recording(
    session_id: str,
    audio: UploadFile = File(...),
    duration: int = Form(...),
    video: UploadFile | None = File(None),
    current_user: CurrentUser = Depends(get_current_user),
    supabase=Depends(get_supabase_client),
) -> dict:
    """
    音声・動画ファイルをアップロードして分析開始
    
    - 音声ファイルを一時保存
    - Celeryタスクで文字起こし + 音響分析
    - 動画ファイルは姿勢分析用（Phase 4）
    """
    service = SessionService(supabase)
    
    try:
        # セッション取得して権限確認
        session_data = service.get_session(session_id=session_id, requester=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    
    # 音声ファイルを一時ディレクトリに保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_audio:
        audio_content = await audio.read()
        tmp_audio.write(audio_content)
        audio_path = tmp_audio.name
    
    # ビデオファイルも保存（任意）
    video_path = None
    if video:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_video:
            video_content = await video.read()
            tmp_video.write(video_content)
            video_path = tmp_video.name
    
    # セッションステータスを「processing」に更新
    service.request_processing(session_id=session_id, requester=current_user)
    
    # Celeryタスクで非同期処理開始
    task = process_audio_analysis.delay(
        session_id=session_id,
        audio_file_path=audio_path,
        video_file_path=video_path,
        duration=duration,
    )
    
    return {
        "status": "processing",
        "task_id": task.id,
        "message": "音声分析を開始しました。完了までお待ちください。",
    }
