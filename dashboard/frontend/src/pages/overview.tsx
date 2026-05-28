import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { MetricCard } from "@/components/ui/metric-card"
import { Card, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/loading"
import { SimpleBarChart } from "@/charts/bar-chart"
import { SimplePieChart } from "@/charts/pie-chart"
import { SimpleLineChart } from "@/charts/line-chart"
import { api } from "@/services/api"
import type { Summary, SentimentData, CategoryData, TrendData, ClusterData, ViralityData, LanguageData, SourceCount } from "@/types"

export function OverviewPage() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [sentiment, setSentiment] = useState<SentimentData | null>(null)
  const [categories, setCategories] = useState<CategoryData[]>([])
  const [trends, setTrends] = useState<TrendData[]>([])
  const [clusters, setClusters] = useState<ClusterData[]>([])
  const [virality, setVirality] = useState<ViralityData | null>(null)
  const [languages, setLanguages] = useState<LanguageData[]>([])
  const [sources, setSources] = useState<SourceCount[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.summary(), api.sentiment(), api.categories(), api.trends(),
      api.clusters(), api.virality(), api.languages(), api.sources(),
    ]).then(([s, sent, cats, tr, cl, vir, lang, src]) => {
      setSummary(s)
      setSentiment(sent)
      setCategories(cats)
      setTrends(tr.top_keywords)
      setClusters(cl)
      setVirality(vir)
      setLanguages(lang)
      setSources(src)
      setLoading(false)
    })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  const sentPie = sentiment ? Object.entries(sentiment.distribution).map(([name, value]) => ({ name, value })) : []

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <h1 className="text-xl font-bold">Dashboard Overview</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
        <MetricCard title="Total Articles" value={summary?.total_articles ?? 0} icon="📄" />
        <MetricCard title="Avg Sentiment" value={summary?.avg_sentiment.toFixed(3) ?? "—"} icon="📊" />
        <MetricCard title="Sensationalism" value={summary?.avg_sensationalism.toFixed(3) ?? "—"} icon="⚠️" />
        <MetricCard title="Virality" value={summary?.avg_virality.toFixed(3) ?? "—"} icon="🔥" />
        <MetricCard title="Sources" value={summary?.sources ?? 0} icon="📡" />
        <MetricCard title="Vector Index" value={summary?.vector_indexed ?? 0} icon="🔍" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Sentiment */}
        <Card>
          <CardTitle>Sentiment Distribution</CardTitle>
          {sentPie.length > 0 && <SimplePieChart data={sentPie} />}
        </Card>

        {/* Top Keywords */}
        <Card>
          <CardTitle>Top Keywords</CardTitle>
          <SimpleBarChart data={trends.slice(0, 15)} xKey="word" yKey="count" color="var(--color-secondary)" height={250} />
        </Card>

        {/* Categories */}
        <Card>
          <CardTitle>Categories</CardTitle>
          <SimpleBarChart data={categories.slice(0, 12)} xKey="name" yKey="count" color="var(--color-accent)" height={250} />
        </Card>

        {/* Clusters */}
        <Card>
          <CardTitle>Topic Clusters</CardTitle>
          <SimpleBarChart data={clusters} xKey="label" yKey="count" color="var(--color-primary)" height={250} />
        </Card>

        {/* Virality Distribution */}
        {virality && (
          <Card>
            <CardTitle>Virality Score Distribution</CardTitle>
            <SimpleLineChart
              data={virality.distribution.map((v, i) => ({ index: i, score: v }))}
              xKey="index"
              yKey="score"
              color="var(--color-accent)"
            />
          </Card>
        )}

        {/* Languages */}
        <Card>
          <CardTitle>Language Distribution</CardTitle>
          <SimpleBarChart data={languages} xKey="code" yKey="count" color="var(--color-secondary)" height={250} />
        </Card>
      </div>
    </motion.div>
  )
}
