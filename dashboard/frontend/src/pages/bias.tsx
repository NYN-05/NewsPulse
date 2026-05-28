import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Scale, ShieldCheck, TrendingUp, AlertTriangle } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { ChartSkeleton, CardSkeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { SimplePieChart } from "@/charts/pie-chart"
import { SimpleBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { BiasData, SourceReliability } from "@/types"

export function BiasPage() {
  const [bias, setBias] = useState<BiasData | null>(null)
  const [reliability, setReliability] = useState<SourceReliability>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.bias(), api.sourceReliability()]).then(([b, r]) => {
      setBias(b); setReliability(r); setLoading(false)
    })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Bias & Source Reliability" description="Loading quality metrics..." />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartSkeleton />
        <CardSkeleton />
      </div>
      <CardSkeleton />
    </div>
  )

  const pieData = bias ? Object.entries(bias.political_leaning).map(([name, value]) => ({ name, value })) : []
  const relData = Object.entries(reliability).map(([name, v]) => ({
    name: name.length > 25 ? name.slice(0, 25) + "..." : name,
    score: v.reliability_score,
    articles: v.total_articles,
  }))

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Bias & Source Reliability"
        description="Understand the editorial stance and trustworthiness of your news sources. Political leaning shows how sources lean across the spectrum. Reliability scores reflect consistency and factual reporting quality."
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Political Leaning */}
        {pieData.length > 0 && (
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5">
            <div className="mb-4 flex items-center gap-2">
              <Scale className="h-4 w-4 text-[var(--color-primary)]" />
              <h3 className="font-semibold text-sm">Political Leaning</h3>
            </div>
            <p className="mb-4 text-xs text-[var(--color-muted-foreground)]">
              How sources are distributed across the political spectrum. This helps identify potential bias in coverage.
            </p>
            <SimplePieChart data={pieData} height={280} />
            <div className="mt-4 flex flex-wrap items-center justify-center gap-3 text-xs">
              {pieData.map((d) => (
                <span key={d.name} className="flex items-center gap-1.5 capitalize">
                  <span className={cn(
                    "inline-block h-2.5 w-2.5 rounded-full",
                    d.name === "left" && "bg-blue-400",
                    d.name === "center" && "bg-gray-400",
                    d.name === "right" && "bg-red-400",
                  )} />
                  {d.name} ({d.value})
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Aggregate Metrics */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5">
          <div className="mb-4 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-[var(--color-primary)]" />
            <h3 className="font-semibold text-sm">Quality Metrics</h3>
          </div>
          <p className="mb-4 text-xs text-[var(--color-muted-foreground)]">
            Aggregate quality scores across all sources. Clickbait and emotional scores measure sensationalism in headlines.
          </p>
          <div className="space-y-3">
            <MetricRow
              icon={AlertTriangle}
              label="Clickbait Score"
              value={bias?.avg_clickbait ?? 0}
              format=".4f"
              higherIs={bias ? bias.avg_clickbait > 0.5 : false ? "warning" : "better"}
            />
            <MetricRow
              icon={TrendingUp}
              label="Emotional Score"
              value={bias?.avg_emotional ?? 0}
              format=".4f"
              higherIs={bias ? bias.avg_emotional > 0.5 : false ? "warning" : "better"}
            />
          </div>
          <div className="mt-4 rounded-lg bg-[var(--color-muted)]/30 p-3">
            <p className="text-xs text-[var(--color-muted-foreground)]">
              <strong>What this means:</strong> Lower clickbait scores indicate more straightforward, factual headlines. Lower emotional scores suggest more objective reporting.
            </p>
          </div>
        </div>

        {/* Source Reliability */}
        {relData.length > 0 && (
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 lg:col-span-2">
            <div className="mb-4 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-[var(--color-primary)]" />
              <h3 className="font-semibold text-sm">Source Reliability Scores</h3>
            </div>
            <p className="mb-4 text-xs text-[var(--color-muted-foreground)]">
              Each source's reliability score based on historical accuracy, consistency, and reporting quality. Higher scores mean more trustworthy sources.
            </p>
            <SimpleBarChart
              data={relData}
              xKey="name"
              yKey="score"
              color="var(--color-primary)"
              height={Math.max(200, relData.length * 30)}
            />
          </div>
        )}
      </div>
    </motion.div>
  )
}

function MetricRow({ icon: Icon, label, value, format, higherIs }: {
  icon: React.ElementType
  label: string
  value: number
  format: string
  higherIs: "warning" | "better"
}) {
  const color = higherIs === "warning"
    ? value > 0.5 ? "text-red-400" : "text-emerald-400"
    : "text-[var(--color-foreground)]"

  return (
    <div className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-muted)]/30 p-3.5">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-[var(--color-muted-foreground)]" />
        <span className="text-sm">{label}</span>
      </div>
      <span className={cn("text-lg font-bold", color)}>
        {value.toFixed(4)}
      </span>
    </div>
  )
}

function cn(...inputs: (string | undefined | false | null)[]) {
  return inputs.filter(Boolean).join(" ")
}
