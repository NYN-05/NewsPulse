import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { TrendingUp, Hash } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { CardSkeleton } from "@/components/ui/skeleton"
import { HorizontalBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { TrendData } from "@/types"

export function TrendsPage() {
  const [data, setData] = useState<TrendData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.trends().then((d) => { setData(d.top_keywords); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Trending Topics" description="Loading trending data..." />
      <CardSkeleton />
    </div>
  )

  const topCount = data[0]?.count ?? 1

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Trending Topics"
        description="The most frequently mentioned keywords across all news sources. These are the words and phrases dominating the news cycle right now. Larger bars mean more mentions."
      />

      <div className="rounded-xl border border-(--color-border) bg-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <Hash className="h-4 w-4 text-secondary" />
          <h3 className="font-semibold text-sm">Top Keywords by Frequency</h3>
        </div>
        <HorizontalBarChart
          data={data}
          xKey="word"
          yKey="count"
          color="var(--color-secondary)"
          height={Math.max(300, data.length * 26)}
        />
      </div>

      <div className="rounded-xl border border-(--color-border) bg-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-accent" />
          <h3 className="font-semibold text-sm">Keyword Cloud</h3>
        </div>
        <p className="mb-4 text-xs text-muted-foreground">
          Keywords sized by frequency. The most-mentioned words appear largest.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {data.slice(0, 50).map((t) => {
            const size = 0.7 + (t.count / topCount) * 1.3
            return (
              <span
                key={t.word}
                className="inline-block rounded-full border border-(--color-border) px-2.5 py-1 transition-colors hover:border-primary/50"
                style={{ fontSize: `${size * 0.875}rem` }}
              >
                {t.word}
                <span className="ml-1 text-xs text-muted-foreground">{t.count}</span>
              </span>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}
