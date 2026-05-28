import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { SimpleLineChart } from "@/charts/line-chart"
import { api } from "@/services/api"
import type { ViralityData } from "@/types"

export function ViralityPage() {
  const [data, setData] = useState<ViralityData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.virality().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  if (!data) return <p className="text-center text-[var(--color-muted-foreground)]">No virality data</p>

  return (
    <div className="space-y-4">
      <h1 className="flex items-center gap-2 text-xl font-bold">🔥 Virality Analysis</h1>

      <Card>
        <CardTitle>Score Distribution</CardTitle>
        <SimpleLineChart
          data={data.distribution.map((v, i) => ({ index: i, score: v }))}
          xKey="index"
          yKey="score"
          color="var(--color-accent)"
          height={300}
        />
      </Card>

      <div className="grid grid-cols-1 gap-3">
        <Card>
          <CardTitle>Most Viral Articles</CardTitle>
          <div className="space-y-2">
            {data.top_viral.map((a, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-[var(--color-muted)] p-3">
                <div className="flex-1">
                  <p className="text-sm font-medium">{a.title.slice(0, 80)}</p>
                  <p className="text-xs text-[var(--color-muted-foreground)]">{a.source}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge>{a.sentiment}</Badge>
                  <span className="font-bold text-[var(--color-accent)]">{Number(a.virality_score).toFixed(3)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
