import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { CrossDomainGraph } from "@/charts/entity-graph"
import { api } from "@/services/api"
import type { CrossDomainData } from "@/types"

const SECTOR_COLORS: Record<string, string> = {
  politics: "#ef4444",
  finance: "#22c55e",
  technology: "#3b82f6",
  energy: "#f59e0b",
  military: "#dc2626",
  startups: "#a855f7",
  social: "#ec4899",
  global_events: "#06b6d4",
}

const SECTOR_DISPLAY: Record<string, string> = {
  politics: "Politics",
  finance: "Finance",
  technology: "Technology",
  energy: "Energy",
  military: "Military",
  startups: "Startups",
  social: "Social",
  global_events: "Global Events",
}

export function CrossDomainPage() {
  const [data, setData] = useState<CrossDomainData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showChains, setShowChains] = useState(false)

  useEffect(() => {
    api.crossDomain().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />
  if (!data || data.links.length === 0) {
    return <p className="text-center text-[var(--color-muted-foreground)]">No cross-domain data. Run pipeline with cross_domain step.</p>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Cross-Domain Intelligence</h1>
        <div className="flex items-center gap-2">
          <Badge>{data.links.length} links</Badge>
          <Badge variant="warning">{data.chains.length} impact chains</Badge>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {Object.entries(SECTOR_DISPLAY).map(([key, label]) => (
          <div key={key} className="flex items-center gap-1.5 rounded-full border border-[var(--color-border)] px-3 py-1 text-xs">
            <div className="h-2 w-2 rounded-full" style={{ background: SECTOR_COLORS[key] }} />
            <span className="capitalize">{label}</span>
          </div>
        ))}
      </div>

      <div className="flex gap-1 rounded-lg bg-[var(--color-muted)] p-1 text-sm">
        <button
          onClick={() => setShowChains(false)}
          className={`flex-1 rounded-md px-3 py-1.5 text-center text-sm font-medium transition-colors ${!showChains ? "bg-[var(--color-card)] text-[var(--color-foreground)]" : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"}`}
        >
          Relationship Map
        </button>
        <button
          onClick={() => setShowChains(true)}
          className={`flex-1 rounded-md px-3 py-1.5 text-center text-sm font-medium transition-colors ${showChains ? "bg-[var(--color-card)] text-[var(--color-foreground)]" : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"}`}
        >
          Impact Chains
        </button>
      </div>

      {!showChains && (
        <>
          <Card>
            <CardTitle>Cross-Domain Relationship Map</CardTitle>
            <div className="text-xs text-[var(--color-muted-foreground)] mb-2">
              Nodes colored by sector · Edge thickness = relationship strength · Drag/zoom to explore
            </div>
            <CrossDomainGraph links={data.links} height={500} />
          </Card>

          <Card>
            <CardTitle>Top Cross-Domain Links</CardTitle>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)] text-left">
                    <th className="p-2">Source Entity</th>
                    <th className="p-2">Sector</th>
                    <th className="p-2">→</th>
                    <th className="p-2">Target Entity</th>
                    <th className="p-2">Sector</th>
                    <th className="p-2">Strength</th>
                    <th className="p-2">Co-occurrence</th>
                    <th className="p-2">Sources</th>
                  </tr>
                </thead>
                <tbody>
                  {data.links.slice(0, 50).map((l, i) => (
                    <tr key={i} className="border-b border-[var(--color-border)]">
                      <td className="p-2 font-medium capitalize">{l.source_entity}</td>
                      <td className="p-2">
                        <span className="inline-flex items-center gap-1">
                          <div className="h-2 w-2 rounded-full" style={{ background: SECTOR_COLORS[l.source_sector] }} />
                          <span className="text-xs">{SECTOR_DISPLAY[l.source_sector] || l.source_sector}</span>
                        </span>
                      </td>
                      <td className="p-2 text-center text-[var(--color-muted-foreground)]">↔</td>
                      <td className="p-2 font-medium capitalize">{l.target_entity}</td>
                      <td className="p-2">
                        <span className="inline-flex items-center gap-1">
                          <div className="h-2 w-2 rounded-full" style={{ background: SECTOR_COLORS[l.target_sector] }} />
                          <span className="text-xs">{SECTOR_DISPLAY[l.target_sector] || l.target_sector}</span>
                        </span>
                      </td>
                      <td className="p-2 font-bold text-[var(--color-accent)]">{l.strength.toFixed(1)}</td>
                      <td className="p-2">{l.cooccurrence_count}</td>
                      <td className="p-2">{l.source_diversity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {showChains && data.chains.length > 0 && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {data.chains.map((c, i) => (
            <Card key={i}>
              <CardTitle>Chain {i + 1}</CardTitle>
              <div className="flex flex-wrap items-center gap-1.5 text-sm">
                {c.chain.map((entity, ci) => (
                  <span key={ci} className="flex items-center gap-1">
                    <span className={`rounded-md px-2 py-0.5 text-xs font-medium capitalize`}
                      style={{
                        background: `${SECTOR_COLORS[c.sectors[ci]] || "#a1a1aa"}20`,
                        color: SECTOR_COLORS[c.sectors[ci]] || "#a1a1aa",
                      }}
                    >
                      {entity}
                    </span>
                    {ci < c.chain.length - 1 && <span className="text-[var(--color-muted-foreground)]">→</span>}
                  </span>
                ))}
              </div>
              <div className="mt-2 flex gap-2 text-xs text-[var(--color-muted-foreground)]">
                <span>Hops: {c.cross_domain_hops}</span>
                <span>·</span>
                <span>Weight: {c.total_weight}</span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
