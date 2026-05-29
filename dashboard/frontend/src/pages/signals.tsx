import { useEffect, useState } from "react"
import { api } from "@/services/api"
import type { BreakingEvent } from "@/types"

export function SignalsPage() {
  const [signals, setSignals] = useState<BreakingEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.breaking().then((d) => { setSignals(d || []); setLoading(false) })
  }, [])

  if (loading) {
    return (
      <div className="space-y-5">
        <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Loading signals...</p>
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
            <div className="h-4 w-32 bg-[var(--color-border)] rounded mb-3" />
            <div className="h-3 w-3/4 bg-[var(--color-border)] rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-[var(--color-border)] pb-5">
        <h1 className="text-xl font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Intelligence Signals</h1>
        <p className="text-xs font-mono text-[var(--color-fg-muted)] mt-1 tracking-wider uppercase">
          {signals.length} active signals · unusual activity detected
        </p>
      </div>

      <div className="space-y-2">
        {signals.map((s, i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] transition-colors p-4">
            <div className="flex items-start gap-3">
              <span className="w-2 h-2 rounded-full shrink-0 mt-1 bg-[var(--color-red)]" />
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-widest uppercase">
                    {s.signal.replace("_", " ")}
                  </span>
                  {s.burst_factor && s.burst_factor > 5 && (
                    <span className="text-[9px] font-mono text-[var(--color-red)] bg-[var(--color-red)]/10 rounded px-1.5 py-0.5">high</span>
                  )}
                </div>
                <p className="text-sm font-serif text-[var(--color-fg)]">{s.keyword || s.entity || "Unknown"}</p>
                <div className="flex gap-3 mt-2 text-[10px] font-mono text-[var(--color-fg-muted)]">
                  <span>Score: {s.score.toFixed(1)}</span>
                  {s.recent_count !== undefined && <span>Articles: {s.recent_count}</span>}
                  {s.burst_factor !== undefined && <span>Burst: {s.burst_factor.toFixed(1)}×</span>}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {signals.length === 0 && (
        <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">No active signals at this time.</p>
        </div>
      )}
    </div>
  )
}
