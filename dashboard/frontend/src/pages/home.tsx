import { useEffect, useState, useRef } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { api } from "@/services/api"
import type { CrossDomainLink, BreakingEvent } from "@/types"

interface Discovery {
  id: string
  type: "cross_domain" | "narrative" | "influence" | "signal" | "chain"
  title: string
  body: string
  explanation: string
  entities: string[]
  sectors: string[]
  confidence: number
  meta: string
}

interface ImpactChain {
  chain: string[]
  sectors: string[]
  chain_key: string
  length: number
  cross_domain_hops: number
  total_weight: number
}

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

const SECTOR_EXPLANATIONS: Record<string, string> = {
  politics: "political dynamics", finance: "financial markets", technology: "tech sector",
  energy: "energy markets", military: "military affairs", startups: "startup ecosystem",
  social: "social trends", global_events: "global events",
}

const TYPE_META: Record<string, { label: string; dot: string }> = {
  cross_domain: { label: "Cross-Domain Link", dot: "#4a7cf7" },
  narrative: { label: "Narrative Shift", dot: "#4fcf8d" },
  influence: { label: "Influence Update", dot: "#d4a757" },
  signal: { label: "Signal Spike", dot: "#e06c7a" },
  chain: { label: "Impact Chain", dot: "#5bc0eb" },
}

const COUNTRY_COORDS: Record<string, [number, number]> = {
  us: [37.09, -95.71], "u. s.": [37.09, -95.71], india: [20.59, 78.96],
  iran: [32.42, 53.68], israel: [31.04, 34.85], china: [35.86, 104.19],
  russia: [61.52, 105.31], uk: [55.37, -3.43], germany: [51.16, 10.45],
  france: [46.60, 1.88], japan: [36.20, 138.25], australia: [-25.27, 133.77],
  canada: [56.13, -106.34], brazil: [-14.23, -51.92], "saudi arabia": [23.88, 45.07],
  turkey: [38.96, 35.24], pakistan: [30.37, 69.34], ukraine: [48.37, 31.16],
  iraq: [33.22, 43.67], afghanistan: [33.93, 67.71], syria: [34.80, 38.99],
  egypt: [26.82, 30.80], nigeria: [9.08, 8.67], "south korea": [35.90, 127.76],
  "north korea": [40.33, 127.51], indonesia: [-0.78, 113.92], kuwait: [29.31, 47.48],
  qatar: [25.35, 51.18], oman: [21.47, 55.97], lebanon: [33.85, 35.86],
  "strait of hormuz": [26.50, 56.00],
}

function getCountryCoords(name: string): [number, number] | null {
  const key = name.toLowerCase().trim()
  for (const [n, coords] of Object.entries(COUNTRY_COORDS)) {
    if (key === n || key.includes(n)) return coords
  }
  return null
}

function explainRelationship(src: string, tgt: string, srcSec: string, tgtSec: string): string {
  const sl = SECTOR_EXPLANATIONS[srcSec] || srcSec
  const tl = SECTOR_EXPLANATIONS[tgtSec] || tgtSec
  return `Relationship between ${src} (${sl}) and ${tgt} (${tl}) - changes in one directly affect the other through cross-domain dependencies.`
}

