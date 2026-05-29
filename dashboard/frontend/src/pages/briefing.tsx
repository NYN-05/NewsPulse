import { useState, useEffect } from "react"
import { api } from "@/services/api"
import type { BriefingData } from "@/types"

export function BriefingPage() {
  const [data, setData] = useState<BriefingData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.briefing().then(setData).catch(() => setData(null)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-xs font-mono text-[var(--color-fg-muted)]">Loading briefing...</div>
  if (!data) return <div className="text-xs font-mono text-[var(--color-fg-muted)]">No briefing available</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-serif text-[var(--color-fg)]">Intelligence Briefing</h1>
        <p className="text-[10px] font-mono text-[var(--color-fg-muted)] mt-1">
          {data.generated_at} &middot; Confidence: {data.overall_confidence}
        </p>
      </div>

      <div className="p-4 border border-[var(--color-border)] rounded bg-[var(--color-card)]">
        <p className="text-sm font-sans text-[var(--color-fg)] leading-relaxed">{data.executive_summary}</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {Object.entries(data.statistics).map(([k, v]) => (
          <div key={k} className="p-3 border border-[var(--color-border)] rounded bg-[var(--color-card)]">
            <p className="text-[10px] font-mono text-[var(--color-fg-muted)] uppercase tracking-wider">{k.replace(/_/g, " ")}</p>
            <p className="mt-1 text-lg font-mono text-[var(--color-fg)]">{v}</p>
          </div>
        ))}
      </div>

      {data.sector_situations.length > 0 && (
        <div>
          <h2 className="text-sm font-mono text-[var(--color-fg)] uppercase tracking-wider mb-3">Sector Situations</h2>
          <div className="grid grid-cols-2 gap-3">
            {data.sector_situations.map((s) => (
              <div key={s.sector} className="p-3 border border-[var(--color-border)] rounded bg-[var(--color-card)]">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-[var(--color-fg)] uppercase tracking-wider">{s.sector}</span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                    s.status === "active" ? "bg-[var(--color-cyan)]/10 text-[var(--color-cyan)]" : "text-[var(--color-fg-muted)]"
                  }`}>{s.status}</span>
                </div>
                <p className="mt-1 text-[10px] font-mono text-[var(--color-fg-muted)]">
                  {s.active_entities} entities &middot; {s.cross_domain_links} links &middot; conf {s.avg_confidence}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.key_connections.length > 0 && (
        <div>
          <h2 className="text-sm font-mono text-[var(--color-fg)] uppercase tracking-wider mb-3">Key Connections</h2>
          <div className="space-y-2">
            {data.key_connections.map((c, i) => (
              <div key={i} className="p-3 border border-[var(--color-border)] rounded bg-[var(--color-card)]">
                <p className="text-xs font-mono text-[var(--color-fg)]">
                  {c.source} ({c.source_sector}) &harr; {c.target} ({c.target_sector})
                </p>
                <p className="mt-0.5 text-[10px] font-mono text-[var(--color-fg-muted)]">
                  Confidence: {c.confidence.toFixed(2)} &middot; {c.causal_mechanism || "No causal mechanism"}
                </p>
                {c.impact && <p className="text-[10px] font-mono text-[var(--color-fg-muted)]">Impact: {c.impact}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {data.watch_items.length > 0 && (
        <div>
          <h2 className="text-sm font-mono text-[var(--color-fg)] uppercase tracking-wider mb-3">Watch Items</h2>
          <div className="space-y-1.5">
            {data.watch_items.map((w, i) => (
              <div key={i} className="flex items-center gap-2 p-2 border border-[var(--color-border)] rounded bg-[var(--color-card)]">
                <span className={`w-1.5 h-1.5 rounded-full ${
                  w.priority === "high" ? "bg-[var(--color-red)]" : w.priority === "medium" ? "bg-[var(--color-yellow)]" : "bg-[var(--color-fg-muted)]"
                }`} />
                <span className="text-[10px] font-mono text-[var(--color-fg-muted)]">{w.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
