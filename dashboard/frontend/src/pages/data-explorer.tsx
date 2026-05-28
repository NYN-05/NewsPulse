import { useEffect, useState, useCallback } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { api } from "@/services/api"
import type { ArticleRecord } from "@/types"

export function DataExplorerPage() {
  const [data, setData] = useState<ArticleRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [sortKey, setSortKey] = useState<string>("published")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const d = await api.data({ limit: "200" })
      setData(d)
    } catch {
      setData([])
    }
    setLoading(false)
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const filtered = data
    .filter((r) => {
      if (!search) return true
      const q = search.toLowerCase()
      return (r.title || "").toLowerCase().includes(q) ||
             (r.source || "").toLowerCase().includes(q)
    })

  const sentVariant = (s?: string) => {
    if (s === "positive") return "positive"
    if (s === "negative") return "negative"
    return "neutral"
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Data Explorer</h1>
        <Badge>{data.length} articles loaded</Badge>
      </div>

      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Filter by title or source..."
        className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-2 text-sm outline-none focus:border-[var(--color-primary)]"
      />

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left">
                <th className="p-2">Title</th>
                <th className="p-2">Source</th>
                <th className="p-2">Sentiment</th>
                <th className="p-2">Category</th>
                <th className="p-2">Language</th>
                <th className="p-2">Virality</th>
                <th className="p-2">Published</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => (
                <tr key={i} className="border-b border-[var(--color-border)]">
                  <td className="max-w-xs truncate p-2 font-medium">{r.title}</td>
                  <td className="p-2 text-[var(--color-muted-foreground)]">{r.source}</td>
                  <td className="p-2"><Badge variant={sentVariant(r.sentiment)}>{r.sentiment}</Badge></td>
                  <td className="p-2 text-[var(--color-muted-foreground)]">{r.category}</td>
                  <td className="p-2 text-[var(--color-muted-foreground)]">{r.language || "—"}</td>
                  <td className="p-2">{(r.virality_score ?? 0).toFixed(3)}</td>
                  <td className="p-2 text-xs text-[var(--color-muted-foreground)]">{r.published?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
