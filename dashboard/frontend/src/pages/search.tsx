import { useState, useRef, useEffect } from "react"
import { motion } from "framer-motion"
import { Search, ExternalLink, Sparkles, X } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { Badge } from "@/components/ui/badge"
import { api } from "@/services/api"
import type { SearchResult } from "@/types"

export function SearchPage() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

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
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SectionHeader
        title="Semantic Search"
        description="Search across all indexed articles using AI-powered semantic understanding. Results are ranked by relevance — even if they don't share exact keywords with your query. Try searching for topics, entities, or concepts."
      />

      {/* Search Bar */}
      <div className="rounded-xl border border-(--color-border) bg-card p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder='e.g. "climate policy impact on energy markets"...'
              className="w-full rounded-lg border border-(--color-border) bg-muted/50 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-primary transition-colors"
            />
            {query && (
              <button onClick={() => { setQuery(""); setResults([]); setSearched(false) }} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40 transition-opacity"
          >
            {loading ? (
              <span className="flex items-center gap-1.5">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Searching
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5" />
                Search
              </span>
            )}
          </button>
        </div>
        <p className="mt-2 text-[11px] text-muted-foreground">
          Tip: Use natural language queries for best results. The search understands concepts, not just keywords.
        </p>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Found {results.length} relevant result{results.length !== 1 ? "s" : ""} for "{query}"
          </p>
          {results.map((r, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="rounded-xl border border-(--color-border) bg-card p-4 transition-colors hover:border-primary/30"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{r.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {r.source}
                    {r.category ? ` · ${r.category}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant={r.sentiment === "positive" ? "positive" : r.sentiment === "negative" ? "negative" : "neutral"}>
                    {r.sentiment}
                  </Badge>
                  <span className="text-sm font-bold text-primary">
                    {(r.score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              {r.snippet && (
                <p className="mt-2 text-sm text-muted-foreground line-clamp-2">{r.snippet}</p>
              )}
              {r.link && (
                <a
                  href={r.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-xs text-primary hover:underline"
                >
                  Read full article <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </motion.div>
          ))}
        </div>
      )}

      {searched && !loading && results.length === 0 && (
        <div className="flex h-40 items-center justify-center rounded-xl border border-(--color-border) bg-card">
          <p className="text-sm text-muted-foreground">
            No results found for "{query}". Try different keywords or a broader query.
          </p>
        </div>
      )}

      {!searched && (
        <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-(--color-border) bg-card/50">
          <div className="text-center">
            <Search className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">Type a query and press Enter to search</p>
          </div>
        </div>
      )}
    </motion.div>
  )
}
