import { useMutation } from '@tanstack/react-query'

import { useMediaRecorder } from '@/hooks/use-media-recorder'
import { uploadVideoFile } from '@/lib/api'
import { createFileName, formatDuration } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useSessionStore } from '@/store/session-store'

export const VideoRecorderCard = () => {
  const recorder = useMediaRecorder({ audio: true, video: true, mimeType: 'video/webm;codecs=vp9,opus' })
  const result = useSessionStore((state) => state.videoResult)
  const setResult = useSessionStore((state) => state.setVideoResult)

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
        <div className="rounded-lg border border-dashed p-4">
          <p className="text-sm text-muted-foreground">録画時間</p>
          <p className="text-3xl font-bold tracking-tight">{formatDuration(recorder.duration)}</p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button onClick={recorder.start} disabled={recorder.isRecording}>
            🎥 録画開始
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

        <div className="space-y-2">
          <Button className="w-full" onClick={() => uploadMutation.mutate()} disabled={!recorder.blob || uploadMutation.isPending}>
            {uploadMutation.isPending ? 'アップロード中...' : '動画をアップロード'}
          </Button>
          {uploadMutation.error && (
            <p className="text-sm text-destructive">{(uploadMutation.error as Error).message}</p>
          )}
        </div>

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
