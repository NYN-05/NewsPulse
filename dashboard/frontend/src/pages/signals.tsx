import { useEffect, useState } from "react"
import { api } from "@/services/api"
import type { BreakingEvent } from "@/types"

export function SignalsPage() {
  const [signals, setSignals] = useState<BreakingEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.breaking().then((d) => {
      setSignals(d || [])
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-[var(--color-fg-muted)] font-mono">Loading signals...</p>
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
            <div className="h-4 w-32 bg-[var(--color-border)] rounded mb-3" />
            <div className="h-3 w-56 bg-[var(--color-border)] rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-[var(--color-border)] pb-4">
        <h1 className="text-lg font-medium text-[var(--color-fg)]">Intelligence Signals</h1>
        <p className="text-xs text-[var(--color-fg-muted)] mt-0.5">
          {signals.length} active signals · unusual activity and anomalies
        </p>
      </div>

      <div className="space-y-2">
        {signals.map((s, i) => (
          <div
            key={i}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-fg-muted)]">
                    {s.signal.replace("_", " ")}
                  </span>
                  {s.burst_factor && s.burst_factor > 5 && (
                    <span className="text-[10px] font-mono text-[var(--color-red)] bg-[var(--color-red)]/10 rounded px-1.5 py-0.5">
                      high
                    </span>
                  )}
                </div>
                <p className="text-sm font-medium text-[var(--color-fg)]">
                  {s.keyword || s.entity || "Unknown"}
                </p>
                <div className="flex gap-3 mt-2 text-[10px] text-[var(--color-fg-muted)] font-mono">
                  <span>Score: {s.score.toFixed(1)}</span>
                  {s.recent_count !== undefined && <span>Count: {s.recent_count}</span>}
                  {s.burst_factor !== undefined && <span>Burst: {s.burst_factor.toFixed(1)}×</span>}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {signals.length === 0 && (
        <div className="flex h-40 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs text-[var(--color-fg-muted)] font-mono">No active signals at this time.</p>
        </div>
      )}
    </div>
  )
}
