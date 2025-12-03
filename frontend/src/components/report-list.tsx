import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Download, Trash2 } from 'lucide-react'

import { fetchReports, downloadReport, deleteReport } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useState } from 'react'

const formatDate = (value: string) => {
  const date = new Date(value)
  return date.toLocaleString('ja-JP', { hour12: false })
}

export const ReportList = () => {
  const queryClient = useQueryClient()
  const [downloading, setDownloading] = useState<string | null>(null)
  
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['reports'],
    queryFn: fetchReports,
    refetchInterval: 60_000,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
  })

  const handleDownload = async (filename: string) => {
    try {
      setDownloading(filename)
      await downloadReport(filename)
      // ダウンロード後、サーバー側で削除されるのでリストを更新
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['reports'] })
      }, 500)
    } catch (error) {
      console.error('ダウンロードエラー:', error)
      alert('ダウンロードに失敗しました')
    } finally {
      setDownloading(null)
    }
  }

  const handleDelete = async (filename: string) => {
    if (!confirm(`レポート "${filename}" を削除しますか？`)) return
    deleteMutation.mutate(filename)
  }

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div>
          <CardTitle>レポート一覧</CardTitle>
          <CardDescription>生成済みの Markdown レポートをダウンロードできます。</CardDescription>
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
                <div className="flex flex-col gap-2">
                  <div className="flex items-start justify-between">
                    <div className="flex flex-col gap-1 text-sm flex-1">
                      <span className="font-semibold">{report.filename}</span>
                      <span className="text-muted-foreground text-xs">
                        作成日時: {formatDate(report.created_at)}
                      </span>
                      <span className="text-muted-foreground text-xs">
                        サイズ: {(report.size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 mt-2">
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => handleDownload(report.filename)}
                      disabled={downloading === report.filename || deleteMutation.isPending}
                      className="flex items-center gap-2"
                    >
                      {downloading === report.filename ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          ダウンロード中...
                        </>
                      ) : (
                        <>
                          <Download className="h-4 w-4" />
                          ダウンロード
                        </>
                      )}
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(report.url, '_blank')}
                      disabled={downloading === report.filename || deleteMutation.isPending}
                    >
                      プレビュー
                    </Button>
                    
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(report.filename)}
                      disabled={downloading === report.filename || deleteMutation.isPending}
                      className="flex items-center gap-2"
                    >
                      {deleteMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
