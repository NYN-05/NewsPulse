import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { SimplePieChart } from "@/charts/pie-chart"
import { SimpleBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { BiasData, SourceReliability } from "@/types"

export function BiasPage() {
  const [bias, setBias] = useState<BiasData | null>(null)
  const [reliability, setReliability] = useState<SourceReliability>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.bias(), api.sourceReliability()]).then(([b, r]) => {
      setBias(b); setReliability(r); setLoading(false)
    })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  const pieData = bias ? Object.entries(bias.political_leaning).map(([name, value]) => ({ name, value })) : []

  const relData = Object.entries(reliability).map(([name, v]) => ({
    name: name.slice(0, 25),
    score: v.reliability_score,
    articles: v.total_articles,
  }))

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">⚖ Bias & Source Reliability</h1>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {pieData.length > 0 && (
          <Card>
            <CardTitle>Political Leaning</CardTitle>
            <SimplePieChart data={pieData} height={280} />
          </Card>
        )}

        <Card>
          <CardTitle>Aggregate Metrics</CardTitle>
          <div className="space-y-3 p-2">
            <div className="flex justify-between rounded-lg bg-[var(--color-muted)] p-3">
              <span className="text-sm text-[var(--color-muted-foreground)]">Avg Clickbait Score</span>
              <span className="font-bold">{bias?.avg_clickbait.toFixed(4) || "—"}</span>
            </div>
            <div className="flex justify-between rounded-lg bg-[var(--color-muted)] p-3">
              <span className="text-sm text-[var(--color-muted-foreground)]">Avg Emotional Score</span>
              <span className="font-bold">{bias?.avg_emotional.toFixed(4) || "—"}</span>
            </div>
          </div>
        </Card>

        {relData.length > 0 && (
          <Card className="lg:col-span-2">
            <CardTitle>Source Reliability Scores</CardTitle>
            <SimpleBarChart data={relData} xKey="name" yKey="score" color="var(--color-primary)" height={Math.max(200, relData.length * 30)} />
          </Card>
        )}
      </div>
    </div>
  )
}
