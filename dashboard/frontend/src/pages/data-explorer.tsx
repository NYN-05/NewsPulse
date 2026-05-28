import { useEffect, useState, useCallback } from "react"
import { motion } from "framer-motion"
import { Table2, Search, RefreshCw, Filter } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { Badge } from "@/components/ui/badge"
import { api } from "@/services/api"
import type { ArticleRecord } from "@/types"

export function DataExplorerPage() {
  const [data, setData] = useState<ArticleRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [sourceFilter, setSourceFilter] = useState("")

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

  const categories = [...new Set(data.map((r) => r.category).filter(Boolean))].sort() as string[]
  const sources = [...new Set(data.map((r) => r.source).filter(Boolean))].sort() as string[]

  const filtered = data.filter((r) => {
    if (search) {
      const q = search.toLowerCase()
      if (!(r.title || "").toLowerCase().includes(q) &&
          !(r.source || "").toLowerCase().includes(q)) return false
    }
    if (categoryFilter && r.category !== categoryFilter) return false
    if (sourceFilter && r.source !== sourceFilter) return false
    return true
  })

  const sentVariant = (s?: string) => {
    if (s === "positive") return "positive" as const
    if (s === "negative") return "negative" as const
    return "neutral" as const
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Data Explorer"
        description={`Browse and filter ${data.length} articles from your news database. Use the search bar and filters to find specific stories, or scroll through the full list.`}
      />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--color-muted-foreground)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by title or source..."
            className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] py-2 pl-8 pr-3 text-sm outline-none focus:border-[var(--color-primary)] transition-colors"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2 text-xs outline-none"
        >
          <option value="">All categories</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2 text-xs outline-none"
        >
          <option value="">All sources</option>
          {sources.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button onClick={fetchData} className="rounded-lg border border-[var(--color-border)] p-2 hover:bg-[var(--color-muted)] transition-colors" title="Refresh">
          <RefreshCw className="h-4 w-4" />
        </button>
        <Badge variant="default" className="ml-auto">
          <Filter className="h-3 w-3 mr-1" />
          {filtered.length} of {data.length}
        </Badge>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-card)]">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] bg-[var(--color-muted)]/30">
                <th className="p-3 text-left text-xs font-medium text-[var(--color-muted-foreground)]">Title</th>
                <th className="p-3 text-left text-xs font-medium text-[var(--color-muted-foreground)]">Source</th>
                <th className="p-3 text-left text-xs font-medium text-[var(--color-muted-foreground)]">Sentiment</th>
                <th className="p-3 text-left text-xs font-medium text-[var(--color-muted-foreground)]">Category</th>
                <th className="p-3 text-left text-xs font-medium text-[var(--color-muted-foreground)]">Lang</th>
                <th className="p-3 text-left text-xs font-medium text-[var(--color-muted-foreground)]">Virality</th>
                <th className="p-3 text-left text-xs font-medium text-[var(--color-muted-foreground)]">Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-sm text-[var(--color-muted-foreground)]">
                    <span className="inline-flex items-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-border)] border-t-[var(--color-primary)]" />
                      Loading...
                    </span>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-sm text-[var(--color-muted-foreground)]">
                    No articles match your filters.
                  </td>
                </tr>
              ) : (
                filtered.map((r, i) => (
                  <tr key={i} className="border-b border-[var(--color-border)] transition-colors hover:bg-[var(--color-muted)]/20">
                    <td className="max-w-xs truncate p-3 font-medium">{r.title}</td>
                    <td className="p-3 text-[var(--color-muted-foreground)]">{r.source}</td>
                    <td className="p-3">
                      <Badge variant={sentVariant(r.sentiment)} className="text-[10px]">{r.sentiment}</Badge>
                    </td>
                    <td className="p-3 text-[var(--color-muted-foreground)]">{r.category}</td>
                    <td className="p-3 text-[var(--color-muted-foreground)] text-xs">{r.language || "—"}</td>
                    <td className="p-3 text-xs">{(r.virality_score ?? 0).toFixed(3)}</td>
                    <td className="p-3 text-xs text-[var(--color-muted-foreground)]">{r.published?.slice(0, 10)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  )
}
