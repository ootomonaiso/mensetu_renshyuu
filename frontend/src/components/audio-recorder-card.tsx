import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { useMediaRecorder } from '@/hooks/use-media-recorder'
import { uploadAudioFile } from '@/lib/api'
import { createFileName, formatDuration } from '@/lib/utils'
import { useSessionStore } from '@/store/session-store'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'

const RecordingStatusLabel = ({ status }: { status: string }) => {
  const variants: Record<string, { label: string; variant: 'default' | 'secondary' | 'outline' | 'destructive' }> = {
    idle: { label: '待機中', variant: 'secondary' },
    requesting: { label: 'デバイス確認中', variant: 'secondary' },
    recording: { label: '録音中', variant: 'default' },
    stopped: { label: '録音完了', variant: 'outline' },
    error: { label: 'エラー', variant: 'destructive' },
  }

  const state = variants[status] ?? variants.idle
  return <Badge variant={state.variant}>{state.label}</Badge>
}

export const AudioRecorderCard = () => {
  const recorder = useMediaRecorder({ audio: true, video: false, mimeType: 'audio/webm;codecs=opus' })
  const summary = useSessionStore((state) => state.audioSummary)
  const setSummary = useSessionStore((state) => state.setAudioSummary)

  const [autoStopMinutes, setAutoStopMinutes] = useState(5)
  const [autoUpload, setAutoUpload] = useState(true)
  const [countdown, setCountdown] = useState<number | null>(null)

  const analyzeMutation = useMutation({
    mutationFn: async () => {
      if (!recorder.blob) {
        throw new Error('録音データがありません')
      }
      const filename = createFileName('audio')
      return uploadAudioFile(recorder.blob, filename)
    },
    onSuccess: (data) => {
      setSummary(data)
    },
  })

  // 自動停止タイマー
  useEffect(() => {
    if (recorder.isRecording && autoStopMinutes > 0) {
      const timer = setTimeout(() => {
        recorder.stop()
      }, autoStopMinutes * 60 * 1000)
      return () => clearTimeout(timer)
    }
  }, [recorder.isRecording, autoStopMinutes, recorder])

  // 自動アップロード
  useEffect(() => {
    if (autoUpload && recorder.blob && recorder.status === 'stopped' && !analyzeMutation.isPending) {
      analyzeMutation.mutate()
    }
  }, [recorder.blob, recorder.status, autoUpload, analyzeMutation])

  // カウントダウン機能
  const startWithCountdown = () => {
    setCountdown(3)
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(interval)
          recorder.start()
          return null
        }
        return prev - 1
      })
    }, 1000)
  }

  const isUploading = analyzeMutation.isPending

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle>音声録音とアップロード</CardTitle>
            <CardDescription>マイク入力を録音し、FastAPI バックエンドへ送信します。</CardDescription>
          </div>
          <RecordingStatusLabel status={recorder.status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {countdown !== null && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="text-9xl font-bold text-white">{countdown}</div>
          </div>
        )}

        <div className="space-y-3 rounded-lg border bg-muted/20 p-4">
          <div className="flex items-center justify-between">
            <label htmlFor="autoStopMinutes" className="text-sm font-medium">
              自動停止時間（分）
            </label>
            <Input
              id="autoStopMinutes"
              type="number"
              min={1}
              max={60}
              value={autoStopMinutes}
              onChange={(e) => setAutoStopMinutes(Number(e.target.value))}
              className="w-20 text-right"
              disabled={recorder.isRecording}
            />
          </div>
          <div className="flex items-center justify-between">
            <label htmlFor="autoUpload" className="text-sm font-medium">
              録音後に自動アップロード
            </label>
            <input
              id="autoUpload"
              type="checkbox"
              checked={autoUpload}
              onChange={(e) => setAutoUpload(e.target.checked)}
              className="h-4 w-4"
              disabled={recorder.isRecording}
            />
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-4">
          <p className="text-sm text-muted-foreground">録音時間</p>
          <p className="text-3xl font-bold tracking-tight">{formatDuration(recorder.duration)}</p>
          {autoStopMinutes > 0 && recorder.isRecording && (
            <p className="mt-1 text-xs text-muted-foreground">
              {autoStopMinutes}分後に自動停止します
            </p>
          )}
          {recorder.error && <p className="mt-2 text-sm text-destructive">{recorder.error}</p>}
        </div>

        <div className="flex flex-wrap gap-3">
          <Button onClick={startWithCountdown} disabled={recorder.isRecording || recorder.status === 'requesting'}>
            🎙️ 録音開始（3秒カウントダウン）
          </Button>
          <Button onClick={recorder.start} disabled={recorder.isRecording || recorder.status === 'requesting'} variant="outline">
            録音開始（即時）
          </Button>
          <Button variant="secondary" onClick={recorder.stop} disabled={!recorder.isRecording}>
            ⏹️ 録音停止
          </Button>
          <Button variant="ghost" onClick={recorder.reset} disabled={recorder.status === 'idle'}>
            ♻️ リセット
          </Button>
        </div>

        <div className="rounded-lg bg-muted/40 p-4 text-sm text-muted-foreground">
          WebM (Opus) 形式で録音します。
          {autoUpload ? '録音停止後に自動で分析が開始されます。' : '録音後に「AI 分析を実行」ボタンを押してください。'}
        </div>

        {!autoUpload && (
          <div className="space-y-3">
            <Button
              className="w-full"
              onClick={() => analyzeMutation.mutate()}
              disabled={!recorder.blob || isUploading}
            >
              {isUploading ? 'アップロード中...' : 'AI 分析を実行'}
            </Button>
            {analyzeMutation.error && (
              <p className="text-sm text-destructive">{(analyzeMutation.error as Error).message}</p>
            )}
          </div>
        )}

        {autoUpload && isUploading && (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-sm font-medium text-blue-900">AI 分析中...</p>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-blue-200">
              <div className="h-full animate-pulse bg-blue-600" style={{ width: '100%' }} />
            </div>
          </div>
        )}

        {analyzeMutation.error && autoUpload && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm font-medium text-red-900">エラー</p>
            <p className="text-sm text-red-700">{(analyzeMutation.error as Error).message}</p>
          </div>
        )}

        {summary && (
          <div className="space-y-4 rounded-lg border bg-white/40 p-4">
            <div>
              <p className="text-sm font-semibold text-muted-foreground">最新レポート</p>
              <p className="text-lg font-bold">話速: {summary.summary.speech_rate.toLocaleString('ja-JP')} 文字/分</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">自信度</p>
              <Progress value={summary.summary.confidence_score} />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">緊張度</p>
              <Progress value={summary.summary.nervousness_score} />
            </div>
            <div className="flex flex-wrap gap-2 text-sm">
              {summary.summary.keywords.map((keyword) => (
                <Badge key={keyword} variant="outline">
                  {keyword}
                </Badge>
              ))}
            </div>
            <a
              href={summary.report_url}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-semibold text-primary underline-offset-4 hover:underline"
            >
              📄 レポートを開く
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
