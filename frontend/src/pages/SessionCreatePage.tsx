import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createSession, type SessionType } from '../api/sessions'
import { getUserProfile, type UserProfile } from '../api/profiles'
import { useAuthStore } from '../stores/authStore'

const SESSION_TYPE_OPTIONS: Array<{ value: SessionType; label: string; description: string }> = [
  { value: 'practice', label: '練習', description: '通常の面接練習セッション' },
  { value: 'mock', label: '模擬', description: '教師と模擬面接を行うセッション' },
  { value: 'real', label: '本番', description: '実際の面接を記録用に管理するセッション' },
]

export function SessionCreatePage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(true)

  const [title, setTitle] = useState('')
  const [sessionType, setSessionType] = useState<SessionType>('practice')
  const [targetCompany, setTargetCompany] = useState('')
  const [targetPosition, setTargetPosition] = useState('')
  const [studentId, setStudentId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchProfile() {
      if (!user) {
        setLoadingProfile(false)
        return
      }
      try {
        const res = await getUserProfile(user.id)
        setProfile(res)
      } catch (err) {
        setProfileError('プロフィール情報の取得に失敗しました')
      } finally {
        setLoadingProfile(false)
      }
    }

    fetchProfile()
  }, [user])

  const isTeacherLike = useMemo(() => {
    if (!profile) return false
    return profile.role === 'teacher' || profile.role === 'admin'
  }, [profile])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)

    if (!title.trim()) {
      setError('タイトルを入力してください')
      return
    }

    if (isTeacherLike && !studentId.trim()) {
      setError('担当する生徒のIDを入力してください')
      return
    }

    setSubmitting(true)
    try {
      const payload: Parameters<typeof createSession>[0] = {
        title: title.trim(),
        session_type: sessionType,
      }

      if (targetCompany.trim()) {
        payload.target_company = targetCompany.trim()
      }
      if (targetPosition.trim()) {
        payload.target_position = targetPosition.trim()
      }
      if (isTeacherLike) {
        payload.student_id = studentId.trim()
      }

      const session = await createSession(payload)
      navigate(`/sessions/${session.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'セッション作成に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  if (loadingProfile) {
    return <div className="min-h-screen flex items-center justify-center text-gray-500">読み込み中...</div>
  }

  if (profileError) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center space-y-4 text-center">
        <p className="text-red-600">{profileError}</p>
        <Link to="/dashboard" className="text-blue-600 hover:text-blue-500">
          ダッシュボードに戻る
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto py-8 px-4">
        <div className="mb-6">
          <p className="text-sm text-gray-500">新規セッション</p>
          <h1 className="text-2xl font-bold text-gray-900">面接練習を登録する</h1>
          <p className="text-sm text-gray-600 mt-2">
            Markdown ログ生成用のセッションを作成します。録音ファイルは扱わず、ハイライトやメモを元に後から処理を実行します。
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
          {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">セッションタイトル *</label>
            <input
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="block w-full rounded-md border border-gray-300 px-3 py-2"
              placeholder="例: 3年A組 模擬面接 第1回"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">セッション種別 *</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {SESSION_TYPE_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  className={`border rounded-md p-3 cursor-pointer ${
                    sessionType === option.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <input
                    type="radio"
                    name="session_type"
                    value={option.value}
                    checked={sessionType === option.value}
                    onChange={() => setSessionType(option.value)}
                    className="sr-only"
                  />
                  <div className="font-medium text-gray-900">{option.label}</div>
                  <div className="text-xs text-gray-500 mt-1">{option.description}</div>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">対象企業</label>
              <input
                type="text"
                value={targetCompany}
                onChange={(event) => setTargetCompany(event.target.value)}
                className="block w-full rounded-md border border-gray-300 px-3 py-2"
                placeholder="例: 株式会社Example"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">対象職種</label>
              <input
                type="text"
                value={targetPosition}
                onChange={(event) => setTargetPosition(event.target.value)}
                className="block w-full rounded-md border border-gray-300 px-3 py-2"
                placeholder="例: 営業職"
              />
            </div>
          </div>

          {isTeacherLike && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">生徒ID *</label>
              <input
                type="text"
                value={studentId}
                onChange={(event) => setStudentId(event.target.value)}
                className="block w-full rounded-md border border-gray-300 px-3 py-2"
                placeholder="Supabase の生徒ユーザーID"
              />
              <p className="text-xs text-gray-500 mt-1">担当する生徒のユーザーIDを入力してください。</p>
            </div>
          )}

          <div className="flex items-center justify-end space-x-3">
            <Link
              to="/sessions"
              className="px-4 py-2 rounded-md border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              キャンセル
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-md bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-60"
            >
              {submitting ? '作成中...' : 'セッションを作成'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
