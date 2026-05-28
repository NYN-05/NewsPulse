import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { LineChart, TrendingUp } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { ChartSkeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { SimpleAreaChart } from "@/charts/area-chart"
import { api } from "@/services/api"
import type { TopicCluster } from "@/types"

const chartColors = ["var(--color-primary)", "var(--color-secondary)", "var(--color-accent)", "var(--color-destructive)"]

export function EvolutionPage() {
  const [clusters, setClusters] = useState<TopicCluster[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.topicEvolution().then((d) => { setClusters(d.clusters || []); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Topic Evolution" description="Loading topic trajectories..." />
      {Array.from({ length: 3 }).map((_, i) => <ChartSkeleton key={i} />)}
    </div>
  )

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Topic Evolution Over Time"
        description={`${clusters.length} topic clusters tracked over time. These charts show how discussion volume for each topic has changed — growing topics are gaining traction, while shrinking topics are fading from the news cycle.`}
      />

      {clusters.length === 0 && (
        <div className="flex h-40 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-card)]">
          <p className="text-sm text-[var(--color-muted-foreground)]">No topic evolution data available.</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {clusters.map((c, idx) => {
          const trajectory = c.trajectory || []
          const isGrowing = c.momentum > 0

          return (
            <motion.div
              key={c.cluster}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5"
            >
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <LineChart className="h-4 w-4 text-[var(--color-primary)]" />
                  <h3 className="font-semibold text-sm">Cluster {c.cluster}{c.label ? ` — ${c.label}` : ""}</h3>
                </div>
                <div className="flex items-center gap-2">
                  <Badge>{c.total_articles} articles</Badge>
                  <Badge variant={isGrowing ? "positive" : "negative"}>
                    <span className="flex items-center gap-1">
                      {isGrowing ? <TrendingUp className="h-3 w-3" /> : null}
                      {c.momentum > 0 ? "+" : ""}{c.momentum.toFixed(1)}
                    </span>
                  </Badge>
                </div>
              </div>
              <p className="mb-4 text-xs text-[var(--color-muted-foreground)]">
                {isGrowing
                  ? "This topic is gaining traction — mention volume is increasing over time."
                  : "This topic is declining — mention volume is shrinking over time."}
              </p>
              {trajectory.length > 0 && (
                <SimpleAreaChart
                  data={trajectory.map((t) => ({ date: t.date.slice(5, 10), count: t.count }))}
                  xKey="date"
                  yKey="count"
                  color={chartColors[c.cluster % chartColors.length]}
                />
              )}
            </motion.div>
          )
        })}
      </div>
    </motion.div>
  )
}