function buildFeed(links: CrossDomainLink[], breaking: BreakingEvent[], narratives: any, influence: any): Discovery[] {
  const items: Discovery[] = []

  for (const link of (links || []).slice(0, 20)) {
    if (link.strength < 3) continue
    const sl = SECTOR_LABELS[link.source_sector] || link.source_sector
    const tl = SECTOR_LABELS[link.target_sector] || link.target_sector
    items.push({
      id: `cd-${link.source_entity}-${link.target_entity}`,
      type: "cross_domain",
      title: `${link.source_entity} <-> ${link.target_entity}`,
      body: `Connection bridging ${sl} and ${tl}. Co-occurring in ${link.cooccurrence_count} articles across ${Math.round(link.source_diversity)} sources.`,
      explanation: explainRelationship(link.source_entity, link.target_entity, link.source_sector, link.target_sector),
      entities: [link.source_entity, link.target_entity],
      sectors: [link.source_sector, link.target_sector],
      confidence: Math.min(link.strength / 30, 0.99),
      meta: `${link.cooccurrence_count} co-occurrences - diversity ${link.source_diversity.toFixed(2)}`,
    })
  }

  for (const sig of (breaking || []).slice(0, 8)) {
    items.push({
      id: `sig-${sig.keyword || sig.entity || Math.random()}`,
      type: "signal",
      title: sig.keyword || sig.entity || "Unknown",
      body: `${(sig.signal || "").replace("_", " ")} - burst factor ${(sig.burst_factor || 1).toFixed(1)}x above normal.`,
      explanation: `Unusual activity detected: "${sig.keyword || sig.entity}" at ${(sig.burst_factor || 1).toFixed(1)}x expected rate. May indicate an emerging event.`,
      entities: sig.entity ? [sig.entity] : [],
      sectors: [],
      confidence: Math.min(sig.score / 100, 0.99),
      meta: `score ${sig.score.toFixed(1)} - ${sig.recent_count || 0} articles`,
    })
  }

  if (narratives) {
    for (const t of (narratives.emerging_topics || []).slice(0, 6)) {
      items.push({
        id: `narr-${t.cluster || Math.random()}`,
        type: "narrative",
        title: t.topic || "Emerging trend",
        body: `Entering ${t.phase || "emerging"} phase with acceleration ${(t.acceleration || 0).toFixed(1)}.`,
        explanation: `Gaining momentum (acceleration: ${(t.acceleration || 0).toFixed(2)}). If sustained, signals a major narrative shift.`,
        entities: (t.keywords || []).slice(0, 5),
        sectors: t.sectors || [],
        confidence: Math.min(Math.abs(t.acceleration || 0) / 10, 0.99) || 0.5,
        meta: `${t.count || 0} articles - momentum ${(t.momentum || 0).toFixed(1)}`,
      })
    }
  }

  if (influence) {
    for (const e of (influence.entity_influence || []).slice(0, 6)) {
      const reach = e.cross_domain_reach || e.cross_domain_links || 0
      items.push({
        id: `inf-${e.entity || Math.random()}`,
        type: "influence",
        title: e.entity || "Unknown",
        body: `Influence score ${(e.influence_score || 0).toFixed(2)} - cross-domain reach across ${reach} sectors.`,
        explanation: `"${e.entity}" is increasingly central. Score ${(e.influence_score || 0).toFixed(2)} suggests growing cross-domain significance.`,
        entities: [e.entity].filter(Boolean),
        sectors: [],
        confidence: Math.min((e.influence_score || 0) / 6, 0.99),
        meta: `score ${(e.influence_score || 0).toFixed(2)} - ${e.source_diversity || 0} sources`,
      })
    }
  }

  items.sort((a, b) => b.confidence - a.confidence)
  return items.slice(0, 30)
}

