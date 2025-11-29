import { apiFetch } from '../lib/apiClient'

export type SessionStatus = 'recording' | 'processing' | 'completed' | 'failed'
export type SessionType = 'practice' | 'mock' | 'real'

export interface SessionSummary {
  id: string
  student_id: string
  teacher_id?: string | null
  title: string
  session_type: SessionType
  target_company?: string | null
  target_position?: string | null
  status: SessionStatus
  audio_duration?: number | null
  created_at: string
  updated_at?: string | null
}

export interface SessionDetail extends SessionSummary {
  transcript?: string | null
  transcript_with_timestamps?: Array<Record<string, unknown>> | null
}

export interface SessionListResponse {
  sessions: SessionSummary[]
  total: number
  limit: number
  offset: number
}

export interface SessionCreatePayload {
  title: string
  session_type: SessionType
  target_company?: string
  target_position?: string
  student_id?: string
}

export interface ProcessingRequestPayload {
  transcript?: string
  highlights?: string[]
  notes?: string
  audio_features?: Record<string, string | number>
  timeline?: Array<{ timestamp: number | string; label: string; detail?: string }>
}

export interface ProcessingJobResponse {
  task_id: string
  status: string
}

export async function listSessions(params?: { status?: SessionStatus; student_id?: string; limit?: number; offset?: number }) {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set('status', params.status)
  if (params?.student_id) searchParams.set('student_id', params.student_id)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())

  const query = searchParams.toString()
  return apiFetch<SessionListResponse>(`/sessions${query ? `?${query}` : ''}`)
}

export function getSession(sessionId: string) {
  return apiFetch<SessionDetail>(`/sessions/${sessionId}`)
}

export function createSession(payload: SessionCreatePayload) {
  return apiFetch<SessionDetail>('/sessions', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function deleteSession(sessionId: string) {
  return apiFetch<{ status: string }>(`/sessions/${sessionId}`, {
    method: 'DELETE',
  })
}

export function requestProcessing(sessionId: string, payload?: ProcessingRequestPayload) {
  return apiFetch<ProcessingJobResponse>(`/sessions/${sessionId}/process`, {
    method: 'POST',
    body: JSON.stringify(payload ?? {}),
  })
}

export function saveProcessingLog(sessionId: string, payload: { title: string; summary: string; markdown?: string }) {
  return apiFetch(`/sessions/${sessionId}/logs`, {
    method: 'POST',
    body: JSON.stringify({
      title: payload.title,
      summary: payload.summary,
      raw_markdown: payload.markdown,
      mark_as_completed: true,
    }),
  })
}
