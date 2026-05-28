import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { SimpleAreaChart } from "@/charts/area-chart"
import { api } from "@/services/api"
import type { TopicCluster } from "@/types"

export function EvolutionPage() {
  const [clusters, setClusters] = useState<TopicCluster[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.topicEvolution().then((d) => { setClusters(d.clusters || []); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Topic Evolution Over Time</h1>

      <div className="grid grid-cols-1 gap-4">
        {clusters.map((c) => (
          <Card key={c.cluster}>
            <div className="mb-2 flex items-center justify-between">
              <CardTitle>Cluster {c.cluster}</CardTitle>
              <div className="flex gap-2">
                <Badge>{c.total_articles} articles</Badge>
                <Badge variant={c.momentum > 0 ? "positive" : "negative"}>
                  {c.momentum > 0 ? "+" : ""}{c.momentum}
                </Badge>
              </div>
            </div>
            {c.trajectory && c.trajectory.length > 0 && (
              <SimpleAreaChart
                data={c.trajectory.map((t) => ({ date: t.date.slice(5, 10), count: t.count }))}
                xKey="date"
                yKey="count"
                color={["var(--color-primary)", "var(--color-secondary)", "var(--color-accent)", "var(--color-destructive)"][c.cluster % 4]}
              />
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}