function DiscoveriesList({ discoveries, expanded, setExpanded }: {
  discoveries: Discovery[]
  expanded: string | null
  setExpanded: (id: string | null) => void
}) {
  return (
    <div className="space-y-2">
      {discoveries.map((d, i) => {
        const meta = TYPE_META[d.type]
        return (
          <div
            key={d.id}
            className="animate-slideUp rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] hover:border-[var(--color-border-hover)] transition-all"
            style={{ animationDelay: `${i * 30}ms` }}
          >
            <button onClick={() => setExpanded(expanded === d.id ? null : d.id)} className="w-full text-left p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: meta.dot }} />
                <span className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-widest uppercase">{meta.label}</span>
                <span className="text-[10px] font-mono text-[var(--color-fg-muted)] ml-auto">{(d.confidence * 100).toFixed(0)}% confidence</span>
              </div>
              <h2 className="text-base font-serif text-[var(--color-fg)] leading-snug">{d.title}</h2>
              <p className="text-xs text-[var(--color-fg-secondary)] mt-1.5 leading-relaxed">{d.body}</p>
              {!expanded && d.explanation && (
                <p className="text-[11px] text-[var(--color-accent)] mt-2 font-mono italic opacity-80">// {d.explanation}</p>
              )}
              <div className="flex flex-wrap gap-1.5 mt-3">
                {d.entities.slice(0, 4).map((e) => (
                  <span key={e} className="text-[9px] font-mono text-[var(--color-accent)] bg-[var(--color-accent-subtle)] rounded px-1.5 py-0.5">{e}</span>
                ))}
              </div>
              <div className="mt-2 text-[10px] font-mono text-[var(--color-fg-muted)]">{d.meta}</div>
              {expanded === d.id && d.explanation && (
                <div className="mt-3 pt-3 border-t border-[var(--color-border)]">
                  <p className="text-xs text-[var(--color-fg-secondary)] leading-relaxed">{d.explanation}</p>
                  {d.sectors.length > 0 && (
                    <div className="mt-2 text-[10px] font-mono text-[var(--color-fg-muted)]">
                      Sectors: {d.sectors.map((s) => SECTOR_LABELS[s] || s).join(", ")}
                    </div>
                  )}
                </div>
              )}
            </button>
          </div>
        )
      })}
    </div>
  )
}

function IntelligenceMap({ links, breaking }: { links: CrossDomainLink[]; breaking: BreakingEvent[] }) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstance = useRef<L.Map | null>(null)

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return
    const map = L.map(mapRef.current, { center: [20, 30], zoom: 2, zoomControl: false, attributionControl: false })
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 18 }).addTo(map)
    L.control.zoom({ position: "bottomright" }).addTo(map)
    mapInstance.current = map
    return () => { map.remove(); mapInstance.current = null }
  }, [])

  useEffect(() => {
    const map = mapInstance.current
    if (!map) return
    map.eachLayer((l) => { if ((l as any)._isNewsLayer) map.removeLayer(l) })

    const seen = new Set<string>()
    for (const link of links) {
      const from = getCountryCoords(link.source_entity)
      const to = getCountryCoords(link.target_entity)
      if (!from || !to) continue
      for (const [coords, name] of [[from, link.source_entity], [to, link.target_entity]] as const) {
        const key = name.toLowerCase()
        if (!seen.has(key)) {
          seen.add(key)
          const intensity = Math.min(link.strength / 40, 1)
          const radius = 4 + intensity * 6
          const marker = L.circleMarker(coords, {
            radius, weight: 1,
            color: "#4a7cf7", fillColor: "#4a7cf7", fillOpacity: 0.3 + intensity * 0.4,
            interactive: true,
          } as any)
          marker.addTo(map)
          marker.bindTooltip(`<div style="font-family:monospace;font-size:10px;padding:4px 8px"><strong>${name}</strong></div>`)
          ;(marker as any)._isNewsLayer = true
        }
      }

      const pts: [number, number][] = []
      const segments = 30
      for (let i = 0; i <= segments; i++) {
        const f = i / segments
        pts.push([from[0] + (to[0] - from[0]) * f, from[1] + (to[1] - from[1]) * f])
      }
      const opacity = Math.max(0.15, link.strength / 50)
      const line = L.polyline(pts, { weight: 1, color: "#4a7cf7", opacity, interactive: false } as any)
      line.addTo(map)
      ;(line as any)._isNewsLayer = true
    }

    for (const sig of (breaking || []).slice(0, 5)) {
      const ents = sig.entity ? [sig.entity] : (sig.keyword ? [sig.keyword] : [])
      for (const ent of ents) {
        const coords = getCountryCoords(ent)
        if (!coords) continue
        const burst = Math.min((sig.burst_factor || 1) / 100, 1)
        const sigMarker = L.circleMarker(coords, {
          radius: 6 + burst * 10, weight: 2,
          color: "#e06c7a", fillColor: "#e06c7a", fillOpacity: 0.2 + burst * 0.3,
          interactive: true,
        } as any)
        sigMarker.addTo(map)
        sigMarker.bindTooltip(`<div style="font-family:monospace;font-size:10px;padding:4px 8px"><strong style="color:#e06c7a">${ent}</strong><br/>Burst: ${(sig.burst_factor || 1).toFixed(1)}x</div>`)
        ;(sigMarker as any)._isNewsLayer = true
      }
    }
  }, [links, breaking])

  return (
    <div className="rounded-lg border border-[var(--color-border)] overflow-hidden" style={{ height: 320 }}>
      <div ref={mapRef} className="w-full h-full" />
    </div>
  )
}

