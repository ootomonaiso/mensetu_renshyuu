"""フロントエンド用アップロードAPI型定義"""
import type { Session } from "./sessions";

export interface UploadRecordingRequest {
  audio: Blob;
  video?: Blob;
  duration: number;
}

export interface UploadRecordingResponse {
  status: "processing";
  task_id: string;
  message: string;
}

export async function uploadRecording(
  sessionId: string,
  request: UploadRecordingRequest
): Promise<UploadRecordingResponse> {
  const formData = new FormData();
  formData.append("audio", request.audio, "recording.webm");
  formData.append("duration", String(request.duration));
  
  if (request.video) {
    formData.append("video", request.video, "recording.webm");
  }

  const res = await fetch(`/api/v1/sessions/${sessionId}/upload`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "アップロードに失敗しました" }));
    throw new Error(error.detail || "アップロードに失敗しました");
  }

  return res.json();
}
