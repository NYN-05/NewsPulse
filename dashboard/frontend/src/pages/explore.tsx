import { useEffect, useState } from "react"
import { api } from "@/services/api"
import type { CrossDomainLink } from "@/types"

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

export function ExplorePage() {
  const [links, setLinks] = useState<CrossDomainLink[]>([])
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState<CrossDomainLink | null>(null)
  const [loading, setLoading] = useState(true)
  const [sectorFilter, setSectorFilter] = useState("")

  useEffect(() => {
    api.crossDomain().then((d) => {
      setLinks((d.links || []).sort((a, b) => b.strength - a.strength))
      setLoading(false)
    })
  }, [])

  const sectors = [...new Set(links.flatMap((l) => [l.source_sector, l.target_sector]))].sort()

  const filtered = links.filter((l) => {
    if (search) {
      const q = search.toLowerCase()
      if (!l.source_entity.toLowerCase().includes(q) && !l.target_entity.toLowerCase().includes(q)) return false
    }
    if (sectorFilter && l.source_sector !== sectorFilter && l.target_sector !== sectorFilter) return false
    return true
  })

  if (loading) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-[var(--color-fg-muted)] font-mono">Loading relationships...</p>
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
            <div className="h-4 w-64 bg-[var(--color-border)] rounded mb-3" />
            <div className="h-3 w-full bg-[var(--color-border)] rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-[var(--color-border)] pb-4">
        <h1 className="text-lg font-medium text-[var(--color-fg)]">Relationship Explorer</h1>
        <p className="text-xs text-[var(--color-fg-muted)] mt-0.5">
          Cross-domain entity connections · {filtered.length} relationships
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter entities..."
          className="flex-1 min-w-[160px] max-w-xs bg-[var(--color-card)] border border-[var(--color-border)] rounded px-3 py-1.5 text-xs text-[var(--color-fg)] placeholder-[var(--color-fg-muted)] outline-none focus:border-[var(--color-accent)] transition-colors"
        />
        <select
          value={sectorFilter}
          onChange={(e) => setSectorFilter(e.target.value)}
          className="bg-[var(--color-card)] border border-[var(--color-border)] rounded px-2.5 py-1.5 text-xs text-[var(--color-fg)] outline-none"
        >
          <option value="">All sectors</option>
          {sectors.map((s) => (
            <option key={s} value={s}>{SECTOR_LABELS[s] || s}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-1.5">
        {filtered.slice(0, 100).map((link, i) => (
          <button
            key={`${link.source_entity}-${link.target_entity}-${i}`}
            onClick={() => setSelected(selected === link ? null : link)}
            className={`w-full text-left rounded-lg border transition-colors p-3 ${
              selected === link
                ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                : "border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)]"
            }`}
          >
            <div className="flex items-center gap-3 text-xs">
              <span className="font-mono text-[var(--color-fg)] min-w-0 truncate">{link.source_entity}</span>
              <span className="text-[var(--color-fg-muted)] shrink-0">→</span>
              <span className="font-mono text-[var(--color-fg)] min-w-0 truncate">{link.target_entity}</span>
              <span className="ml-auto shrink-0 flex items-center gap-2">
                <span className="text-[10px] text-[var(--color-fg-muted)] font-mono">
                  {SECTOR_LABELS[link.source_sector] || link.source_sector}
                </span>
                <span className="text-[10px] text-[var(--color-fg-muted)]">x</span>
                <span className="text-[10px] text-[var(--color-fg-muted)] font-mono">
                  {SECTOR_LABELS[link.target_sector] || link.target_sector}
                </span>
                <span className="text-xs font-mono text-[var(--color-accent)] w-8 text-right">
                  {link.strength.toFixed(1)}
                </span>
              </span>
            </div>
            {selected === link && (
              <div className="mt-2 pt-2 border-t border-[var(--color-border)] text-[10px] text-[var(--color-fg-secondary)] font-mono leading-relaxed space-y-0.5">
                <div>Co-occurrences: {link.cooccurrence_count}</div>
                <div>Source diversity: {link.source_diversity.toFixed(2)}</div>
                <div>Sentiment variance: {link.sentiment_variance.toFixed(2)}</div>
              </div>
            )}
          </button>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="flex h-40 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs text-[var(--color-fg-muted)] font-mono">No relationships match the current filters.</p>
        </div>
      )}
    </div>
  )
}
