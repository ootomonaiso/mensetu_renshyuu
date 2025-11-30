import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'

import { fetchReports } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const formatDate = (value: string) => {
  const date = new Date(value)
  return date.toLocaleString('ja-JP', { hour12: false })
}

export const ReportList = () => {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['reports'],
    queryFn: fetchReports,
    refetchInterval: 60_000,
  })

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div>
          <CardTitle>レポート一覧</CardTitle>
          <CardDescription>生成済みの Markdown レポートを閲覧できます。</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
          {isFetching ? '更新中...' : '再読み込み'}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            読み込み中...
          </div>
        )}

        {isError && <p className="text-sm text-destructive">レポートの取得に失敗しました。</p>}

        {!isLoading && data && data.total === 0 && (
          <p className="text-sm text-muted-foreground">まだレポートはありません。録音をアップロードすると自動生成されます。</p>
        )}

        {!isLoading && data && data.total > 0 && (
          <div className="space-y-4">
            {data.reports.map((report) => (
              <div key={report.filename} className="rounded-md border p-4">
                <div className="flex flex-col gap-1 text-sm">
                  <span className="font-semibold">{report.filename}</span>
                  <span className="text-muted-foreground">{formatDate(report.created_at)}</span>
                </div>
                <Button asChild className="mt-3" variant="secondary" size="sm">
                  <a href={report.url} target="_blank" rel="noreferrer">
                    📄 レポートを開く
                  </a>
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
