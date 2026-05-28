import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { TrendingUp, Users, Calendar } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { CardSkeleton, ChartSkeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { SimpleBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { EntityTrend } from "@/types"

export function EntityTrendsPage() {
  const [data, setData] = useState<EntityTrend[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.entityTrends().then((d) => { setData(d || []); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Entity Trends" description="Loading entity data..." />
      <ChartSkeleton />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
    </div>
  )

  const momentumData = data.map((e) => ({ entity: e.entity, momentum: e.momentum }))
  const hotEntities = [...data].sort((a, b) => b.momentum - a.momentum).slice(0, 6)

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Entity Trends"
        description={`Tracking ${data.length} named entities (people, organizations, locations) across news sources. Momentum scores show which entities are gaining or losing attention — positive momentum means increasing mentions.`}
      />

      <div className="rounded-xl border border-(--color-border) bg-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-accent" />
          <h3 className="font-semibold text-sm">Entity Momentum</h3>
        </div>
        <p className="mb-4 text-xs text-muted-foreground">
          How each entity's mention frequency is changing. Positive bars mean rising attention; negative bars indicate fading interest.
        </p>
        <SimpleBarChart
          data={momentumData}
          xKey="entity"
          yKey="momentum"
          color="var(--color-accent)"
          height={Math.max(250, momentumData.length * 28)}
        />
      </div>

      <h3 className="text-sm font-semibold">Top Entities by Momentum</h3>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {hotEntities.map((e, i) => (
          <motion.div
            key={e.entity}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
            className="rounded-xl border border-(--color-border) bg-card p-4 transition-colors hover:border-accent/30"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-accent" />
                <span className="font-medium capitalize">{e.entity}</span>
              </div>
              <Badge variant={e.momentum > 50 ? "warning" : e.momentum > 0 ? "positive" : "negative"}>
                {e.momentum > 0 ? "+" : ""}{e.momentum.toFixed(1)}
              </Badge>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
              <div>
                <p className="font-medium text-foreground">{e.total_mentions}</p>
                <p>Total mentions</p>
              </div>
              <div>
                <p className="font-medium text-foreground">{e.recent_mentions}</p>
                <p>Recent mentions</p>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-1.5 text-[10px] text-muted-foreground">
              <Calendar className="h-3 w-3" />
              Peak: {e.peak_date}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}
