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

export function TimelinePage() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    api.narratives().then((n) => {
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
      setEntries(items.slice(0, 40))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-5">
        <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Loading timeline...</p>
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
        <h1 className="text-xl font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Narrative Timeline</h1>
        <p className="text-xs font-mono text-[var(--color-fg-muted)] mt-1 tracking-wider uppercase">
          {entries.length} narratives · sorted by acceleration
        </p>
      </div>

      <div className="space-y-1">
        {entries.map((e, i) => {
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
      </div>

      {entries.length === 0 && (
        <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">No timeline data available.</p>
        </div>
      )}
    </div>
  )
}
