import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { EntityGraphFlow } from "@/charts/entity-graph"
import { api } from "@/services/api"
import type { EntityGraph } from "@/types"

export function EntityGraphPage() {
  const [data, setData] = useState<EntityGraph | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.entityGraph().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />
  if (!data || "error" in data) return <p className="text-center text-[var(--color-muted-foreground)]">No entity graph data. Run pipeline first.</p>

  return (
    <div className="space-y-4">
      <h1 className="mb-2 text-xl font-bold">Entity Relationship Graph</h1>

      <div className="grid grid-cols-4 gap-3">
        <Card><CardTitle>Total Nodes</CardTitle><p className="text-2xl font-bold">{data.stats.total_nodes}</p></Card>
        <Card><CardTitle>Total Edges</CardTitle><p className="text-2xl font-bold">{data.stats.total_edges}</p></Card>
        <Card><CardTitle>Communities</CardTitle><p className="text-2xl font-bold">{data.stats.communities.length}</p></Card>
        <Card><CardTitle>Top Centrality</CardTitle><p className="text-lg font-bold capitalize">{data.stats.top_entities[0]?.entity || "—"}</p></Card>
      </div>

      <Card>
        <CardTitle>Interactive Graph</CardTitle>
        <div className="text-xs text-[var(--color-muted-foreground)] mb-2">Drag to pan · Scroll to zoom · Click nodes to explore</div>
        <EntityGraphFlow nodes={data.nodes} edges={data.edges} height={500} />
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Top Entities by Centrality</CardTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-[var(--color-border)] text-left">
                <th className="p-2">Entity</th><th className="p-2">Type</th><th className="p-2">Centrality</th><th className="p-2">Betweenness</th>
              </tr></thead>
              <tbody>
                {data.nodes.map((n) => (
                  <tr key={n.id} className="border-b border-[var(--color-border)]">
                    <td className="p-2 font-medium capitalize">{n.id}</td>
                    <td className="p-2"><Badge>{n.type}</Badge></td>
                    <td className="p-2">{n.centrality.toFixed(4)}</td>
                    <td className="p-2">{n.betweenness.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card>
          <CardTitle>Communities</CardTitle>
          <div className="space-y-2">
            {data.stats.communities.map((c) => (
              <div key={c.id} className="rounded-lg bg-[var(--color-muted)] p-3">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-sm font-medium">Community {c.id + 1}</span>
                  <Badge>{c.size} members</Badge>
                </div>
                <div className="flex flex-wrap gap-1">
                  {c.members.slice(0, 8).map((m) => (
                    <span key={m} className="rounded bg-[var(--color-card)] px-1.5 py-0.5 text-[10px] capitalize">{m}</span>
                  ))}
                  {c.members.length > 8 && <span className="text-[10px] text-[var(--color-muted-foreground)]">+{c.members.length - 8} more</span>}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
