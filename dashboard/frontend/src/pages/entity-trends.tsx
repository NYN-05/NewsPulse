import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { SimpleBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { EntityTrend } from "@/types"

export function EntityTrendsPage() {
  const [data, setData] = useState<EntityTrend[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.entityTrends().then((d) => { setData(d || []); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Entity Trend Analysis</h1>
      <Card>
        <CardTitle>Entity Momentum</CardTitle>
        <SimpleBarChart
          data={data.map((e) => ({ entity: e.entity, momentum: e.momentum }))}
          xKey="entity"
          yKey="momentum"
          color="var(--color-accent)"
        />
      </Card>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {data.map((e) => (
          <div key={e.entity} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="font-medium capitalize">{e.entity}</span>
              <Badge variant={e.momentum > 50 ? "warning" : "default"}>{e.momentum > 0 ? "+" : ""}{e.momentum}</Badge>
            </div>
            <div className="space-y-1 text-xs text-[var(--color-muted-foreground)]">
              <p>Total mentions: {e.total_mentions}</p>
              <p>Recent: {e.recent_mentions}</p>
              <p>Peak: {e.peak_date}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
