import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { SimpleBarChart } from "@/charts/bar-chart"
import { SimpleAreaChart } from "@/charts/area-chart"
import { api } from "@/services/api"

const PHASE_COLORS: Record<string, string> = {
  emerging: "#22c55e",
  accelerating: "#3b82f6",
  growing: "#06b6d4",
  peaked: "#f59e0b",
  stable: "#a1a1aa",
  declining: "#ef4444",
  fading: "#dc2626",
  resurging: "#a855f7",
  dormant: "#6b7280",
}

export function NarrativesPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<"emerging" | "clusters" | "entities">("emerging")

  useEffect(() => {
    api.narratives().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />
  if (!data || !data.summary) return <p className="text-center text-[var(--color-muted-foreground)]">No narrative data. Run pipeline with narratives step.</p>

  const tabs = [
    { id: "emerging" as const, label: "Emerging", count: data.summary.emerging_count },
    { id: "clusters" as const, label: "Cluster Narratives", count: data.summary.total_cluster_narratives },
    { id: "entities" as const, label: "Entity Narratives", count: data.summary.total_entity_narratives },
  ]

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Narrative Evolution</h1>

      <div className="flex gap-1 rounded-lg bg-[var(--color-muted)] p-1 text-sm">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 flex-1 rounded-md px-3 py-1.5 text-center text-sm font-medium transition-colors ${
              tab === t.id ? "bg-[var(--color-card)] text-[var(--color-foreground)]" : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
            }`}
          >
            {t.label}
            <Badge variant="outline">{t.count}</Badge>
          </button>
        ))}
      </div>

      {tab === "emerging" && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {data.emerging_topics.map((t: any, i: number) => (
            <Card key={i} className="border-l-2" style={{ borderLeftColor: PHASE_COLORS[t.phase] || "#a1a1aa" }}>
              <div className="flex items-start justify-between">
                <p className="font-medium capitalize">{t.name}</p>
                <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize" style={{ background: PHASE_COLORS[t.phase] + "30", color: PHASE_COLORS[t.phase] }}>{t.phase}</span>
              </div>
              <div className="mt-2 space-y-1 text-xs text-[var(--color-muted-foreground)]">
                <p>Type: {t.type}</p>
                <p>Acceleration: {t.acceleration > 0 ? "+" : ""}{t.acceleration}</p>
                <p>Total: {t.total_mentions || t.total_articles || 0}</p>
                <p>First seen: {t.first_seen}</p>
                {t.keywords && <p>Keywords: {t.keywords.join(", ")}</p>}
              </div>
            </Card>
          ))}
        </div>
      )}

      {tab === "clusters" && (
        <div className="grid grid-cols-1 gap-4">
          {data.cluster_narratives.map((c: any) => (
            <Card key={c.cluster}>
              <div className="flex items-center justify-between">
                <CardTitle>Cluster {c.cluster}</CardTitle>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize" style={{ background: PHASE_COLORS[c.phase] + "30", color: PHASE_COLORS[c.phase] }}>{c.phase}</span>
                  <Badge>{c.total_articles} articles</Badge>
                </div>
              </div>
              {c.top_keywords && <p className="mb-2 text-xs text-[var(--color-muted-foreground)]">Keywords: {c.top_keywords.join(", ")}</p>}
              {c.trajectory && c.trajectory.length > 0 && (
                <SimpleAreaChart
                  data={c.trajectory.map((t: any) => ({ date: t.date.slice(5, 10), count: t.count }))}
                  xKey="date" yKey="count" color={PHASE_COLORS[c.phase] || "var(--color-primary)"}
                />
              )}
            </Card>
          ))}
        </div>
      )}

      {tab === "entities" && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {data.entity_narratives.map((e: any, i: number) => (
            <Card key={i}>
              <div className="flex items-center justify-between">
                <span className="font-medium capitalize">{e.entity}</span>
                <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize" style={{ background: PHASE_COLORS[e.phase] + "30", color: PHASE_COLORS[e.phase] }}>{e.phase}</span>
              </div>
              <div className="mt-2 space-y-1 text-xs text-[var(--color-muted-foreground)]">
                <p>Mentions: {e.total_mentions} (recent 7d: {e.recent_7_days})</p>
                <p>Acceleration: {e.acceleration > 0 ? "+" : ""}{e.acceleration}</p>
                <p>Avg sentiment: {e.avg_sentiment.toFixed(3)}</p>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
