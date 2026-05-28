import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/loading"
import { SimplePieChart } from "@/charts/pie-chart"
import { SimpleLineChart } from "@/charts/line-chart"
import { api } from "@/services/api"
import type { SentimentData } from "@/types"

export function SentimentPage() {
  const [data, setData] = useState<SentimentData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.sentiment().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  if (!data) return <p className="text-center text-[var(--color-muted-foreground)]">No sentiment data</p>

  const pie = Object.entries(data.distribution).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Sentiment Analysis</h1>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Distribution</CardTitle>
          <SimplePieChart data={pie} height={300} />
        </Card>
        <Card>
          <CardTitle>Metrics</CardTitle>
          <div className="space-y-3 p-2">
            <div className="flex justify-between rounded-lg bg-[var(--color-muted)] p-3">
              <span className="text-sm text-[var(--color-muted-foreground)]">Average Compound Score</span>
              <span className="font-bold">{data.avg_compound.toFixed(4)}</span>
            </div>
            {Object.entries(data.distribution).map(([k, v]) => (
              <div key={k} className="flex justify-between rounded-lg bg-[var(--color-muted)] p-3">
                <span className="text-sm capitalize text-[var(--color-muted-foreground)]">{k}</span>
                <span className="font-bold">{v}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
