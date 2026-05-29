import { useEffect, useState } from "react"
import { api } from "@/services/api"

interface Entry {
  id: string
  label: string
  phase: string
  momentum: number
  acceleration: number
  count: number
  sentiment: number
  keywords: string[]
}

interface ChainEntry {
  id: string
  chain: string[]
  sectors: string[]
  length: number
  hops: number
  weight: number
}

const PHASE_COLORS: Record<string, string> = {
  emerging: "#6fcf8d",
  accelerating: "#8b7cf7",
  growing: "#6fcf8d",
  peaked: "#d4a757",
  stable: "#a6a0b8",
  declining: "#e06c7a",
  fading: "#5f5878",
  resurging: "#8b7cf7",
  dormant: "#5f5878",
}

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

export function TimelinePage() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [chains, setChains] = useState<ChainEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [view, setView] = useState<"narratives" | "chains">("narratives")

  useEffect(() => {
    Promise.all([
      api.narratives().catch(() => ({})),
      api.crossDomain().catch(() => ({ links: [], chains: [], sector_map: {} })),
    ]).then(([n, cd]) => {
      const items: Entry[] = []
      for (const t of (n as any).emerging_topics || []) {
        items.push({
          id: `em-${t.cluster || Math.random()}`,
          label: t.topic || `Cluster ${t.cluster}`,
          phase: t.phase || "emerging",
          momentum: t.momentum || 0,
          acceleration: t.acceleration || 0,
          count: t.count || 0,
          sentiment: t.avg_sentiment || 0,
          keywords: t.keywords || [],
        })
      }
      for (const e of (n as any).entity_narratives || []) {
        items.push({
          id: `ent-${e.entity || Math.random()}`,
          label: e.entity || "Unknown",
          phase: e.phase || "stable",
          momentum: e.momentum || 0,
          acceleration: e.acceleration || 0,
          count: e.total_mentions || 0,
          sentiment: e.avg_sentiment || 0,
          keywords: [],
        })
      }
      items.sort((a, b) => Math.abs(b.acceleration) - Math.abs(a.acceleration))
      setEntries(items.slice(0, 30))

      const rawChains = (cd as any).chains || []
      const parsed: ChainEntry[] = rawChains
        .filter((c: any) => c.chain && c.chain.length >= 2)
        .slice(0, 10)
        .map((c: any) => ({
          id: `chain-${c.chain_key || Math.random()}`,
          chain: c.chain,
          sectors: c.sectors || [],
          length: c.length || c.chain.length,
          hops: c.cross_domain_hops || 0,
          weight: c.total_weight || 0,
        }))
      setChains(parsed)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-5">
        <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Tracking narrative evolution...</p>
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
            <div className="h-4 w-40 bg-[var(--color-border)] rounded mb-3" />
            <div className="h-3 w-3/4 bg-[var(--color-border)] rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-[var(--color-border)] pb-5">
        <h1 className="text-xl font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Narrative Evolution</h1>
        <p className="text-xs font-mono text-[var(--color-fg-muted)] mt-1 tracking-wider uppercase">
          Tracking how narratives emerge, propagate, and mutate across domains
        </p>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setView("narratives")}
          className={`text-[10px] font-mono tracking-wider px-3 py-1.5 rounded border transition-colors ${
            view === "narratives"
              ? "border-[var(--color-accent)] text-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
              : "border-[var(--color-border)] text-[var(--color-fg-muted)]"
          }`}
        >
          Active Narratives
        </button>
        <button
          onClick={() => setView("chains")}
          className={`text-[10px] font-mono tracking-wider px-3 py-1.5 rounded border transition-colors ${
            view === "chains"
              ? "border-[var(--color-accent)] text-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
              : "border-[var(--color-border)] text-[var(--color-fg-muted)]"
          }`}
        >
          Impact Chains
        </button>
      </div>

      {view === "narratives" && (
        <div className="space-y-1">
          {entries.map((e) => {
            const color = PHASE_COLORS[e.phase] || "#a6a0b8"
            const isExpanded = expanded === e.id
            return (
              <button
                key={e.id}
                onClick={() => setExpanded(isExpanded ? null : e.id)}
                className={`w-full text-left rounded-lg border transition-all p-4 ${
                  isExpanded
                    ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                    : "border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] hover:border-[var(--color-border-hover)]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
                  <span className="text-[10px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase w-20 shrink-0">{e.phase}</span>
                  <span className="text-sm text-[var(--color-fg)] truncate font-serif">{e.label}</span>
                  <span className="ml-auto shrink-0 flex items-center gap-3">
                    <span className="text-[10px] font-mono text-[var(--color-fg-muted)]">{e.count} art.</span>
                    <span className={`text-xs font-mono w-12 text-right ${
                      e.acceleration > 0 ? "text-[var(--color-green)]" : "text-[var(--color-red)]"
                    }`}>
                      {e.acceleration > 0 ? "+" : ""}{e.acceleration.toFixed(1)}
                    </span>
                  </span>
                </div>
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-[var(--color-border)] grid grid-cols-2 gap-2 text-[10px] font-mono text-[var(--color-fg-muted)]">
                    <div>Momentum: {e.momentum.toFixed(2)}</div>
                    <div>Acceleration: {e.acceleration.toFixed(2)}</div>
                    <div>Sentiment: {e.sentiment.toFixed(3)}</div>
                    <div>Articles: {e.count}</div>
                    {e.keywords.length > 0 && (
                      <div className="col-span-2 flex flex-wrap gap-1 mt-1">
                        {e.keywords.slice(0, 8).map((kw) => (
                          <span key={kw} className="text-[9px] font-mono text-[var(--color-fg-muted)] bg-[var(--color-card)] border border-[var(--color-border)] rounded px-1.5 py-0.5">
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </button>
            )
          })}
          {entries.length === 0 && (
            <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
              <p className="text-xs font-mono text-[var(--color-fg-muted)]">No narrative data available.</p>
            </div>
          )}
        </div>
      )}

      {view === "chains" && (
        <div className="space-y-1">
          {chains.map((c) => (
            <div
              key={c.id}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4"
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-[var(--color-accent)] shrink-0" />
                <span className="text-[10px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">
                  Impact chain · {c.hops} domain hops
                </span>
                <span className="ml-auto text-[10px] font-mono text-[var(--color-accent)]">
                  weight {c.weight.toFixed(1)}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-1.5">
                {c.chain.map((step, i) => (
                  <span key={i} className="flex items-center gap-1.5">
                    <span className="text-xs font-mono text-[var(--color-fg)] px-2 py-1 rounded bg-[var(--color-card-hover)] border border-[var(--color-border)]">
                      {step}
                    </span>
                    {i < c.chain.length - 1 && (
                      <span className="text-[var(--color-accent)] text-xs">→</span>
                    )}
                  </span>
                ))}
              </div>

              {c.sectors.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {c.sectors.map((s) => (
                    <span key={s} className="text-[9px] font-mono text-[var(--color-fg-muted)] bg-[var(--color-accent-subtle)] rounded px-1.5 py-0.5">
                      {SECTOR_LABELS[s] || s}
                    </span>
                  ))}
                </div>
              )}

              <p className="mt-3 text-[10px] font-mono text-[var(--color-fg-muted)] italic">
                Disruption propagates across {c.hops} domains in {c.length} hops
              </p>
            </div>
          ))}
          {chains.length === 0 && (
            <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
              <p className="text-xs font-mono text-[var(--color-fg-muted)]">No impact chains detected yet.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
