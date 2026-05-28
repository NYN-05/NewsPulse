import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import {
  Newspaper, TrendingUp, MessageSquare, Activity,
  Globe, BarChart3, Zap, ExternalLink,
} from "lucide-react"
import { CardSkeleton, ChartSkeleton } from "@/components/ui/skeleton"
import { SectionHeader } from "@/components/ui/section-header"
import { SimplePieChart } from "@/charts/pie-chart"
import { SimpleBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { Summary, SentimentData, CategoryData, TrendData, ClusterData } from "@/types"

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.05 } },
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

function KpiCard({ title, value, icon: Icon, subtitle, trend }: {
  title: string
  value: string | number
  icon: React.ElementType
  subtitle?: string
  trend?: { direction: "up" | "down" | "neutral"; label: string }
}) {
  return (
    <motion.div variants={item} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 transition-colors hover:border-[var(--color-primary)]/30">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-[var(--color-muted-foreground)] uppercase tracking-wider">{title}</p>
          <p className="mt-1.5 text-2xl font-bold tracking-tight">{value}</p>
          {subtitle && <p className="mt-0.5 text-xs text-[var(--color-muted-foreground)]">{subtitle}</p>}
          {trend && (
            <p className={cn(
              "mt-1 text-xs font-medium",
              trend.direction === "up" && "text-emerald-400",
              trend.direction === "down" && "text-red-400",
              trend.direction === "neutral" && "text-[var(--color-muted-foreground)]",
            )}>
              {trend.label}
            </p>
          )}
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-primary)]/10">
          <Icon className="h-4 w-4 text-[var(--color-primary)]" />
        </div>
      </div>
    </motion.div>
  )
}

function cn(...inputs: (string | undefined | false | null)[]) {
  return inputs.filter(Boolean).join(" ")
}

function TrendingPill({ word, count, maxCount }: { word: string; count: number; maxCount: number }) {
  const intensity = count / maxCount
  const opacity = 0.15 + intensity * 0.45

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-[var(--color-border)] px-3 py-1 text-sm transition-colors hover:border-[var(--color-primary)]/50 hover:bg-[var(--color-primary)]/5"
      style={{ background: `rgba(99,102,241,${opacity})` }}
    >
      <TrendingUp className="h-3 w-3 text-[var(--color-primary)]" />
      {word}
      <span className="text-xs text-[var(--color-muted-foreground)]">{count}</span>
    </span>
  )
}

