import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
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
      <h1 className="text-xl font-bold">Entity Relationship Graph</h1>

      <div className="grid grid-cols-3 gap-3">
        <Card>
          <CardTitle>Total Nodes</CardTitle>
          <p className="text-2xl font-bold">{data.stats.total_nodes}</p>
        </Card>
        <Card>
          <CardTitle>Total Edges</CardTitle>
          <p className="text-2xl font-bold">{data.stats.total_edges}</p>
        </Card>
        <Card>
          <CardTitle>Communities</CardTitle>
          <p className="text-2xl font-bold">{data.stats.communities.length}</p>
        </Card>
      </div>

      <Card>
        <CardTitle>Top Entities by Centrality</CardTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left">
                <th className="p-2">Entity</th>
                <th className="p-2">Type</th>
                <th className="p-2">Centrality</th>
                <th className="p-2">Betweenness</th>
              </tr>
            </thead>
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

      {data.edges.length > 0 && (
        <Card>
          <CardTitle>Entity Connections (Top {data.edges.length})</CardTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)] text-left">
                  <th className="p-2">Source</th>
                  <th className="p-2">Target</th>
                  <th className="p-2">Weight</th>
                </tr>
              </thead>
              <tbody>
                {data.edges.slice(0, 30).map((e, i) => (
                  <tr key={i} className="border-b border-[var(--color-border)]">
                    <td className="p-2 capitalize">{e.source}</td>
                    <td className="p-2 capitalize">{e.target}</td>
                    <td className="p-2">{e.weight}</td>
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
