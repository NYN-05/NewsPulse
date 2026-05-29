import { useEffect, useState } from "react"
import { api } from "@/services/api"
import type { CrossDomainLink } from "@/types"
import { RelationshipGraph, RelationshipExplanation } from "@/components/charts/relationship-graph"

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

export function ExplorePage() {
  const [links, setLinks] = useState<CrossDomainLink[]>([])
  const [search, setSearch] = useState("")
  const [sectorFilter, setSectorFilter] = useState("")
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null)
  const [selectedLink, setSelectedLink] = useState<CrossDomainLink | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.crossDomain().then((d) => {
      setLinks((d.links || []).sort((a: CrossDomainLink, b: CrossDomainLink) => b.strength - a.strength))
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

  const entityLinks = selectedEntity
    ? filtered.filter((l) => l.source_entity === selectedEntity || l.target_entity === selectedEntity)
    : []

  const handleNodeClick = (entity: string) => {
    setSelectedEntity(entity === selectedEntity ? null : entity)
    setSelectedLink(null)
  }

  const handleLinkSelect = (link: CrossDomainLink) => {
    setSelectedLink(link === selectedLink ? null : link)
  }

  if (loading) {
    return (
      <div className="space-y-5">
        <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Loading relationship graph...</p>
        <div className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
          <div className="h-[520px] bg-[var(--color-card)] rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-[var(--color-border)] pb-5">
        <h1 className="text-xl font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Relationship Explorer</h1>
        <p className="text-[10px] font-mono text-[var(--color-fg-muted)] mt-1 tracking-wider uppercase">
          {filtered.length} cross-domain connections — {new Set(filtered.flatMap((l) => [l.source_entity, l.target_entity])).size} entities
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter entities..."
          className="flex-1 min-w-[160px] max-w-xs bg-[var(--color-card)] border border-[var(--color-border)] rounded px-3 py-1.5 text-xs text-[var(--color-fg)] placeholder-[var(--color-fg-muted)] outline-none focus:border-[var(--color-accent)] transition-colors font-mono"
        />
        <select
          value={sectorFilter}
          onChange={(e) => setSectorFilter(e.target.value)}
          className="bg-[var(--color-card)] border border-[var(--color-border)] rounded px-2.5 py-1.5 text-xs text-[var(--color-fg)] outline-none font-mono"
        >
          <option value="">All sectors</option>
          {sectors.map((s) => (
            <option key={s} value={s}>{SECTOR_LABELS[s] || s}</option>
          ))}
        </select>
        {selectedEntity && (
          <button onClick={() => { setSelectedEntity(null); setSelectedLink(null) }}
            className="text-[10px] font-mono text-[var(--color-accent)] hover:underline ml-auto"
          >
            Clear selection
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6" style={{ gridTemplateColumns: selectedLink ? "1fr 380px" : "1fr" }}>
        <div className="space-y-4">
          <RelationshipGraph links={filtered} onNodeClick={handleNodeClick} selectedEntity={selectedEntity} />

          {selectedEntity && entityLinks.length > 0 && (
            <div className="space-y-1.5 animate-slideUp">
              <p className="text-[10px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">
                Connections for <span className="text-[var(--color-accent)]">{selectedEntity}</span>
              </p>
              {entityLinks.map((link, i) => {
                const isSelected = selectedLink === link
                const connected = link.source_entity === selectedEntity ? link.target_entity : link.source_entity
                return (
                  <button
                    key={i}
                    onClick={() => handleLinkSelect(link)}
                    className={`w-full text-left rounded-lg border transition-all p-3 ${
                      isSelected
                        ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                        : "border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)]"
                    }`}
                  >
                    <div className="flex items-center gap-3 text-xs font-mono">
                      <span className="text-[var(--color-fg)] truncate">{connected}</span>
                      <span className="text-[var(--color-fg-muted)] shrink-0">→</span>
                      <span className="text-[var(--color-fg-muted)] text-[10px]">
                        {SECTOR_LABELS[link.source_sector]}/{SECTOR_LABELS[link.target_sector]}
                      </span>
                      <span className="ml-auto text-[var(--color-accent)]">{link.strength.toFixed(1)}</span>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {selectedLink && (
          <div className="animate-slideUp">
            <RelationshipExplanation link={selectedLink} />
          </div>
        )}
      </div>

      {filtered.length === 0 && (
        <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">No relationships match the current filters.</p>
        </div>
      )}
    </div>
  )
}
