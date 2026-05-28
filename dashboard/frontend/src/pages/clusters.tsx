import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Layers, MessageSquare, Globe } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { CardSkeleton, ChartSkeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { SimpleBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { ClusterData } from "@/types"

export function ClustersPage() {
  const [data, setData] = useState<ClusterData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.clusters().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Topic Clusters" description="Loading clusters..." />
      <ChartSkeleton />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
    </div>
  )

  const sorted = [...data].sort((a, b) => b.count - a.count)

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Topic Clusters"
        description={`${data.length} topic clusters identified. Clusters group related articles together, revealing the main storylines and themes in the news. Each cluster represents a distinct topic being discussed across sources.`}
      />

      <div className="rounded-xl border border-(--color-border) bg-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <Layers className="h-4 w-4 text-primary" />
          <h3 className="font-semibold text-sm">Cluster Size Distribution</h3>
        </div>
        <p className="mb-4 text-xs text-muted-foreground">
          How many articles belong to each cluster. Larger clusters represent more dominant storylines.
        </p>
        <SimpleBarChart data={sorted} xKey="label" yKey="count" color="var(--color-primary)" height={300} />
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {sorted.map((c, i) => (
          <motion.div
            key={c.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.02 }}
            className="rounded-xl border border-(--color-border) bg-card p-4 transition-colors hover:border-primary/30"
          >
            <div className="mb-3 flex items-center justify-between">
              <span className="font-medium text-sm">{c.label}</span>
              <Badge variant={c.count > 50 ? "warning" : "default"}>{c.count} articles</Badge>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2 text-muted-foreground">
                <MessageSquare className="h-3 w-3" />
                <span>Sentiment: </span>
                <span className={cn(
                  "font-medium",
                  (c.avg_sentiment ?? 0) > 0.1 ? "text-emerald-400"
                  : (c.avg_sentiment ?? 0) < -0.1 ? "text-red-400"
                  : "text-foreground",
                )}>
                  {(c.avg_sentiment ?? 0).toFixed(3)}
                </span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Globe className="h-3 w-3" />
                <span>Top source: </span>
                <span className="font-medium text-foreground">{c.top_source}</span>
              </div>
            </div>
            <div className="mt-3 h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${(c.count / sorted[0].count) * 100}%` }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

function cn(...inputs: (string | undefined | false | null)[]) {
  return inputs.filter(Boolean).join(" ")
}
