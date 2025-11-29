import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import type { SessionDetail } from '../api/sessions'
import { getSession } from '../api/sessions'

export function SessionRecordPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [error, setError] = useState<string | null>(null)
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const videoChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!sessionId) return
    
    async function loadSession() {
      try {
        const data = await getSession(sessionId!)
        setSession(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'セッション読み込みエラー')
      }
    }
    
    loadSession()
  }, [sessionId])

  const startRecording = useCallback(async () => {
    try {
      // 音声とビデオストリームを取得
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
      })
      
      streamRef.current = stream
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      
      // 音声のみのMediaRecorder（音声分析用）
      const audioStream = new MediaStream(stream.getAudioTracks())
      const audioRecorder = new MediaRecorder(audioStream, {
        mimeType: 'audio/webm;codecs=opus',
      })
      
      audioRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      // ビデオ録画（任意）
      const videoRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp9,opus',
      })
      
      videoRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          videoChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorderRef.current = audioRecorder
      audioRecorder.start(1000) // 1秒ごとにチャンク
      videoRecorder.start(1000)
      
      setIsRecording(true)
      setRecordingTime(0)
      
      // タイマー開始
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1)
      }, 1000)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'デバイスアクセスエラー')
    }
  }, [])

  const stopRecording = useCallback(async () => {
    if (!mediaRecorderRef.current || !streamRef.current) return
    
    mediaRecorderRef.current.stop()
    
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }
    
    // ストリーム停止
    streamRef.current.getTracks().forEach((track) => track.stop())
    
    setIsRecording(false)
    
    // 録音データをBlobに変換
    await new Promise((resolve) => setTimeout(resolve, 500)) // データ収集待機
    
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
    const videoBlob = new Blob(videoChunksRef.current, { type: 'video/webm' })
    
    // バックエンドに送信
    await uploadRecording(audioBlob, videoBlob)
    
  }, [])

  const uploadRecording = async (audioBlob: Blob, videoBlob: Blob) => {
    if (!sessionId) return
    
    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'interview.webm')
      formData.append('video', videoBlob, 'interview_video.webm')
      formData.append('duration', recordingTime.toString())
      
      const response = await fetch(`/api/v1/sessions/${sessionId}/upload`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'アップロード失敗' }))
        throw new Error(errorData.detail || 'アップロード失敗')
      }
      
      const result = await response.json()
      console.log('アップロード成功:', result)
      
      // 処理開始メッセージ
      alert(`✅ ${result.message}\n処理が完了したら詳細ページで確認できます。`)
      
      // 処理開始
      navigate(`/sessions/${sessionId}`)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'アップロードエラー')
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => navigate(`/sessions/${sessionId}`)}
            className="px-4 py-2 bg-gray-600 text-white rounded-md"
          >
            戻る
          </button>
        </div>
      </div>
    )
  }

  if (!session) {
    return <div className="min-h-screen flex items-center justify-center">読み込み中...</div>
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-6xl mx-auto py-8 px-4">
        {/* ヘッダー */}
        <div className="mb-6 text-white">
          <h1 className="text-2xl font-bold">{session.title}</h1>
          <p className="text-sm text-gray-400">
            {session.target_company} - {session.target_position}
          </p>
        </div>

        {/* ビデオプレビュー */}
        <div className="relative bg-black rounded-lg overflow-hidden mb-6" style={{ aspectRatio: '16/9' }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          
          {isRecording && (
            <div className="absolute top-4 left-4 flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
              <span className="text-white font-mono text-lg">{formatTime(recordingTime)}</span>
            </div>
          )}
        </div>

        {/* コントロール */}
        <div className="flex items-center justify-center space-x-4">
          {!isRecording ? (
            <>
              <button
                onClick={startRecording}
                className="px-8 py-4 bg-red-600 text-white rounded-full text-lg font-semibold hover:bg-red-700 transition"
              >
                🎙️ 録画開始
              </button>
              <button
                onClick={() => navigate(`/sessions/${sessionId}`)}
                className="px-6 py-4 bg-gray-700 text-white rounded-full hover:bg-gray-600 transition"
              >
                キャンセル
              </button>
            </>
          ) : (
            <button
              onClick={stopRecording}
              className="px-8 py-4 bg-blue-600 text-white rounded-full text-lg font-semibold hover:bg-blue-700 transition"
            >
              ⏹️ 録画停止・分析開始
            </button>
          )}
        </div>

        {/* 注意事項 */}
        <div className="mt-8 bg-yellow-900/20 border border-yellow-600/50 rounded-lg p-4 text-yellow-100 text-sm">
          <p className="font-semibold mb-2">📝 録画の注意事項</p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>音声は自動で文字起こしされ、AI分析が行われます</li>
            <li>カメラ映像は姿勢・表情分析に使用されます（保存されません）</li>
            <li>録画停止後、自動で分析が開始されます（数分かかる場合があります）</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
