import { useState } from "react"
import { Card, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { api } from "@/services/api"
import type { SearchResult } from "@/types"

export function SearchPage() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const d = await api.search(query)
      setResults(d.results || [])
    } catch {
      setResults([])
    }
    setLoading(false)
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Semantic Search</h1>
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search articles semantically..."
          className="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-2.5 text-sm outline-none focus:border-[var(--color-primary)]"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="rounded-xl bg-[var(--color-primary)] px-6 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "..." : "Search"}
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-[var(--color-muted-foreground)]">{results.length} results</p>
          {results.map((r, i) => (
            <Card key={i}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-medium">{r.title}</p>
                  <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">{r.source} · {r.category}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge>{r.sentiment}</Badge>
                  <span className="text-sm font-bold text-[var(--color-primary)]">{(r.score * 100).toFixed(1)}%</span>
                </div>
              </div>
              {r.snippet && <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">{r.snippet.slice(0, 200)}</p>}
              {r.link && (
                <a href={r.link} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-xs text-[var(--color-primary)] hover:underline">
                  Read more →
                </a>
              )}
            </Card>
          ))}
        </div>
      )}

      {searched && !loading && results.length === 0 && (
        <p className="text-center text-sm text-[var(--color-muted-foreground)]">No results found</p>
      )}
    </div>
  )
}
