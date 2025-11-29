import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { deleteSession, getSession, requestProcessing, type SessionDetail } from '../api/sessions'

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const loadSession = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const detail = await getSession(sessionId)
      setSession(detail)
    } catch (err) {
      setError(err instanceof Error ? err.message : '詳細取得中にエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    loadSession()
  }, [loadSession])

  const handleProcessingRequest = async () => {
    if (!sessionId) return
    setActionMessage(null)
    try {
      const job = await requestProcessing(sessionId, {
        highlights: ['自動処理をリクエストしました'],
        notes: 'ダッシュボードから手動実行',
      })
      setActionMessage(`処理キューに登録しました (task: ${job.task_id})`)
      await loadSession()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : '処理キュー投入に失敗しました')
    }
  }

  const handleDelete = async () => {
    if (!sessionId) return
    if (!window.confirm('このセッションを削除しますか？')) return
    try {
      await deleteSession(sessionId)
      navigate('/sessions')
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : '削除に失敗しました')
    }
  }

  if (!sessionId) {
    return <div className="p-6">無効なセッションIDです。</div>
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-gray-500">読み込み中...</div>
  }

  if (error || !session) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center space-y-4">
        <div className="text-red-600">{error || 'セッション情報を取得できませんでした。'}</div>
        <Link to="/sessions" className="text-blue-600 hover:text-blue-500">
          セッション一覧に戻る
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">セッション詳細</p>
            <h1 className="text-2xl font-bold text-gray-900">{session.title}</h1>
          </div>
          <div className="space-x-3 text-sm">
            <Link
              to={`/sessions/${sessionId}/record`}
              className="px-4 py-2 rounded-md bg-green-600 text-white font-medium hover:bg-green-700"
            >
              🎥 面接録画開始
            </Link>
            <button
              onClick={handleProcessingRequest}
              className="px-4 py-2 rounded-md bg-blue-600 text-white font-medium hover:bg-blue-700"
            >
              Markdown処理を実行
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 rounded-md border border-red-200 text-red-600 font-medium hover:bg-red-50"
            >
              セッション削除
            </button>
            <Link
              to="/sessions"
              className="px-4 py-2 rounded-md border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
            >
              一覧に戻る
            </Link>
          </div>
        </div>

        {actionMessage && <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-700">{actionMessage}</div>}

        <section className="bg-white rounded-lg shadow p-4 space-y-2 text-sm text-gray-700">
          <p>
            <span className="font-medium">セッション種別:</span> {session.session_type}
          </p>
          <p>
            <span className="font-medium">対象企業:</span> {session.target_company || '未設定'}
          </p>
          <p>
            <span className="font-medium">対象職種:</span> {session.target_position || '未設定'}
          </p>
          <p>
            <span className="font-medium">ステータス:</span> {session.status}
          </p>
          <p>
            <span className="font-medium">作成日:</span> {new Date(session.created_at).toLocaleString('ja-JP')}
          </p>
          {session.updated_at && (
            <p>
              <span className="font-medium">最終更新:</span> {new Date(session.updated_at).toLocaleString('ja-JP')}
            </p>
          )}
        </section>

        {session.transcript ? (
          <section className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Markdownログ</h2>
              <button onClick={loadSession} className="text-sm text-blue-600 hover:text-blue-500">
                再読み込み
              </button>
            </div>
            <pre className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 rounded-md p-4 overflow-x-auto">
              {session.transcript}
            </pre>
          </section>
        ) : (
          <section className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
            まだ Markdown ログが生成されていません。
          </section>
        )}
      </div>
    </div>
  )
}
