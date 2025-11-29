import { supabase } from './supabase'

const apiBase = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
const API_ROOT = `${apiBase}/api/v1`

interface ApiErrorDetail {
  detail?: string
  message?: string
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const {
    data: { session },
  } = await supabase.auth.getSession()

  const headers = new Headers({
    Accept: 'application/json',
    'Content-Type': 'application/json',
  })

  if (init.headers) {
    new Headers(init.headers).forEach((value, key) => headers.set(key, value))
  }

  if (session?.access_token) {
    headers.set('Authorization', `Bearer ${session.access_token}`)
  }

  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let message = response.statusText
    try {
      const body = (await response.json()) as ApiErrorDetail
      message = body.detail || body.message || message
    } catch (error) {
      // ignore JSON parse failures and fall back to status text
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return null as T
  }

  return (await response.json()) as T
}
