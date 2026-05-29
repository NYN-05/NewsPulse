import { useState, useEffect } from "react"
import { api } from "@/services/api"
import type { AlertData } from "@/types"

export function AlertsPage() {
  const [data, setData] = useState<AlertData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.alerts().then(setData).catch(() => setData(null)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-xs font-mono text-[var(--color-fg-muted)]">Loading alerts...</div>
  if (!data?.alerts?.length) return <div className="text-xs font-mono text-[var(--color-fg-muted)]">No alerts</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-serif text-[var(--color-fg)]">Intelligence Alerts</h1>
          <p className="text-[10px] font-mono text-[var(--color-fg-muted)] mt-1">{data.alerts.length} total alerts</p>
        </div>
        <div className="flex gap-3 text-[10px] font-mono">
          <span className="text-[var(--color-red)]">{data.summary.high_severity} high</span>
          <span className="text-[var(--color-yellow)]">{data.summary.medium_severity} medium</span>
          <span className="text-[var(--color-fg-muted)]">{data.summary.low_severity} low</span>
        </div>
      </div>

      <div className="space-y-2">
        {data.alerts.map((a, i) => (
          <div key={i} className={`p-3 border rounded bg-[var(--color-card)] ${
            a.severity === "high" ? "border-[var(--color-red)]/30" : "border-[var(--color-border)]"
          }`}>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                a.severity === "high" ? "bg-[var(--color-red)]" :
                a.severity === "medium" ? "bg-[var(--color-yellow)]" : "bg-[var(--color-fg-muted)]"
              }`} />
              <span className="text-xs font-mono text-[var(--color-fg)]">{a.title}</span>
              <span className="ml-auto text-[9px] font-mono text-[var(--color-fg-muted)] uppercase">{a.type}</span>
            </div>
            <p className="mt-1 text-[10px] font-mono text-[var(--color-fg-muted)] pl-4">{a.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
