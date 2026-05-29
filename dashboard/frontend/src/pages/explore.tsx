import { useEffect, useState, useMemo } from "react"
import { api } from "@/services/api"
import type { CrossDomainLink } from "@/types"
import { FocusedGraph, IntelligencePanel, RelationshipSummary, EmptyGraphOverlay } from "@/components/charts/relationship-graph"

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

const SECTOR_COLORS: Record<string, string> = {
  politics: "#4a7cf7", finance: "#4fcf8d", technology: "#5bc0eb",
  energy: "#d4a757", military: "#e06c7a", startups: "#8b7cf7",
  social: "#f0a5d4", global_events: "#45c4b0",
}

const INTELLIGENCE_MODES = [
  { id: "relationship", label: "Relationship" },
  { id: "dependency", label: "Dependency" },
  { id: "influence", label: "Influence" },
  { id: "narrative", label: "Narrative" },
] as const

function EntityList({
  entitiesByDomain,
  selectedEntity,
  onSelect,
  search,
  onSearchChange,
  allSectors,
  activeDomains,
  onToggleDomain,
}: {
  entitiesByDomain: Map<string, { entity: string; totalStrength: number; count: number }[]>
  selectedEntity: string | null
  onSelect: (e: string) => void
  search: string
  onSearchChange: (s: string) => void
  allSectors: string[]
  activeDomains: Set<string>
  onToggleDomain: (s: string) => void
}) {
  return (
    <div className="flex flex-col h-full">
      <div className="space-y-2 shrink-0">
        <p className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Entity Discovery</p>
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search entities..."
          className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-[10px] text-[var(--color-fg)] placeholder-[var(--color-fg-muted)] outline-none focus:border-[var(--color-accent)] transition-colors font-mono"
        />
        <div className="flex flex-wrap gap-1">
          {allSectors.map((s) => (
            <button
              key={s}
              onClick={() => onToggleDomain(s)}
              className={`text-[9px] font-mono px-1.5 py-0.5 rounded border transition-all ${
                activeDomains.has(s)
                  ? "border-[var(--color-accent)] text-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                  : "border-[var(--color-border)] text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
              }`}
            >
              {SECTOR_LABELS[s] || s}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto mt-2 space-y-2 custom-scroll" style={{ minHeight: 0 }}>
        {Array.from(entitiesByDomain.entries()).map(([domain, entities]) => (
          <div key={domain}>
            <div className="flex items-center gap-1.5 mb-1">
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: SECTOR_COLORS[domain] || "#4a7cf7" }} />
              <span className="text-[8px] font-mono uppercase tracking-wider text-[var(--color-fg-muted)]">
                {SECTOR_LABELS[domain] || domain}
              </span>
              <span className="text-[8px] font-mono text-[var(--color-fg-muted)] opacity-50">{entities.length}</span>
            </div>
            {entities.map((e) => (
              <button
                key={e.entity}
                onClick={() => onSelect(e.entity)}
                className={`w-full text-left rounded px-1.5 py-1 transition-all text-[10px] font-mono flex items-center gap-2 ${
                  selectedEntity === e.entity
                    ? "bg-[var(--color-accent-subtle)] border border-[var(--color-accent)]"
                    : "hover:bg-[var(--color-card-hover)] border border-transparent"
                }`}
              >
                <span className="text-[var(--color-fg)] truncate flex-1">{e.entity}</span>
                <span className="text-[var(--color-fg-muted)] shrink-0 text-[8px]">{e.count}</span>
                <span className="text-[8px] font-mono shrink-0" style={{ color: SECTOR_COLORS[domain] || "#4a7cf7" }}>
                  {e.totalStrength.toFixed(0)}
                </span>
              </button>
            ))}
          </div>
        ))}
        {entitiesByDomain.size === 0 && (
          <p className="text-[10px] font-mono text-[var(--color-fg-muted)]">No entities match the current filter.</p>
        )}
      </div>
    </div>
  )
}

function SampleIntelligence({
  links,
  stats,
}: {
  links: CrossDomainLink[]
  stats: { entityCount: number; sectorCount: number; topSectors: [string, number][] }
}) {
  const top5 = useMemo(() => [...links].sort((a, b) => b.strength - a.strength).slice(0, 5), [links])
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)] animate-pulseGlow" />
        <span className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Featured Intelligence</span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
        <div className="border border-[var(--color-border)] rounded p-2">
          <p className="text-[var(--color-fg-muted)] text-[9px]">Connections</p>
          <p className="text-[var(--color-accent)] text-sm mt-0.5">{links.length}</p>
        </div>
        <div className="border border-[var(--color-border)] rounded p-2">
          <p className="text-[var(--color-fg-muted)] text-[9px]">Entities</p>
          <p className="text-[var(--color-fg)] text-sm mt-0.5">{stats.entityCount}</p>
        </div>
        <div className="border border-[var(--color-border)] rounded p-2">
          <p className="text-[var(--color-fg-muted)] text-[9px]">Domains</p>
          <p className="text-[var(--color-fg)] text-sm mt-0.5">{stats.sectorCount}</p>
        </div>
      </div>
      <div className="space-y-1">
        <p className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider">Top Relationships</p>
        {top5.map((l, i) => (
          <div key={i} className="flex items-center gap-2 text-[10px] font-mono border border-[var(--color-border)] rounded px-2 py-1">
            <span className="text-[var(--color-fg-muted)] w-3">{i + 1}.</span>
            <span className="text-[var(--color-fg)] truncate flex-1">{l.source_entity}</span>
            <span className="text-[var(--color-accent)] text-[9px]">&harr;</span>
            <span className="text-[var(--color-fg)] truncate flex-1">{l.target_entity}</span>
            <span className="text-[var(--color-fg-muted)] text-[8px]">{l.strength.toFixed(1)}</span>
          </div>
        ))}
      </div>
      {stats.topSectors.length > 0 && (
        <div>
          <p className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider mb-1">Active Sectors</p>
          <div className="flex flex-wrap gap-1">
            {stats.topSectors.map(([s, c]) => (
              <span key={s} className="text-[9px] font-mono px-1.5 py-0.5 rounded border"
                style={{ color: SECTOR_COLORS[s] || "#4a7cf7", borderColor: SECTOR_COLORS[s] || "#4a7cf7", background: `${SECTOR_COLORS[s] || "#4a7cf7"}10` }}>
                {SECTOR_LABELS[s] || s} {c}
              </span>
            ))}
          </div>
        </div>
      )}
      <div className="border-t border-[var(--color-border)] pt-2 mt-2">
        <p className="text-[8px] font-mono text-[var(--color-fg-muted)]">Select an entity from the left panel to explore its cross-domain relationships on the graph canvas.</p>
      </div>
    </div>
  )
}

