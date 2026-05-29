import { useEffect, useState, useMemo } from "react"
import { api } from "@/services/api"
import type { CrossDomainLink } from "@/types"
import { FocusedGraph, IntelligencePanel, RelationshipSummary } from "@/components/charts/relationship-graph"

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

function DomainCount({ entitiesByDomain }: { entitiesByDomain: Map<string, { entity: string; totalStrength: number; count: number }[]> }) {
  return (
    <div className="flex flex-wrap gap-1">
      {Array.from(entitiesByDomain.entries()).map(([domain, entities]) => (
        <span
          key={domain}
          className="text-[9px] font-mono px-1.5 py-0.5 rounded border"
          style={{
            color: SECTOR_COLORS[domain] || "#4a7cf7",
            borderColor: SECTOR_COLORS[domain] || "#4a7cf7",
            background: `${SECTOR_COLORS[domain] || "#4a7cf7"}10`,
          }}
        >
          {SECTOR_LABELS[domain] || domain} {entities.length}
        </span>
      ))}
    </div>
  )
}

function EntityList({
  entitiesByDomain,
  selectedEntity,
  onSelect,
}: {
  entitiesByDomain: Map<string, { entity: string; totalStrength: number; count: number }[]>
  selectedEntity: string | null
  onSelect: (e: string) => void
}) {
  return (
    <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1 custom-scroll">
      {Array.from(entitiesByDomain.entries()).map(([domain, entities]) => (
        <div key={domain}>
          <div className="flex items-center gap-2 mb-1">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ background: SECTOR_COLORS[domain] || "#4a7cf7" }}
            />
            <span className="text-[9px] font-mono uppercase tracking-wider text-[var(--color-fg-muted)]">
              {SECTOR_LABELS[domain] || domain}
            </span>
            <span className="text-[8px] font-mono text-[var(--color-fg-muted)] opacity-50">{entities.length}</span>
          </div>
          {entities.map((e) => (
            <button
              key={e.entity}
              onClick={() => onSelect(e.entity)}
              className={`w-full text-left rounded px-2 py-1 transition-all text-[10px] font-mono flex items-center gap-2 ${
                selectedEntity === e.entity
                  ? "bg-[var(--color-accent-subtle)] border border-[var(--color-accent)]"
                  : "hover:bg-[var(--color-card-hover)] border border-transparent"
              }`}
            >
              <span className="text-[var(--color-fg)] truncate flex-1">{e.entity}</span>
              <span className="text-[var(--color-fg-muted)] shrink-0 text-[9px]">{e.count} links</span>
              <span
                className="text-[9px] font-mono shrink-0"
                style={{ color: SECTOR_COLORS[domain] || "#4a7cf7" }}
              >
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
      <div className="space-y-5">
        <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Loading relationship data...</p>
        <div className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
          <div className="h-[520px] bg-[var(--color-card)] rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5 animate-fadeIn">
      <div className="border-b border-[var(--color-border)] pb-4">
        <h1 className="text-xl font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Relationship Explorer</h1>
        <p className="text-[10px] font-mono text-[var(--color-fg-muted)] mt-1 tracking-wider uppercase">
          {filteredLinks.length} connections — {entityCount} entities — {allSectors.length} domains
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1 rounded-lg border border-[var(--color-border)] p-0.5">
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
          <button onClick={clearAll}
            className="text-[10px] font-mono text-[var(--color-accent)] hover:underline ml-auto"
          >
            Clear selection
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-5" style={{ gridTemplateColumns: "260px 1fr 340px" }}>
        <div className="space-y-3">
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-3 space-y-3">
            <div className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Entity Discovery</div>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search entities..."
              className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2.5 py-1.5 text-[10px] text-[var(--color-fg)] placeholder-[var(--color-fg-muted)] outline-none focus:border-[var(--color-accent)] transition-colors font-mono"
            />
            <div className="flex flex-wrap gap-1">
              {allSectors.map((s) => (
                <button
                  key={s}
                  onClick={() => toggleDomain(s)}
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
            <EntityList entitiesByDomain={entitiesByDomain} selectedEntity={selectedEntity} onSelect={handleEntitySelect} />
          </div>
        </div>

        <div className="space-y-4">
          <FocusedGraph
            selectEntity={setSelectedEntity}
            selectedEntity={selectedEntity}
            connectedLinks={connectedLinks}
            onNodeClick={handleEntitySelect}
            onEdgeClick={setSelectedLink}
          />
          <RelationshipSummary selectedEntity={selectedEntity} connectedLinks={connectedLinks} />
        </div>

        <div className="space-y-3">
          {selectedLink && (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-3">
              <div className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase mb-3">
                Intelligence Explanation
              </div>
              <IntelligencePanel link={selectedLink} totalLinks={filteredLinks.length} />
            </div>
          )}
          {!selectedLink && selectedEntity && connectedLinks.length > 0 && (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-3">
              <div className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase mb-2">
                Connections for {selectedEntity}
              </div>
              <div className="space-y-1">
                {connectedLinks.map((link, i) => {
                  const counterpart = link.source_entity === selectedEntity ? link.target_entity : link.source_entity
                  const sector = link.source_entity === selectedEntity ? link.target_sector : link.source_sector
                  return (
                    <button
                      key={i}
                      onClick={() => setSelectedLink(link)}
                      className="w-full text-left rounded border border-[var(--color-border)] px-2.5 py-1.5 bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] transition-all"
                    >
                      <div className="flex items-center gap-2 text-[10px] font-mono">
                        <span className="text-[var(--color-fg)] truncate flex-1">{counterpart}</span>
                        <span className="text-[var(--color-accent)]">{link.strength.toFixed(1)}</span>
                      </div>
                      <div className="text-[8px] font-mono text-[var(--color-fg-muted)]">{SECTOR_LABELS[sector] || sector}</div>
                    </button>
                  )
                })}
              </div>
            </div>
          )}
          {!selectedEntity && (
            <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-[var(--color-border)]">
              <div className="text-center p-4">
                <p className="text-[10px] font-mono text-[var(--color-fg-muted)]">Select an entity</p>
                <p className="text-[8px] font-mono text-[var(--color-fg-muted)] mt-1 opacity-60">to view intelligence</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {filteredLinks.length === 0 && (
        <div className="flex h-32 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">No relationships match the current filters.</p>
        </div>
      )}
    </div>
  )
}
