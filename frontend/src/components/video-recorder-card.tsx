import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { useMediaRecorder } from '@/hooks/use-media-recorder'
import { uploadVideoFile } from '@/lib/api'
import { createFileName, formatDuration } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useSessionStore } from '@/store/session-store'

export const VideoRecorderCard = () => {
  const recorder = useMediaRecorder({ audio: true, video: true, mimeType: 'video/webm;codecs=vp9,opus' })
  const result = useSessionStore((state) => state.videoResult)
  const setResult = useSessionStore((state) => state.setVideoResult)

  const [autoStopMinutes, setAutoStopMinutes] = useState(10)
  const [autoUpload, setAutoUpload] = useState(false)
  const [countdown, setCountdown] = useState<number | null>(null)

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!recorder.blob) {
        throw new Error('録画データがありません')
      }
      const filename = createFileName('video')
      return uploadVideoFile(recorder.blob, filename)
    },
    onSuccess: (data) => setResult(data),
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
    if (autoUpload && recorder.blob && recorder.status === 'stopped' && !uploadMutation.isPending) {
      uploadMutation.mutate()
    }
  }, [recorder.blob, recorder.status, autoUpload, uploadMutation])

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

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>カメラ録画</CardTitle>
            <CardDescription>面接風景を記録し、将来実装予定の動画分析 API へ送信します。</CardDescription>
          </div>
          <Badge variant={recorder.isRecording ? 'default' : 'secondary'}>
            {recorder.isRecording ? '録画中' : '待機中'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {countdown !== null && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="text-9xl font-bold text-white">{countdown}</div>
          </div>
        )}

        <div className="space-y-3 rounded-lg border bg-muted/20 p-4">
          <div className="flex items-center justify-between">
            <label htmlFor="videoAutoStopMinutes" className="text-sm font-medium">
              自動停止時間（分）
            </label>
            <Input
              id="videoAutoStopMinutes"
              type="number"
              min={1}
              max={120}
              value={autoStopMinutes}
              onChange={(e) => setAutoStopMinutes(Number(e.target.value))}
              className="w-20 text-right"
              disabled={recorder.isRecording}
            />
          </div>
          <div className="flex items-center justify-between">
            <label htmlFor="videoAutoUpload" className="text-sm font-medium">
              録画後に自動アップロード
            </label>
            <input
              id="videoAutoUpload"
              type="checkbox"
              checked={autoUpload}
              onChange={(e) => setAutoUpload(e.target.checked)}
              className="h-4 w-4"
              disabled={recorder.isRecording}
            />
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-4">
          <p className="text-sm text-muted-foreground">録画時間</p>
          <p className="text-3xl font-bold tracking-tight">{formatDuration(recorder.duration)}</p>
          {autoStopMinutes > 0 && recorder.isRecording && (
            <p className="mt-1 text-xs text-muted-foreground">
              {autoStopMinutes}分後に自動停止します
            </p>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <Button onClick={startWithCountdown} disabled={recorder.isRecording}>
            🎥 録画開始（3秒カウントダウン）
          </Button>
          <Button onClick={recorder.start} disabled={recorder.isRecording} variant="outline">
            録画開始（即時）
          </Button>
          <Button variant="secondary" onClick={recorder.stop} disabled={!recorder.isRecording}>
            ⏹️ 録画停止
          </Button>
          <Button variant="ghost" onClick={recorder.reset} disabled={recorder.status === 'idle'}>
            ♻️ リセット
          </Button>
        </div>

        {recorder.previewUrl ? (
          <video className="w-full rounded-lg border" controls src={recorder.previewUrl} />
        ) : (
          <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            プレビューはここに表示されます。
          </div>
        )}

        {!autoUpload && (
          <div className="space-y-2">
            <Button className="w-full" onClick={() => uploadMutation.mutate()} disabled={!recorder.blob || uploadMutation.isPending}>
              {uploadMutation.isPending ? 'アップロード中...' : '動画をアップロード'}
            </Button>
            {uploadMutation.error && (
              <p className="text-sm text-destructive">{(uploadMutation.error as Error).message}</p>
            )}
          </div>
        )}

        {autoUpload && uploadMutation.isPending && (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-sm font-medium text-blue-900">動画アップロード中...</p>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-blue-200">
              <div className="h-full animate-pulse bg-blue-600" style={{ width: '100%' }} />
            </div>
          </div>
        )}

        {recorder.previewUrl && (
          <Button asChild variant="outline" className="w-full">
            <a href={recorder.previewUrl} download={createFileName('video')}>
              💾 ローカルに保存
            </a>
          </Button>
        )}

        {result && (
          <div
            className={`rounded-lg border ${
              result.status === 'success'
                ? 'border-green-200 bg-green-50'
                : result.status === 'error'
                  ? 'border-red-200 bg-red-50'
                  : 'border-amber-200 bg-amber-50'
            } p-4 text-sm`}
          >
            <p className="font-semibold">動画アップロード結果: {result.status}</p>
            {result.message && <p className="mt-1 text-muted-foreground">{result.message}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
