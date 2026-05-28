import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { api } from "@/services/api"
import type { BreakingEvent } from "@/types"

const sigColors: Record<string, string> = {
  keyword_burst: "warning",
  entity_spike: "info",
}

export function BreakingPage() {
  const [data, setData] = useState<BreakingEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.breaking().then((d) => { setData(d || []); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  return (
    <div className="space-y-4">
      <h1 className="flex items-center gap-2 text-xl font-bold">
        ⚡ Breaking News Detection
        <Badge variant="destructive">{data.length} signals</Badge>
      </h1>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {data.map((e, i) => {
          const kw = e.keyword || e.entity || "unknown"
          return (
            <Card key={i} className="border-l-2" style={{ borderLeftColor: "var(--color-accent)" }}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium capitalize">{kw}</p>
                  <Badge variant={sigColors[e.signal] || "default"}>{e.signal.replace("_", " ")}</Badge>
                </div>
                <span className="text-lg font-bold">{e.score.toFixed(0)}</span>
              </div>
              <div className="mt-2 flex gap-3 text-xs text-[var(--color-muted-foreground)]">
                <span>Count: {e.recent_count || 0}</span>
                <span>Burst: {e.burst_factor?.toFixed(1) || "—"}×</span>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
