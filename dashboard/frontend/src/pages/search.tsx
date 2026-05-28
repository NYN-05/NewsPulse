import { useState, useRef, useEffect } from "react"
import { api } from "@/services/api"
import type { SearchResult } from "@/types"

export function SearchPage() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setHasSearched(true)
    try {
      const d = await api.search(query)
      setResults(d.results || [])
    } catch {
      setResults([])
    }
    setLoading(false)
  }

  return (
    <div className="animate-fadeIn">
      {/* Search section — centered */}
      <div className="flex flex-col items-center justify-center min-h-[50vh]">
        <div className="w-full max-w-xl">
          <div className="text-center mb-8">
            <h1 className="text-lg font-medium text-[var(--color-fg)]">Semantic Discovery</h1>
            <p className="text-xs text-[var(--color-fg-muted)] mt-1">
              Ask natural language questions about cross-domain intelligence
            </p>
          </div>

          {/* Input */}
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder='e.g. "links between AI policy and energy markets"'
              className="flex-1 bg-[var(--color-card)] border border-[var(--color-border)] rounded-lg px-4 py-3 text-sm text-[var(--color-fg)] placeholder-[var(--color-fg-muted)] outline-none focus:border-[var(--color-accent)] transition-colors"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="px-5 py-3 rounded-lg bg-[var(--color-accent)] text-white text-sm font-medium hover:bg-[var(--color-accent-hover)] disabled:opacity-30 transition-colors"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="inline-block w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" />
                  Searching
                </span>
              ) : (
                "Ask"
              )}
            </button>
          </div>

          <p className="mt-3 text-[10px] text-[var(--color-fg-muted)] font-mono text-center">
            Powered by semantic vector search · understands concepts, not just keywords
          </p>
        </div>
      </div>

      {/* Results */}
      {hasSearched && (
        <div className="mt-8 space-y-3">
          {loading ? (
            [1, 2, 3].map((i) => (
              <div key={i} className="rounded-lg border border-[var(--color-border)] p-4 animate-pulse">
                <div className="h-4 w-64 bg-[var(--color-border)] rounded mb-2" />
                <div className="h-3 w-48 bg-[var(--color-border)] rounded" />
              </div>
            ))
          ) : results.length > 0 ? (
            <>
              <p className="text-xs text-[var(--color-fg-muted)] font-mono">
                {results.length} result{results.length !== 1 ? "s" : ""} for "{query}"
              </p>
              {results.map((r, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] transition-colors p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-[var(--color-fg)]">{r.title}</p>
                      <p className="text-[10px] text-[var(--color-fg-muted)] font-mono mt-0.5">
                        {r.source}{r.category ? ` · ${r.category}` : ""}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <span className="font-mono text-xs text-[var(--color-accent)]">
                        {(r.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  {r.snippet && (
                    <p className="mt-2 text-xs text-[var(--color-fg-secondary)] leading-relaxed">{r.snippet}</p>
                  )}
                  {r.link && (
                    <a
                      href={r.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-block text-[10px] text-[var(--color-accent)] hover:underline font-mono"
                    >
                      Read →
                    </a>
                  )}
                </div>
              ))}
            </>
          ) : (
            <div className="flex h-32 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
              <p className="text-xs text-[var(--color-fg-muted)] font-mono">No results for "{query}". Try a different query.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
