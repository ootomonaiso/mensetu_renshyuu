import { AudioRecorderCard } from '@/components/audio-recorder-card'
import { ReportList } from '@/components/report-list'
import { VideoRecorderCard } from '@/components/video-recorder-card'
import { LiveAnalysisCard } from '@/components/live-analysis-card'
import { Button } from '@/components/ui/button'

const App = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 pb-16">
      <header className="border-b bg-white/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-primary">圧勝面接 - 学校特化型面接支援</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 lg:text-4xl">音声・映像を一括記録し AI 分析</h1>
            <p className="mt-4 max-w-2xl text-base text-muted-foreground">
              マイクとカメラを使って模擬面接を記録し、そのまま FastAPI バックエンドへアップロードします。生成された Markdown レポートもここから確認できます。
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <a href="/static/realtime.html" target="_blank" rel="noreferrer">
                ⚡ リアルタイム練習を開く
              </a>
            </Button>
            <Button asChild variant="outline">
              <a href="/api/reports" target="_blank" rel="noreferrer">
                API レスポンスを確認
              </a>
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto mt-10 grid max-w-6xl gap-6 px-6 lg:grid-cols-2">
        <div className="lg:col-span-2">
          <LiveAnalysisCard />
        </div>
        <AudioRecorderCard />
        <VideoRecorderCard />
        <div className="lg:col-span-2">
          <ReportList />
        </div>
      </main>
    </div>
  )
}

export default App
