import { useEffect, useState } from "react"
import { api } from "@/services/api"
import type { CrossDomainLink, BreakingEvent } from "@/types"

interface Discovery {
  id: string
  type: "cross_domain" | "narrative" | "influence" | "signal"
  title: string
  body: string
  entities: string[]
  sectors: string[]
  confidence: number
  meta: string
}

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

const TYPE_META: Record<string, { label: string; dot: string }> = {
  cross_domain: { label: "Cross-Domain Link", dot: "#8b7cf7" },
  narrative: { label: "Narrative Shift", dot: "#6fcf8d" },
  influence: { label: "Influence Update", dot: "#d4a757" },
  signal: { label: "Signal Spike", dot: "#e06c7a" },
}

function buildFeed(links: CrossDomainLink[], breaking: BreakingEvent[], narratives: any, influence: any): Discovery[] {
  const items: Discovery[] = []

  for (const link of (links || []).slice(0, 25)) {
    if (link.strength < 3) continue
    items.push({
      id: `cd-${link.source_entity}-${link.target_entity}`,
      type: "cross_domain",
      title: `${link.source_entity} ↔ ${link.target_entity}`,
      body: `Connection bridging ${SECTOR_LABELS[link.source_sector] || link.source_sector} and ${SECTOR_LABELS[link.target_sector] || link.target_sector}. Both entities appear together in ${link.cooccurrence_count} articles across ${Math.round(link.source_diversity)} sources.`,
      entities: [link.source_entity, link.target_entity],
      sectors: [link.source_sector, link.target_sector],
      confidence: Math.min(link.strength / 30, 0.99),
      meta: `${link.cooccurrence_count} co-occurrences · diversity ${link.source_diversity.toFixed(2)}`,
    })
  }

  for (const sig of (breaking || []).slice(0, 10)) {
    items.push({
      id: `sig-${sig.keyword || sig.entity || Math.random()}`,
      type: "signal",
      title: sig.keyword || sig.entity || "Unknown",
      body: `${sig.signal.replace("_", " ")} with burst factor ${(sig.burst_factor || 1).toFixed(1)}× above baseline.`,
      entities: sig.entity ? [sig.entity] : [],
      sectors: [],
      confidence: Math.min(sig.score / 100, 0.99),
      meta: `score ${sig.score.toFixed(1)} · ${sig.recent_count || 0} articles`,
    })
  }

  if (narratives) {
    const emerging = narratives.emerging_topics || []
    for (const t of emerging.slice(0, 8)) {
      items.push({
        id: `narr-${t.cluster || Math.random()}`,
        type: "narrative",
        title: t.topic || `Cluster ${t.cluster}`,
        body: `Entering ${t.phase || "emerging"} phase with acceleration ${(t.acceleration || 0).toFixed(1)}. This topic is gaining traction across ${t.count || 0} articles.`,
        entities: (t.keywords || []).slice(0, 5),
        sectors: t.sectors || [],
        confidence: Math.min(Math.abs(t.acceleration || 0) / 10, 0.99) || 0.5,
        meta: `${t.count || 0} articles · momentum ${(t.momentum || 0).toFixed(1)}`,
      })
    }
  }

  if (influence) {
    const entities = influence.entity_influence || []
    for (const e of entities.slice(0, 8)) {
      items.push({
        id: `inf-${e.entity || Math.random()}`,
        type: "influence",
        title: e.entity || "Unknown",
        body: `Influence score ${(e.influence_score || 0).toFixed(2)} with cross-domain reach across ${e.cross_domain_reach || 0} sectors and ${e.source_diversity || 0} distinct sources.`,
        entities: [e.entity].filter(Boolean),
        sectors: [],
        confidence: Math.min((e.influence_score || 0) / 6, 0.99),
        meta: `score ${(e.influence_score || 0).toFixed(2)} · ${e.source_diversity || 0} sources`,
      })
    }
  }

  items.sort((a, b) => b.confidence - a.confidence)
  return items.slice(0, 40)
}

export function HomePage() {
  const [discoveries, setDiscoveries] = useState<Discovery[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.crossDomain().catch(() => ({ links: [], chains: [], sector_map: {} })),
      api.breaking().catch(() => []),
      api.narratives().catch(() => ({})),
      api.influence().catch(() => ({})),
    ]).then(([cd, breaking, narratives, influence]) => {
      setDiscoveries(buildFeed((cd as any).links || [], breaking, narratives, influence))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-5">
        <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Loading discoveries...</p>
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] p-6 animate-pulse">
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
      <div className="border-b border-[var(--color-border)] pb-5">
        <h1 className="text-xl font-serif text-[var(--color-fg)]" style={{ fontStyle: "italic" }}>Intelligence Feed</h1>
        <p className="text-xs font-mono text-[var(--color-fg-muted)] mt-1 tracking-wider uppercase">
          {discoveries.length} discoveries · cross-domain intelligence
        </p>
      </div>

      <div className="space-y-3">
        {discoveries.map((d, i) => {
          const meta = TYPE_META[d.type]
          return (
            <div
              key={d.id}
              className="animate-slideUp rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] hover:border-[var(--color-border-hover)] transition-all"
              style={{ animationDelay: `${i * 30}ms` }}
            >
              <button
                onClick={() => setExpanded(expanded === d.id ? null : d.id)}
                className="w-full text-left p-5"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: meta.dot }} />
                  <span className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-widest uppercase">{meta.label}</span>
                  <span className="text-[10px] font-mono text-[var(--color-fg-muted)] ml-auto">
                    {(d.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <h2 className="text-base font-serif text-[var(--color-fg)] leading-snug">{d.title}</h2>

                <p className="text-sm text-[var(--color-fg-secondary)] mt-1.5 leading-relaxed">{d.body}</p>

                {d.entities.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {d.entities.map((e) => (
                      <span key={e} className="text-[10px] font-mono text-[var(--color-accent)] bg-[var(--color-accent-subtle)] rounded px-1.5 py-0.5">
                        {e}
                      </span>
                    ))}
                  </div>
                )}

                <div className="mt-3 text-[10px] font-mono text-[var(--color-fg-muted)]">{d.meta}</div>

                {expanded === d.id && (
                  <div className="mt-4 pt-4 border-t border-[var(--color-border)] text-xs font-mono text-[var(--color-fg-muted)] space-y-1">
                    <div>Confidence: {(d.confidence * 100).toFixed(1)}%</div>
                    <div>Sectors: {d.sectors.map((s) => SECTOR_LABELS[s] || s).join(", ") || "general"}</div>
                  </div>
                )}
              </button>
            </div>
          )
        })}
      </div>

      {discoveries.length === 0 && (
        <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">No discoveries yet. Run the pipeline to generate intelligence.</p>
        </div>
      )}
    </div>
  )
}
