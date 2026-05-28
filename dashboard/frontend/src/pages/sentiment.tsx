import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { MessageSquare, Smile, Meh, Frown } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { ChartSkeleton } from "@/components/ui/skeleton"
import { SimplePieChart } from "@/charts/pie-chart"
import { api } from "@/services/api"
import type { SentimentData } from "@/types"

export function SentimentPage() {
  const [data, setData] = useState<SentimentData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.sentiment().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Sentiment Overview" description="Loading sentiment data..." />
      <ChartSkeleton />
    </div>
  )

  if (!data) return (
    <div className="space-y-6">
      <SectionHeader title="Sentiment Overview" description="No sentiment data available." />
    </div>
  )

  const pie = Object.entries(data.distribution).map(([name, value]) => ({ name, value }))

  const sentDesc =
    data.avg_compound > 0.15 ? "The overall tone of coverage is positive. Stories are predominantly favorable or optimistic."
    : data.avg_compound > 0.05 ? "Coverage leans slightly positive. Most stories carry a constructive or supportive tone."
    : data.avg_compound > -0.05 ? "Coverage is neutral. News reporting is balanced without strong emotional leaning."
    : data.avg_compound > -0.15 ? "Coverage leans slightly negative. Stories tend to be critical or cautious."
    : "Coverage is predominantly negative. Critical or alarming stories dominate the news landscape."

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Sentiment Overview"
        description={`${sentDesc} The average compound score is ${data.avg_compound.toFixed(4)} (range: -1 to +1).`}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-(--color-border) bg-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm">Sentiment Distribution</h3>
          </div>
          <p className="mb-4 text-xs text-muted-foreground">
            The breakdown of positive, negative, and neutral articles. This helps you understand the overall emotional tone of the news landscape.
          </p>
          <SimplePieChart data={pie} height={300} />
          <div className="mt-4 flex items-center justify-center gap-4 text-xs">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-400" /> Positive
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-400" /> Negative
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-gray-400" /> Neutral
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-(--color-border) bg-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm">Sentiment Breakdown</h3>
          </div>
          <p className="mb-4 text-xs text-muted-foreground">
            Detailed breakdown of sentiment categories. The compound score aggregates all article sentiments into a single measure.
          </p>
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border border-(--color-border) bg-muted/30 p-3.5">
              <div className="flex items-center gap-2">
                <Smile className="h-4 w-4 text-emerald-400" />
                <span className="text-sm font-medium">Compound Score</span>
              </div>
              <span className={cn(
                "text-lg font-bold",
                data.avg_compound > 0.1 ? "text-emerald-400"
                : data.avg_compound < -0.1 ? "text-red-400"
                : "text-foreground",
              )}>
                {data.avg_compound.toFixed(4)}
              </span>
            </div>
            {Object.entries(data.distribution).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between rounded-lg border border-(--color-border) bg-muted/30 p-3.5">
                <div className="flex items-center gap-2">
                  {k === "positive" && <Smile className="h-4 w-4 text-emerald-400" />}
                  {k === "negative" && <Frown className="h-4 w-4 text-red-400" />}
                  {k === "neutral" && <Meh className="h-4 w-4 text-gray-400" />}
                  <span className="text-sm capitalize font-medium">{k}</span>
                </div>
                <span className="font-bold">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function cn(...inputs: (string | undefined | false | null)[]) {
  return inputs.filter(Boolean).join(" ")
}
