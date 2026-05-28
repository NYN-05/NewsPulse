import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { SimpleBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { ClusterData } from "@/types"

export function ClustersPage() {
  const [data, setData] = useState<ClusterData[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    api.clusters().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  const sel = data.find((c) => c.label === selected)

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Topic Clusters</h1>
      <Card>
        <CardTitle>Cluster Distribution</CardTitle>
        <SimpleBarChart data={data} xKey="label" yKey="count" height={300} />
      </Card>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {data.map((c) => (
          <button
            key={c.label}
            onClick={() => setSelected(c.label)}
            className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 text-left transition-colors hover:border-[var(--color-primary)]"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="font-medium">{c.label}</span>
              <Badge>{c.count} articles</Badge>
            </div>
            <div className="space-y-1 text-xs text-[var(--color-muted-foreground)]">
              <p>Avg Sentiment: {c.avg_sentiment.toFixed(3)}</p>
              <p>Top Source: {c.top_source}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
