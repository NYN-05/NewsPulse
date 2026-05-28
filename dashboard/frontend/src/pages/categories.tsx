import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { FolderTree, Layers } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { CardSkeleton } from "@/components/ui/skeleton"
import { HorizontalBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { CategoryData } from "@/types"

export function CategoriesPage() {
  const [data, setData] = useState<CategoryData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.categories().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <SectionHeader title="Categories" description="Loading category data..." />
      <CardSkeleton />
    </div>
  )

  const total = data.reduce((sum, c) => sum + c.count, 0)

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Categories"
        description={`${data.length} categories identified across ${total} articles. Categories group articles by subject matter, helping you see which topics are getting the most coverage at a glance.`}
      />

      <div className="rounded-xl border border-(--color-border) bg-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <FolderTree className="h-4 w-4 text-accent" />
          <h3 className="font-semibold text-sm">Article Categories</h3>
        </div>
        <p className="mb-4 text-xs text-muted-foreground">
          Each bar represents a category and its article count. Longer bars mean more coverage in that area.
        </p>
        <HorizontalBarChart
          data={data}
          xKey="name"
          yKey="count"
          color="var(--color-accent)"
          height={Math.max(300, data.length * 26)}
        />
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {data.slice(0, 20).map((c) => (
          <div key={c.name} className="rounded-xl border border-(--color-border) bg-card p-3 text-center">
            <Layers className="mx-auto h-5 w-5 text-accent mb-1.5" />
            <p className="text-sm font-medium truncate" title={c.name}>{c.name}</p>
            <p className="text-xs text-muted-foreground">{c.count} articles</p>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
