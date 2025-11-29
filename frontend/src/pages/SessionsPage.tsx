import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { listSessions, type SessionStatus, type SessionSummary } from '../api/sessions'

const STATUS_LABELS: Record<SessionStatus, string> = {
  recording: '録音中',
  processing: '処理中',
  completed: '完了',
  failed: '失敗',
}

export function SessionsPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [statusFilter, setStatusFilter] = useState<SessionStatus | 'all'>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSessions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await listSessions(statusFilter === 'all' ? undefined : { status: statusFilter })
      setSessions(response.sessions)
    } catch (err) {
      setError(err instanceof Error ? err.message : '一覧取得中にエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const statusOptions = useMemo(() => Object.entries(STATUS_LABELS), [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-8 px-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">セッション一覧</h1>
            <p className="text-sm text-gray-500">録音済みの面接練習を確認し、処理状況を追跡できます。</p>
          </div>
          <div className="flex items-center space-x-3">
            <Link
              to="/sessions/new"
              className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
            >
              新しいセッション
            </Link>
            <button
              onClick={loadSessions}
              className="px-4 py-2 rounded-md border border-gray-300 text-sm font-medium bg-white hover:bg-gray-50"
            >
              再読み込み
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">ステータス</label>
          <select
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as SessionStatus | 'all')}
          >
            <option value="all">すべて</option>
            {statusOptions.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}

        {loading ? (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">読み込み中...</div>
        ) : sessions.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">表示できるセッションがありません。</div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">タイトル</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">区分</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ターゲット</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ステータス</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">作成日</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {sessions.map((session) => (
                  <tr key={session.id}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{session.title}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{session.session_type}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {session.target_company || '--'} / {session.target_position || '--'}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-gray-100 text-gray-800">
                        {STATUS_LABELS[session.status]}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(session.created_at).toLocaleString('ja-JP')}
                    </td>
                    <td className="px-4 py-3 text-right text-sm">
                      <Link to={`/sessions/${session.id}`} className="text-blue-600 hover:text-blue-500">
                        詳細を見る →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
