import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/loading"
import { HorizontalBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { TrendData } from "@/types"

export function TrendsPage() {
  const [data, setData] = useState<TrendData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.trends().then((d) => { setData(d.top_keywords); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Trend Analysis</h1>
      <Card>
        <CardTitle>Top Keywords</CardTitle>
        <HorizontalBarChart data={data} xKey="word" yKey="count" color="var(--color-secondary)" height={Math.max(300, data.length * 25)} />
      </Card>
    </div>
  )
}
