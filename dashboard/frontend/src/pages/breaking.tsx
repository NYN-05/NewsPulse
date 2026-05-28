import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Zap, TrendingUp, Activity } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { CardSkeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { api } from "@/services/api"
import type { BreakingEvent } from "@/types"

const sigColors: Record<string, string> = {
  keyword_burst: "warning",
  entity_spike: "info",
}

const sigLabels: Record<string, string> = {
  keyword_burst: "Keyword Burst — unusual spike in keyword mentions",
  entity_spike: "Entity Spike — surge in entity name appearances",
}

const sigIcons: Record<string, React.ElementType> = {
  keyword_burst: TrendingUp,
  entity_spike: Activity,
}

export function BreakingPage() {
  const [data, setData] = useState<BreakingEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.breaking().then((d) => { setData(d || []); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Breaking News" description="Detecting unusual activity..." />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
    </div>
  )

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Breaking News Signals"
        description={`${data.length} signals detected. These are keywords and entities showing unusual spikes in mention frequency — potentially indicating breaking or rapidly developing stories.`}
      />

      {data.length === 0 && (
        <div className="flex h-40 items-center justify-center rounded-xl border border-(--color-border) bg-card">
          <p className="text-sm text-muted-foreground">No breaking signals at this time.</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {data.map((e, i) => {
          const kw = e.keyword || e.entity || "unknown"
          const Icon = sigIcons[e.signal] || Zap
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="rounded-xl border border-(--color-border) bg-card p-4 transition-colors hover:border-accent/50"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent]/10">
                    <Icon className="h-4 w-4 text-accent" />
                  </div>
                  <div>
                    <p className="font-medium capitalize">{kw}</p>
                    <Badge variant={sigColors[e.signal] || "default"}>
                      {e.signal.replace("_", " ")}
                    </Badge>
                  </div>
                </div>
                <span className="text-xl font-bold text-accent">{e.score.toFixed(0)}</span>
              </div>
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span>Articles: {e.recent_count || 0}</span>
                <span>Burst: {e.burst_factor?.toFixed(1) || "—"}× normal</span>
              </div>
              <p className="mt-2 text-[11px] text-muted-foreground italic">
                {sigLabels[e.signal] || "Anomaly detected"}
              </p>
            </motion.div>
          )
        })}
      </div>
    </motion.div>
  )
}
