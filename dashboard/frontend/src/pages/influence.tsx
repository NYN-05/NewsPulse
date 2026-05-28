import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { SimpleBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"

export function InfluencePage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<"entities" | "sources" | "propagation">("entities")

  useEffect(() => {
    api.influence().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />
  if (!data || !data.summary) return <p className="text-center text-muted-foreground">No influence data. Run pipeline with influence step.</p>

  const tabs = [
    { id: "entities" as const, label: "Influential Entities", count: data.summary.total_entities_scored },
    { id: "sources" as const, label: "Source Amplifiers", count: data.summary.total_sources_scored },
    { id: "propagation" as const, label: "Propagation Speed", count: data.summary.total_propagation_tracked },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Influence Map</h1>
        <div className="flex gap-2 text-xs text-muted-foreground">
          <span>Top influencer: <strong className="text-foreground capitalize">{data.summary.top_influencer || "—"}</strong></span>
          <span>·</span>
          <span>Top amplifier: <strong className="text-foreground">{data.summary.top_amplifier || "—"}</strong></span>
        </div>
      </div>

      <div className="flex gap-1 rounded-lg bg-muted p-1 text-sm">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 flex-1 rounded-md px-3 py-1.5 text-center text-sm font-medium transition-colors ${
              tab === t.id ? "bg-card text-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
            <Badge variant="outline">{t.count}</Badge>
          </button>
        ))}
      </div>

      {tab === "entities" && (
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card>
            <CardTitle>Influence Scores</CardTitle>
            <SimpleBarChart
              data={data.entity_influence.slice(0, 20).map((e: any) => ({ entity: e.entity.slice(0, 15), score: e.influence_score }))}
              xKey="entity" yKey="score" color="var(--color-accent)" height={300}
            />
          </Card>
          <Card>
            <CardTitle>Entity Details</CardTitle>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-(--color-border) text-left">
                  <th className="p-1.5">Entity</th><th className="p-1.5">Score</th><th className="p-1.5">Mentions</th>
                  <th className="p-1.5">Sources</th><th className="p-1.5">Cross-Domain</th>
                </tr></thead>
                <tbody>
                  {data.entity_influence.slice(0, 30).map((e: any, i: number) => (
                    <tr key={i} className="border-b border-(--color-border)">
                      <td className="p-1.5 font-medium capitalize">{e.entity}</td>
                      <td className="p-1.5 font-bold text-accent">{e.influence_score.toFixed(2)}</td>
                      <td className="p-1.5">{e.total_mentions}</td>
                      <td className="p-1.5">{e.source_count}</td>
                      <td className="p-1.5">{e.cross_domain_links}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {tab === "sources" && (
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card>
            <CardTitle>Source Amplification Scores</CardTitle>
            <SimpleBarChart
              data={data.source_amplification.slice(0, 15).map((s: any) => ({ source: s.source.slice(0, 20), score: s.amplification_score }))}
              xKey="source" yKey="score" color="var(--color-primary)" height={350}
            />
          </Card>
          <Card>
            <CardTitle>Source Details</CardTitle>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-(--color-border) text-left">
                  <th className="p-1.5">Source</th><th className="p-1.5">Score</th><th className="p-1.5">Articles</th>
                  <th className="p-1.5">Entities</th><th className="p-1.5">Categories</th>
                </tr></thead>
                <tbody>
                  {data.source_amplification.slice(0, 25).map((s: any, i: number) => (
                    <tr key={i} className="border-b border-(--color-border)">
                      <td className="max-w-[180px] truncate p-1.5 font-medium">{s.source}</td>
                      <td className="p-1.5 font-bold text-primary">{s.amplification_score.toFixed(2)}</td>
                      <td className="p-1.5">{s.total_articles}</td>
                      <td className="p-1.5">{s.entity_count}</td>
                      <td className="p-1.5">{s.category_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {tab === "propagation" && (
        <Card>
          <CardTitle>Information Propagation Speed</CardTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-(--color-border) text-left">
                <th className="p-2">Entity</th><th className="p-2">Spread Speed</th><th className="p-2">Sources</th>
                <th className="p-2">Articles</th><th className="p-2">Density (day)</th>
                <th className="p-2">Mean Adoption (hrs)</th>
              </tr></thead>
              <tbody>
                {data.propagation.map((p: any, i: number) => (
                  <tr key={i} className="border-b border-(--color-border)">
                    <td className="p-2 font-medium capitalize">{p.entity}</td>
                    <td className="p-2 font-bold text-accent">{p.spread_speed.toFixed(1)}</td>
                    <td className="p-2">{p.source_count}</td>
                    <td className="p-2">{p.article_count}</td>
                    <td className="p-2">{p.density_articles_per_day}</td>
                    <td className="p-2">{p.mean_adoption_hours.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
