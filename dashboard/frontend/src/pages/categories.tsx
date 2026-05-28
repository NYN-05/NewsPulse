import { useEffect, useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/loading"
import { HorizontalBarChart } from "@/charts/bar-chart"
import { api } from "@/services/api"
import type { CategoryData } from "@/types"

export function CategoriesPage() {
  const [data, setData] = useState<CategoryData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.categories().then((d) => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <Spinner className="mt-20" />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Categories</h1>
      <Card>
        <CardTitle>Article Categories</CardTitle>
        <HorizontalBarChart data={data} xKey="name" yKey="count" height={Math.max(300, data.length * 25)} />
      </Card>
    </div>
  )
}
