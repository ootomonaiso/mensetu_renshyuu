import { useEffect, useRef, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

interface AnalysisResult {
  type: string
  audio_level?: number
  transcription?: string
  emotion?: {
    confidence: number
    calmness: number
  }
  posture?: {
    score: number
    feedback: string
  }
  eye_contact?: {
    score: number
    feedback: string
  }
  report_url?: string
  report_path?: string
  message?: string
}

export const LiveAnalysisCard = () => {
  const [isActive, setIsActive] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [transcription, setTranscription] = useState('')
  const [emotion, setEmotion] = useState({ confidence: 0, calmness: 0 })
  const [posture, setPosture] = useState({ score: 0, feedback: '' })
  const [eyeContact, setEyeContact] = useState({ score: 0, feedback: '' })
  const [reportUrl, setReportUrl] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)

  const startAnalysis = async () => {
    try {
      // カメラ+マイク取得
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: { echoCancellation: true, noiseSuppression: true }
      })
      
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }

      // WebSocket 接続
      const sessionId = `session_${Date.now()}`
      const ws = new WebSocket(`ws://localhost:8000/ws/live-analysis/${sessionId}`)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket接続成功')
        setIsActive(true)
      }

      ws.onmessage = (event) => {
        const data: AnalysisResult = JSON.parse(event.data)
        
        if (data.type === 'audio_analysis') {
          if (data.audio_level !== undefined) setAudioLevel(data.audio_level)
          if (data.transcription) setTranscription((prev) => prev + ' ' + data.transcription)
          if (data.emotion) setEmotion(data.emotion)
        } else if (data.type === 'video_analysis') {
          if (data.posture) setPosture(data.posture)
          if (data.eye_contact) setEyeContact(data.eye_contact)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocketエラー:', error)
      }

      // 音声ストリーム処理
      const audioContext = new AudioContext({ sampleRate: 16000 })
      audioContextRef.current = audioContext
      const source = audioContext.createMediaStreamSource(stream)
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      processorRef.current = processor

      processor.onaudioprocess = (e) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) return
        
        const inputData = e.inputBuffer.getChannelData(0)
        const int16Array = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          int16Array[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768))
        }
        
        // Base64エンコードして送信
        const base64 = btoa(String.fromCharCode(...new Uint8Array(int16Array.buffer)))
        ws.send(JSON.stringify({
          type: 'audio',
          data: base64
        }))
      }

      source.connect(processor)
      processor.connect(audioContext.destination)

      // 映像フレーム送信（1秒ごと）
      const videoInterval = setInterval(() => {
        if (!canvasRef.current || !videoRef.current || !ws || ws.readyState !== WebSocket.OPEN) return
        
        const canvas = canvasRef.current
        const video = videoRef.current
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        
        const ctx = canvas.getContext('2d')
        if (!ctx) return
        
        ctx.drawImage(video, 0, 0)
        canvas.toBlob((blob) => {
          if (!blob) return
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64 = (reader.result as string).split(',')[1]
            ws.send(JSON.stringify({
              type: 'video',
              data: base64
            }))
          }
          reader.readAsDataURL(blob)
        }, 'image/jpeg', 0.7)
      }, 1000)

      // クリーンアップ関数
      return () => clearInterval(videoInterval)

    } catch (error) {
      console.error('分析開始エラー:', error)
      alert('カメラ・マイクへのアクセスが拒否されました')
    }
  }

  const stopAnalysis = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'stop' }))
      wsRef.current.close()
    }
    
    if (processorRef.current) {
      processorRef.current.disconnect()
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
    
    setIsActive(false)
  }

  useEffect(() => {
    return () => {
      stopAnalysis()
    }
  }, [])

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>🎬 リアルタイム面接分析</CardTitle>
            <CardDescription>カメラと音声をリアルタイムで分析し、フィードバックを表示します</CardDescription>
          </div>
          <Badge variant={isActive ? 'default' : 'secondary'}>
            {isActive ? '分析中' : '待機中'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative overflow-hidden rounded-lg border bg-black">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full"
          />
          <canvas ref={canvasRef} className="hidden" />
          
          {/* オーバーレイ表示 */}
          {isActive && (
            <div className="absolute bottom-4 left-4 right-4 space-y-2">
              <div className="rounded bg-black/70 p-3 text-white backdrop-blur-sm">
                <p className="text-xs font-semibold">音声レベル</p>
                <div className="mt-1">
                  <Progress value={audioLevel} />
                </div>
              </div>
              
              <div className="rounded bg-black/70 p-3 text-white backdrop-blur-sm">
                <p className="text-xs font-semibold">感情スコア</p>
                <div className="mt-1 flex gap-4 text-xs">
                  <span>自信: {emotion.confidence}%</span>
                  <span>落ち着き: {emotion.calmness}%</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-3">
          {!isActive ? (
            <Button onClick={startAnalysis} className="w-full">
              🎬 リアルタイム分析を開始
            </Button>
          ) : (
            <Button onClick={stopAnalysis} variant="destructive" className="w-full">
              ⏹️ 分析を停止
            </Button>
          )}
        </div>

        {isActive && (
          <div className="space-y-3">
            <div className="rounded-lg border bg-muted/20 p-3">
              <p className="text-xs font-semibold text-muted-foreground">文字起こし</p>
              <p className="mt-1 text-sm">{transcription || '（音声を待機中...）'}</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border bg-blue-50 p-3">
                <p className="text-xs font-semibold text-blue-900">姿勢</p>
                <p className="text-2xl font-bold text-blue-700">{posture.score}%</p>
                <p className="text-xs text-blue-600">{posture.feedback}</p>
              </div>
              
              <div className="rounded-lg border bg-green-50 p-3">
                <p className="text-xs font-semibold text-green-900">視線</p>
                <p className="text-2xl font-bold text-green-700">{eyeContact.score}%</p>
                <p className="text-xs text-green-600">{eyeContact.feedback}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