export function OverviewPage() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [sentiment, setSentiment] = useState<SentimentData | null>(null)
  const [categories, setCategories] = useState<CategoryData[]>([])
  const [trends, setTrends] = useState<TrendData[]>([])
  const [clusters, setClusters] = useState<ClusterData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.summary(),
      api.sentiment(),
      api.categories(),
      api.trends(),
      api.clusters(),
    ]).then(([s, sent, cats, tr, cl]) => {
      setSummary(s)
      setSentiment(sent)
      setCategories(cats)
      setTrends(tr.top_keywords)
      setClusters(cl)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="News Pulse Dashboard"
          description="Loading your media intelligence overview..."
        />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      </div>
    )
  }

  const sentPie = sentiment
    ? Object.entries(sentiment.distribution).map(([name, value]) => ({ name, value }))
    : []

  const maxTrendCount = Math.max(...trends.map((t) => t.count), 1)
  const topClusters = clusters.sort((a, b) => b.count - a.count).slice(0, 8)

  const avgSent = summary?.avg_sentiment ?? 0
  const sentimentLabel =
    avgSent > 0.1 ? "Positive — good news dominates the coverage"
    : avgSent < -0.1 ? "Negative — critical stories are prominent"
    : "Neutral — coverage is balanced"

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Header */}
      <motion.div variants={item}>
        <SectionHeader
          title="News Pulse Dashboard"
          description={`Your real-time intelligence overview across ${summary?.sources ?? 0} sources. ${summary?.total_articles ?? 0} articles analyzed.`}
        />
      </motion.div>

      {/* KPI Cards */}
      <motion.div variants={container} className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
        <KpiCard title="Total Articles" value={summary?.total_articles ?? 0} icon={Newspaper} subtitle="Across all sources" />
        <KpiCard
          title="Average Sentiment"
          value={avgSent.toFixed(2)}
          icon={MessageSquare}
          subtitle={sentimentLabel}
          trend={{
            direction: avgSent > 0.05 ? "up" : avgSent < -0.05 ? "down" : "neutral",
            label: avgSent > 0.05 ? "Positive coverage" : avgSent < -0.05 ? "Negative coverage" : "Neutral coverage",
          }}
        />
        <KpiCard title="Active Sources" value={summary?.sources ?? 0} icon={Globe} subtitle="News outlets tracked" />
        <KpiCard
          title="Avg Virality"
          value={summary?.avg_virality.toFixed(2) ?? "—"}
          icon={Zap}
          subtitle="How shareable content is"
        />
        <KpiCard title="Categories" value={categories.length} icon={BarChart3} subtitle="Topics being discussed" />
        <KpiCard title="Vector Index" value={summary?.vector_indexed ?? 0} icon={Activity} subtitle="Articles searchable" />
      </motion.div>

      {/* Sentiment + Trending */}
      <motion.div variants={item} className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Sentiment Snapshot */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="h-4 w-4 text-[var(--color-primary)]" />
            <h3 className="font-semibold text-sm">Sentiment at a Glance</h3>
          </div>
          <p className="text-xs text-[var(--color-muted-foreground)] mb-4">
            {sentimentLabel}. The pie chart shows the proportion of positive, negative, and neutral stories.
          </p>
          {sentPie.length > 0 && <SimplePieChart data={sentPie} />}
          <div className="mt-3 flex items-center gap-2 text-xs text-[var(--color-muted-foreground)]">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" /> Positive
            <span className="inline-block h-2 w-2 rounded-full bg-red-400 ml-2" /> Negative
            <span className="inline-block h-2 w-2 rounded-full bg-gray-400 ml-2" /> Neutral
          </div>
        </div>

        {/* Trending Now */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 lg:col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-[var(--color-accent)]" />
            <h3 className="font-semibold text-sm">Trending Now</h3>
          </div>
          <p className="text-xs text-[var(--color-muted-foreground)] mb-4">
            Most frequently mentioned keywords across all sources. Larger badges indicate higher mention volume.
          </p>
          <div className="flex flex-wrap gap-2">
            {trends.slice(0, 30).map((t) => (
              <TrendingPill key={t.word} word={t.word} count={t.count} maxCount={maxTrendCount} />
            ))}
          </div>
          {trends.length > 30 && (
            <p className="mt-3 text-xs text-[var(--color-muted-foreground)]">
              +{trends.length - 30} more keywords
            </p>
          )}
        </div>
      </motion.div>

      {/* Hot Topics + Categories */}
      <motion.div variants={item} className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Hot Topics */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="h-4 w-4 text-[var(--color-secondary)]" />
            <h3 className="font-semibold text-sm">Most Discussed Topics Today</h3>
          </div>
          <p className="text-xs text-[var(--color-muted-foreground)] mb-4">
            Top article clusters ranked by volume. Click a topic to see which sources are driving the conversation.
          </p>
          <div className="space-y-2">
            {topClusters.map((c) => (
              <div
                key={c.label}
                className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-muted)]/30 px-3 py-2"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-sm truncate">{c.label}</span>
                  {c.count > 50 && (
                    <span className="shrink-0 rounded-full bg-red-500/10 px-1.5 py-0.5 text-[10px] font-medium text-red-400">
                      Hot
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-2">
                  <span className="text-xs text-[var(--color-muted-foreground)]">{c.count} articles</span>
                  <span className={cn(
                    "text-xs font-medium",
                    (c.avg_sentiment ?? 0) > 0.1 ? "text-emerald-400"
                    : (c.avg_sentiment ?? 0) < -0.1 ? "text-red-400"
                    : "text-[var(--color-muted-foreground)]",
                  )}>
                    {(c.avg_sentiment ?? 0) > 0.1 ? "Positive"
                    : (c.avg_sentiment ?? 0) < -0.1 ? "Negative"
                    : "Neutral"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5">
          <div className="flex items-center gap-2 mb-3">
            <Globe className="h-4 w-4 text-[var(--color-accent)]" />
            <h3 className="font-semibold text-sm">Category Breakdown</h3>
          </div>
          <p className="text-xs text-[var(--color-muted-foreground)] mb-4">
            How articles are distributed across categories. This shows which subjects are getting the most coverage.
          </p>
          <SimpleBarChart
            data={categories.slice(0, 15)}
            xKey="name"
            yKey="count"
            color="var(--color-accent)"
            height={280}
          />
        </div>
      </motion.div>

      {/* Quick Links */}
      <motion.div variants={item} className="flex flex-wrap gap-2">
        {[
          { id: "trends", label: "View Trending Topics", icon: TrendingUp },
          { id: "breaking", label: "Breaking News", icon: Zap },
          { id: "clusters", label: "All Topic Clusters", icon: BarChart3 },
        ].map((link) => {
          const Icon = link.icon
          return (
            <span
              key={link.id}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-primary)] hover:bg-[var(--color-primary)]/5 transition-colors cursor-pointer"
            >
              <Icon className="h-3 w-3" />
              {link.label}
              <ExternalLink className="h-3 w-3" />
            </span>
          )
        })}
      </motion.div>
    </motion.div>
  )
}
