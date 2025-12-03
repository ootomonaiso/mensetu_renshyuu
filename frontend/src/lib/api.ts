import { z } from 'zod'

const API_BASE = import.meta.env.VITE_API_BASE?.replace(/\/$/, '') ?? 'http://localhost:8000'

const analyzeSummarySchema = z.object({
  status: z.string(),
  report_url: z.string(),
  report_path: z.string(),
  summary: z.object({
    transcript_length: z.number(),
    speech_rate: z.number(),
    keywords: z.array(z.string()).default([]),
    confidence_score: z.number().min(0).max(100),
    nervousness_score: z.number().min(0).max(100),
  }),
})

const reportSummarySchema = z.object({
  filename: z.string(),
  url: z.string(),
  created_at: z.string(),
  size: z.number(),
  modified_at: z.string().optional(),
})

const reportListSchema = z.object({
  status: z.string(),
  count: z.number(),
  reports: z.array(reportSummarySchema),
})

const videoUploadSchema = z.object({
  status: z.union([z.literal('success'), z.literal('pending'), z.literal('error')]),
  message: z.string().optional(),
  preview_url: z.string().optional(),
})

export type AnalyzeSummary = z.infer<typeof analyzeSummarySchema>
export type ReportSummary = z.infer<typeof reportSummarySchema>
export type ReportListResponse = z.infer<typeof reportListSchema>
export type VideoUploadResponse = z.infer<typeof videoUploadSchema>

async function handleResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T
  }

  const text = await response.text()
  throw new Error(text || fallbackMessage)
}

export async function uploadAudioFile(blob: Blob, filename: string) {
  const formData = new FormData()
  formData.append('file', blob, filename)

  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    body: formData,
  })

  const json = await handleResponse<unknown>(response, '音声の分析リクエストに失敗しました')
  return analyzeSummarySchema.parse(json)
}

export async function uploadVideoFile(blob: Blob, filename: string): Promise<VideoUploadResponse> {
  const formData = new FormData()
  formData.append('file', blob, filename)

  try {
    const response = await fetch(`${API_BASE}/api/video/analyze`, {
      method: 'POST',
      body: formData,
    })

    if (response.status === 404) {
      return {
        status: 'pending',
        message: 'バックエンドの動画分析 API がまだ利用できません。録画ファイルはローカルに保存してください。',
      }
    }

    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || '動画のアップロードに失敗しました')
    }

    const data = (await response.json()) as unknown
    return videoUploadSchema.parse(data)
  } catch (error) {
    if (error instanceof Error) {
      return { status: 'error', message: error.message }
    }
    return { status: 'error', message: '動画のアップロードに失敗しました' }
  }
}

export async function fetchReports() {
  const response = await fetch(`${API_BASE}/api/reports`)
  const json = await handleResponse<unknown>(response, 'レポート一覧の取得に失敗しました')
  const data = reportListSchema.parse(json)
  return {
    reports: data.reports,
    total: data.count,
  }
}

export async function downloadReport(filename: string) {
  const response = await fetch(`${API_BASE}/api/reports/download/${encodeURIComponent(filename)}`)
  
  if (!response.ok) {
    throw new Error('ダウンロードに失敗しました')
  }
  
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

export async function deleteReport(filename: string) {
  const response = await fetch(`${API_BASE}/api/reports/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  })
  
  if (!response.ok) {
    throw new Error('削除に失敗しました')
  }
  
  return await response.json()
}