export function HomePage() {
  const [discoveries, setDiscoveries] = useState<Discovery[]>([])
  const [links, setLinks] = useState<CrossDomainLink[]>([])
  const [breaking, setBreaking] = useState<BreakingEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.crossDomain().catch(() => ({ links: [], chains: [], sector_map: {} })),
      api.breaking().catch(() => []),
      api.narratives().catch(() => ({})),
      api.influence().catch(() => ({})),
    ]).then(([cd, breakingData, narratives, influence]) => {
      const rawLinks = (cd as any).links || []
      setLinks(rawLinks)
      setBreaking(breakingData)
      const feed = buildFeed(rawLinks, breakingData, narratives, influence)
      const chains = ((cd as any).chains || []) as ImpactChain[]
      for (const c of chains.slice(0, 4)) {
        if (c.chain && c.chain.length >= 2) {
          feed.push({
            id: `chain-${c.chain_key || Math.random()}`,
            type: "chain",
            title: c.chain.join(" -> "),
            body: `Impact chain spanning ${c.length} steps across ${c.cross_domain_hops} domains.`,
            explanation: `Narrative propagation: ${c.chain.join(" => ")}. Crosses ${c.sectors.length} domains.`,
            entities: c.chain,
            sectors: c.sectors,
            confidence: Math.min(c.total_weight / 50, 0.99),
            meta: `${c.length} hops - ${c.cross_domain_hops} domains crossed`,
          })
        }
      }
      feed.sort((a, b) => b.confidence - a.confidence)
      setDiscoveries(feed.slice(0, 25))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Loading intelligence feed...</p>
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-cyan)] animate-pulseGlow" />
        </div>
        <div className="rounded-lg border border-[var(--color-border)] p-6 animate-pulse"><div className="h-[320px] bg-[var(--color-card)] rounded" /></div>
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
            <div className="h-4 w-48 bg-[var(--color-border)] rounded mb-4" />
            <div className="h-3 w-full bg-[var(--color-border)] rounded mb-2" />
            <div className="h-3 w-3/4 bg-[var(--color-border)] rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-5">
        <div>
          <h1 className="text-xl font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Intelligence Briefing</h1>
          <p className="text-[10px] font-mono text-[var(--color-fg-muted)] mt-1 tracking-wider uppercase">
            {discoveries.length} cross-domain discoveries identified
          </p>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono text-[var(--color-fg-muted)]">
          <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)]" />Relationships</span>
          <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-[var(--color-red)]" />Signals</span>
          <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-[var(--color-green)]" />Narratives</span>
        </div>
      </div>

      <IntelligenceMap links={links} breaking={breaking} />

      <div className="flex items-center gap-2 text-[10px] font-mono text-[var(--color-fg-muted)]">
        <span className="text-[var(--color-fg)]">Top Discoveries</span>
        <span className="text-[var(--color-border)]">/</span>
        <span>Sorted by confidence</span>
      </div>

      <DiscoveriesList discoveries={discoveries} expanded={expanded} setExpanded={setExpanded} />

      {discoveries.length === 0 && (
        <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">No discoveries yet. Run the pipeline to surface cross-domain intelligence.</p>
        </div>
      )}
    </div>
  )
}
