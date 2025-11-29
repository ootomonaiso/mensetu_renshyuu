"""Session management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.clients.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.schemas.session import (
    SessionCreateRequest,
    SessionDetailResponse,
    SessionListResponse,
    SessionProcessingLogRequest,
    SessionProcessingLogResponse,
    SessionProcessingRequest,
    SessionProcessingJobResponse,
    SessionStatus,
)
from app.schemas.user import CurrentUser
from app.services.session import SessionService
from app.tasks.analysis import process_session_analysis

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _service(supabase=Depends(get_supabase_client)) -> SessionService:
    return SessionService(supabase)


@router.post("", response_model=SessionDetailResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(_service),
) -> SessionDetailResponse:
    if current_user.role not in {"student", "teacher", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="権限がありません")

    requested_student_id = payload.student_id
    if current_user.role == "student":
        if requested_student_id and requested_student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="他の生徒のセッションは作成できません")
        resolved_student_id = current_user.id
        teacher_id = None
    else:
        if not requested_student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_idを指定してください",
            )
        resolved_student_id = requested_student_id
        teacher_id = current_user.id

    try:
        return service.create_session(
            student_id=resolved_student_id,
            teacher_id=teacher_id,
            payload=payload,
        )
    except ValueError as exc:  # includes Supabase insert failures
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=SessionListResponse)
def list_sessions(
    status_filter: SessionStatus | None = Query(default=None, alias="status"),
    student_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(_service),
) -> SessionListResponse:
    try:
        return service.list_sessions(
            requester=current_user,
            student_id=student_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(_service),
) -> SessionDetailResponse:
    try:
        return service.get_session(session_id=session_id, requester=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
def delete_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(_service),
) -> dict:
    try:
        service.delete_session(session_id=session_id, requester=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return {"status": "deleted"}


@router.post(
    "/{session_id}/process",
    response_model=SessionProcessingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_processing_task(
    session_id: str,
    payload: SessionProcessingRequest = Body(default_factory=SessionProcessingRequest),
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(_service),
) -> SessionProcessingJobResponse:
    try:
        service.request_processing(session_id=session_id, requester=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    async_result = process_session_analysis.delay(
        session_id=session_id,
        request_payload=payload.model_dump(exclude_none=True),
    )
    return SessionProcessingJobResponse(task_id=async_result.id, status="queued")


@router.post(
    "/{session_id}/logs",
    response_model=SessionProcessingLogResponse,
    status_code=status.HTTP_200_OK,
)
def create_processing_log(
    session_id: str,
    payload: SessionProcessingLogRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(_service),
) -> SessionProcessingLogResponse:
    try:
        return service.create_processing_log(
            session_id=session_id,
            requester=current_user,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
