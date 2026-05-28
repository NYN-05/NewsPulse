import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Flame, TrendingUp, ExternalLink } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { CardSkeleton, ChartSkeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { SimpleLineChart } from "@/charts/line-chart"
import { api } from "@/services/api"
import type { ViralityData } from "@/types"

export function ViralityPage() {
  const [data, setData] = useState<ViralityData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.virality().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Virality Analysis" description="Loading virality data..." />
      <ChartSkeleton />
      <CardSkeleton />
    </div>
  )

  if (!data) return (
    <div className="space-y-6">
      <SectionHeader title="Virality Analysis" description="No virality data available." />
    </div>
  )

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Virality Analysis"
        description={`Average virality score: ${data.avg_virality.toFixed(3)}. Virality measures how likely articles are to be shared and discussed — higher scores indicate more contagious content.`}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-(--color-border) bg-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-accent" />
            <h3 className="font-semibold text-sm">Virality Score Distribution</h3>
          </div>
          <p className="mb-4 text-xs text-muted-foreground">
            How viral scores are spread across articles. A right-skewed distribution means most content has moderate virality, while the tail contains breakout hits.
          </p>
          <SimpleLineChart
            data={data.distribution.map((v, i) => ({ index: i, score: v }))}
            xKey="index"
            yKey="score"
            color="var(--color-accent)"
            height={300}
          />
        </div>

        <div className="rounded-xl border border-(--color-border) bg-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <Flame className="h-4 w-4 text-accent" />
            <h3 className="font-semibold text-sm">Most Viral Articles</h3>
          </div>
          <p className="mb-4 text-xs text-muted-foreground">
            Top-performing articles by virality score. These stories are generating the most engagement and discussion.
          </p>
          <div className="space-y-2">
            {data.top_viral.map((a, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border border-(--color-border) bg-muted/30 p-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{a.title}</p>
                  <p className="text-xs text-muted-foreground">{a.source}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-2">
                  <Badge variant={a.sentiment === "positive" ? "positive" : a.sentiment === "negative" ? "negative" : "neutral"}>
                    {a.sentiment}
                  </Badge>
                  <span className="font-bold text-accent">{Number(a.virality_score).toFixed(3)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
