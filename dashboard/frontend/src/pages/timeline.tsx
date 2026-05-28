import { useEffect, useState } from "react"
import { api } from "@/services/api"

interface TimelineEntry {
  id: string
  type: "narrative" | "entity" | "cluster"
  label: string
  phase: string
  momentum: number
  acceleration: number
  count: number
  sentiment: number
  keywords: string[]
}

const PHASE_COLORS: Record<string, string> = {
  emerging: "var(--color-cyan)",
  accelerating: "var(--color-accent)",
  growing: "var(--color-green)",
  peaked: "var(--color-amber)",
  stable: "var(--color-fg-secondary)",
  declining: "var(--color-red)",
  fading: "var(--color-fg-muted)",
  resurging: "var(--color-accent)",
  dormant: "var(--color-fg-muted)",
}

export function TimelinePage() {
  const [entries, setEntries] = useState<TimelineEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.narratives().catch(() => ({}) as any),
    ]).then(([narratives]) => {
      const n = narratives as any
      const items: TimelineEntry[] = []

      const emerging = n.emerging_topics || []
      for (const t of emerging.slice(0, 20)) {
        items.push({
          id: `em-${t.cluster || Math.random()}`,
          type: "narrative",
          label: t.topic || `Cluster ${t.cluster}`,
          phase: t.phase || "emerging",
          momentum: t.momentum || 0,
          acceleration: t.acceleration || 0,
          count: t.count || 0,
          sentiment: t.avg_sentiment || 0,
          keywords: t.keywords || [],
        })
      }

      const entities = n.entity_narratives || []
      for (const e of entities.slice(0, 20)) {
        items.push({
          id: `ent-${e.entity || Math.random()}`,
          type: "entity",
          label: e.entity || "unknown",
          phase: e.phase || "stable",
          momentum: e.momentum || 0,
          acceleration: e.acceleration || 0,
          count: e.total_mentions || 0,
          sentiment: e.avg_sentiment || 0,
          keywords: [],
        })
      }

      items.sort((a, b) => Math.abs(b.acceleration) - Math.abs(a.acceleration))
      setEntries(items.slice(0, 40))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-[var(--color-fg-muted)] font-mono">Loading timeline...</p>
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
            <div className="h-4 w-40 bg-[var(--color-border)] rounded mb-3" />
            <div className="h-3 w-72 bg-[var(--color-border)] rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-[var(--color-border)] pb-4">
        <h1 className="text-lg font-medium text-[var(--color-fg)]">Narrative Timeline</h1>
        <p className="text-xs text-[var(--color-fg-muted)] mt-0.5">
          How narratives evolve across phases · sorted by acceleration
        </p>
      </div>

      <div className="space-y-1">
        {entries.map((e, i) => {
          const phaseColor = PHASE_COLORS[e.phase] || "var(--color-fg-secondary)"
          const isExpanded = expanded === e.id

          return (
            <button
              key={e.id}
              onClick={() => setExpanded(isExpanded ? null : e.id)}
              className={`w-full text-left rounded-lg border transition-colors p-4 ${
                isExpanded
                  ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                  : "border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)]"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: phaseColor }} />
                  <span className="text-xs font-mono text-[var(--color-fg-muted)] w-16 shrink-0">{e.phase}</span>
                  <span className="text-sm text-[var(--color-fg)] truncate">{e.label}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[10px] font-mono text-[var(--color-fg-muted)]">{e.count} articles</span>
                  <span className={`text-xs font-mono w-12 text-right ${
                    e.acceleration > 0 ? "text-[var(--color-green)]" : "text-[var(--color-red)]"
                  }`}>
                    {e.acceleration > 0 ? "+" : ""}{e.acceleration.toFixed(1)}
                  </span>
                </div>
              </div>

              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-[var(--color-border)] grid grid-cols-2 gap-3 text-[10px] font-mono text-[var(--color-fg-secondary)]">
                  <div>Momentum: {e.momentum.toFixed(2)}</div>
                  <div>Acceleration: {e.acceleration.toFixed(2)}</div>
                  <div>Sentiment: {e.sentiment.toFixed(3)}</div>
                  <div>Articles: {e.count}</div>
                  {e.keywords.length > 0 && (
                    <div className="col-span-2 flex flex-wrap gap-1 mt-1">
                      {e.keywords.slice(0, 8).map((kw) => (
                        <span key={kw} className="text-[10px] text-[var(--color-fg-muted)] bg-[var(--color-card)] border border-[var(--color-border)] rounded px-1.5 py-0.5">
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
      </div>

      {entries.length === 0 && (
        <div className="flex h-40 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs text-[var(--color-fg-muted)] font-mono">No timeline data available.</p>
        </div>
      )}
    </div>
  )
}