export function ExplorePage() {
  const [links, setLinks] = useState<CrossDomainLink[]>([])
  const [search, setSearch] = useState("")
  const [activeDomains, setActiveDomains] = useState<Set<string>>(new Set())
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null)
  const [selectedLink, setSelectedLink] = useState<CrossDomainLink | null>(null)
  const [intelMode, setIntelMode] = useState<string>("relationship")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.crossDomain().then((d) => {
      const sorted = (d.links || []).sort((a: CrossDomainLink, b: CrossDomainLink) => b.strength - a.strength)
      setLinks(sorted)
      setLoading(false)
    })
  }, [])

  const allSectors = useMemo(
    () => [...new Set(links.flatMap((l) => [l.source_sector, l.target_sector]))].sort(),
    [links],
  )

  const filteredLinks = useMemo(() => {
    return links.filter((l) => {
      if (search) {
        const q = search.toLowerCase()
        if (!l.source_entity.toLowerCase().includes(q) && !l.target_entity.toLowerCase().includes(q)) return false
      }
      if (activeDomains.size > 0) {
        if (!activeDomains.has(l.source_sector) && !activeDomains.has(l.target_sector)) return false
      }
      return true
    })
  }, [links, search, activeDomains])

  const entitiesByDomain = useMemo(() => {
    const map = new Map<string, Map<string, { totalStrength: number; count: number }>>()
    for (const l of filteredLinks) {
      for (const e of [{ entity: l.source_entity, sector: l.source_sector }, { entity: l.target_entity, sector: l.target_sector }]) {
        if (!map.has(e.sector)) map.set(e.sector, new Map())
        const inner = map.get(e.sector)!
        const existing = inner.get(e.entity) || { totalStrength: 0, count: 0 }
        existing.totalStrength += l.strength
        existing.count += 1
        inner.set(e.entity, existing)
      }
    }
    const result = new Map<string, { entity: string; totalStrength: number; count: number }[]>()
    for (const [sector, entities] of map) {
      result.set(sector, Array.from(entities.entries())
        .map(([entity, data]) => ({ entity, ...data }))
        .sort((a, b) => b.totalStrength - a.totalStrength))
    }
    return result
  }, [filteredLinks])

  const connectedLinks = useMemo(() => {
    if (!selectedEntity) return []
    return filteredLinks.filter((l) => l.source_entity === selectedEntity || l.target_entity === selectedEntity)
  }, [filteredLinks, selectedEntity])

  const stats = useMemo(() => {
    const entities = new Set(links.flatMap((l) => [l.source_entity, l.target_entity]))
    const sectors = new Set(links.flatMap((l) => [l.source_sector, l.target_sector]))
    const sectorCounts = new Map<string, number>()
    for (const l of links) {
      sectorCounts.set(l.source_sector, (sectorCounts.get(l.source_sector) || 0) + 1)
      sectorCounts.set(l.target_sector, (sectorCounts.get(l.target_sector) || 0) + 1)
    }
    return {
      entityCount: entities.size,
      sectorCount: sectors.size,
      topSectors: [...sectorCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4),
    }
  }, [links])

  const toggleDomain = (s: string) => {
    setActiveDomains((prev) => {
      const next = new Set(prev)
      if (next.has(s)) next.delete(s); else next.add(s)
      return next
    })
  }

  const handleEntitySelect = (entity: string) => {
    setSelectedEntity(entity === selectedEntity ? null : entity)
    setSelectedLink(null)
  }

  const clearAll = () => {
    setSelectedEntity(null); setSelectedLink(null)
  }

  const entityCount = useMemo(() => {
    const s = new Set(filteredLinks.flatMap((l) => [l.source_entity, l.target_entity]))
    return s.size
  }, [filteredLinks])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--color-bg)]">
        <div className="text-center">
          <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Loading relationship data...</p>
          <div className="mt-4 mx-auto w-4 h-4 border border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen animate-fadeIn">
      {/* Header strip */}
      <div className="flex items-center justify-between shrink-0 border-b border-[var(--color-border)] px-6 h-12">
        <div className="flex items-center gap-4">
          <h1 className="text-base font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Relationship Explorer</h1>
          <p className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">
            {filteredLinks.length} connections &middot; {entityCount} entities &middot; {allSectors.length} domains
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-0.5 rounded-lg border border-[var(--color-border)] p-0.5">
            {INTELLIGENCE_MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setIntelMode(m.id)}
                className={`text-[9px] font-mono px-2 py-1 rounded transition-all ${
                  intelMode === m.id
                    ? "text-[var(--color-accent)] bg-[var(--color-accent-subtle)] border border-[var(--color-accent)]"
                    : "text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] border border-transparent"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
          {selectedEntity && (
            <button onClick={clearAll} className="text-[9px] font-mono text-[var(--color-accent)] hover:underline">
              Clear selection
            </button>
          )}
        </div>
      </div>

      {/* Three-column workspace — fills remaining viewport */}
      <div className="flex-1 flex gap-0 overflow-hidden" style={{ minHeight: 0 }}>
        {/* Left: Entity Discovery ~15% */}
        <div className="w-[200px] xl:w-[220px] 2xl:w-[260px] shrink-0 border-r border-[var(--color-border)] flex flex-col" style={{ minHeight: 0 }}>
          <div className="flex-1 flex flex-col p-3 overflow-hidden" style={{ minHeight: 0 }}>
            <EntityList
              entitiesByDomain={entitiesByDomain}
              selectedEntity={selectedEntity}
              onSelect={handleEntitySelect}
              search={search}
              onSearchChange={setSearch}
              allSectors={allSectors}
              activeDomains={activeDomains}
              onToggleDomain={toggleDomain}
            />
          </div>
        </div>

        {/* Center: Graph canvas ~55-60% */}
        <div className="flex-1 flex flex-col" style={{ minHeight: 0, minWidth: 0 }}>
          <div className="flex-1 flex flex-col" style={{ minHeight: 0 }}>
            <FocusedGraph
              selectEntity={setSelectedEntity}
              selectedEntity={selectedEntity}
              connectedLinks={connectedLinks}
              onNodeClick={handleEntitySelect}
              onEdgeClick={setSelectedLink}
              allLinks={links}
              stats={stats}
            />
          </div>
        </div>

        {/* Right: Intelligence Analysis Panel ~25-30% */}
        <div className="w-[320px] xl:w-[360px] 2xl:w-[420px] shrink-0 border-l border-[var(--color-border)] flex flex-col" style={{ minHeight: 0 }}>
          <div className="flex-1 overflow-y-auto custom-scroll p-4" style={{ minHeight: 0 }}>
            {selectedLink ? (
              <div className="space-y-4 animate-slideUp">
                <p className="text-[9px] font-mono text-[var(--color-accent)] tracking-wider uppercase flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)]" />
                  Intelligence Explanation
                </p>
                <IntelligencePanel link={selectedLink} totalLinks={filteredLinks.length} />
              </div>
            ) : selectedEntity && connectedLinks.length > 0 ? (
              <div className="space-y-3">
                <p className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">
                  Connections for {selectedEntity}
                </p>
                <div className="space-y-1">
                  {connectedLinks.map((link, i) => {
                    const counterpart = link.source_entity === selectedEntity ? link.target_entity : link.source_entity
                    const sector = link.source_entity === selectedEntity ? link.target_sector : link.source_sector
                    return (
                      <button
                        key={i}
                        onClick={() => setSelectedLink(link)}
                        className="w-full text-left rounded border border-[var(--color-border)] px-2.5 py-2 bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] transition-all"
                      >
                        <div className="flex items-center gap-2 text-[10px] font-mono">
                          <span className="text-[var(--color-fg)] truncate flex-1">{counterpart}</span>
                          <span className="text-[var(--color-accent)]">{link.strength.toFixed(1)}</span>
                        </div>
                        <div className="text-[8px] font-mono text-[var(--color-fg-muted)] mt-0.5">{SECTOR_LABELS[sector] || sector}</div>
                      </button>
                    )
                  })}
                </div>
              </div>
            ) : (
              <SampleIntelligence links={filteredLinks} stats={stats} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
