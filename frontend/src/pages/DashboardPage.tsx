import { useEffect, useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useNavigate, Link } from 'react-router-dom'
import { getUserProfile, getStudentProfile } from '../api/profiles'
import type { UserProfile, StudentProfile } from '../api/profiles'

export function DashboardPage() {
  const { user, signOut } = useAuthStore()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [studentProfile, setStudentProfile] = useState<StudentProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadProfile() {
      if (!user) return

      try {
        const userProfile = await getUserProfile(user.id)
        setProfile(userProfile)

        if (userProfile?.role === 'student') {
          const stuProfile = await getStudentProfile(user.id)
          setStudentProfile(stuProfile)
        }
      } catch (error) {
        console.error('プロフィール取得エラー:', error)
      } finally {
        setLoading(false)
      }
    }

    loadProfile()
  }, [user])

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">読み込み中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-bold text-gray-900">圧勝面接練習</h1>
              <div className="hidden md:flex space-x-4">
                <Link
                  to="/dashboard"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-900 hover:bg-gray-100"
                >
                  ダッシュボード
                </Link>
                <Link
                  to="/sessions"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
                >
                  セッション一覧
                </Link>
                <Link
                  to="/profile"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
                >
                  プロフィール
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                {profile?.name || user?.email}
              </span>
              <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                {profile?.role === 'student' ? '生徒' : '教師'}
              </span>
              <button
                onClick={handleSignOut}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
              >
                ログアウト
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* ウェルカムカード */}
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              ようこそ、{profile?.name || user?.email} さん
            </h2>
            <p className="text-gray-600">
              {profile?.role === 'student'
                ? '面接練習を始めましょう。セッションを作成して録音を開始できます。'
                : '生徒の面接練習をサポートしましょう。'}
            </p>
          </div>

          {/* 生徒の場合: プロフィール概要 */}
          {profile?.role === 'student' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">志望情報</h3>
                {studentProfile ? (
                  <div className="space-y-2">
                    <p className="text-sm">
                      <span className="font-medium">業界:</span>{' '}
                      {studentProfile.target_industry || '未設定'}
                    </p>
                    <p className="text-sm">
                      <span className="font-medium">企業:</span>{' '}
                      {studentProfile.target_company || '未設定'}
                    </p>
                    <p className="text-sm">
                      <span className="font-medium">職種:</span>{' '}
                      {studentProfile.target_position || '未設定'}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    プロフィールを設定してください
                  </p>
                )}
                <Link
                  to="/profile"
                  className="mt-4 inline-block text-sm text-blue-600 hover:text-blue-500"
                >
                  プロフィールを編集 →
                </Link>
              </div>

              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">練習状況</h3>
                <div className="space-y-2">
                  <p className="text-sm">
                    <span className="font-medium">総練習回数:</span> 0回
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">平均スコア:</span> --点
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">最終練習日:</span> --
                  </p>
                </div>
                <Link
                  to="/sessions"
                  className="mt-4 inline-block text-sm text-blue-600 hover:text-blue-500"
                >
                  セッション一覧を見る →
                </Link>
              </div>
            </div>
          )}

          {/* クイックアクション */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">クイックアクション</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link
                to="/sessions/new"
                className="flex items-center justify-center px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                新しいセッションを作成
              </Link>
              <Link
                to="/sessions"
                className="flex items-center justify-center px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                過去のセッションを見る
              </Link>
              <Link
                to="/profile"
                className="flex items-center justify-center px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                プロフィールを編集
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
