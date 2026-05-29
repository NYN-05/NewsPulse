import { useEffect, useState } from "react"
import { api } from "@/services/api"
import type { BreakingEvent } from "@/types"

function severityLevel(score: number, burst?: number): { label: string; color: string } {
  if (burst && burst > 50) return { label: "Critical", color: "#e06c7a" }
  if (score > 50 || (burst && burst > 20)) return { label: "High", color: "#d4a757" }
  if (score > 20 || (burst && burst > 5)) return { label: "Elevated", color: "#4a7cf7" }
  return { label: "Monitoring", color: "#8899b4" }
}

export function SignalsPage() {
  const [signals, setSignals] = useState<BreakingEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<number | null>(null)

  useEffect(() => {
    api.breaking().then((d) => { setSignals(d || []); setLoading(false) })
  }, [])

  if (loading) {
    return (
      <div className="space-y-5">
        <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Scanning for signals...</p>
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
        <h1 className="text-xl font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Emerging Signals</h1>
        <p className="text-[10px] font-mono text-[var(--color-fg-muted)] mt-1 tracking-wider uppercase">
          {signals.length} active signals — early warning intelligence
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4">
          <div className="text-[10px] font-mono text-[var(--color-fg-muted)]">Total Signals</div>
          <div className="text-xl font-serif text-[var(--color-fg)] mt-1">{signals.length}</div>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4">
          <div className="text-[10px] font-mono text-[var(--color-fg-muted)]">Critical</div>
          <div className="text-xl font-serif text-[var(--color-red)] mt-1">{signals.filter((s) => (s.burst_factor || 1) > 50).length}</div>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4">
          <div className="text-[10px] font-mono text-[var(--color-fg-muted)]">Avg Burst Factor</div>
          <div className="text-xl font-serif text-[var(--color-cyan)] mt-1">
            {signals.length > 0 ? (signals.reduce((a, s) => a + (s.burst_factor || 1), 0) / signals.length).toFixed(1) : "—"}×
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {signals.map((s, i) => {
          const severity = severityLevel(s.score, s.burst_factor)
          const isExpanded = expanded === i
          return (
            <button
              key={i}
              onClick={() => setExpanded(isExpanded ? null : i)}
              className={`w-full text-left rounded-lg border transition-all p-4 ${
                isExpanded
                  ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                  : "border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)]"
              }`}
            >
              <div className="flex items-start gap-3">
                <span className="w-2 h-2 rounded-full shrink-0 mt-1" style={{ background: severity.color }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-widest uppercase">
                      {(s.signal || "").replace("_", " ")}
                    </span>
                    <span
                      className="text-[9px] font-mono tracking-wider uppercase px-1.5 py-0.5 rounded"
                      style={{
                        background: `${severity.color}15`,
                        color: severity.color,
                        border: `1px solid ${severity.color}30`,
                      }}
                    >
                      {severity.label}
                    </span>
                  </div>
                  <p className="text-sm font-serif text-[var(--color-fg)]">{s.keyword || s.entity || "Unknown"}</p>
                  <div className="flex gap-3 mt-2 text-[10px] font-mono text-[var(--color-fg-muted)]">
                    <span>Score: <span className="text-[var(--color-accent)]">{s.score.toFixed(1)}</span></span>
                    {s.recent_count !== undefined && <span>Articles: {s.recent_count}</span>}
                    {s.burst_factor !== undefined && (
                      <span>Burst: <span className={s.burst_factor > 20 ? "text-[var(--color-red)]" : ""}>{s.burst_factor.toFixed(1)}×</span></span>
                    )}
                  </div>
                  {isExpanded && s.burst_factor && (
                    <div className="mt-3 pt-3 border-t border-[var(--color-border)] text-[10px] font-mono text-[var(--color-fg-secondary)]">
                      <p>
                        Detected anomaly: <strong className="text-[var(--color-fg)]">{s.keyword || s.entity}</strong> is being mentioned at{" "}
                        <strong className="text-[var(--color-red)]">{s.burst_factor.toFixed(1)}×</strong> the normal rate.
                        {s.burst_factor > 20
                          ? " This represents a significant intelligence signal requiring attention."
                          : s.burst_factor > 5
                          ? " This warrants monitoring for escalation."
                          : " Normal fluctuation within expected parameters."}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {signals.length === 0 && (
        <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">No active signals at this time. Intelligence streams are nominal.</p>
        </div>
      )}
    </div>
  )
}
