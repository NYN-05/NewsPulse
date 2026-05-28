import { useEffect, useState } from "react"
import { api } from "@/services/api"
import type { CrossDomainLink, BreakingEvent } from "@/types"

interface Discovery {
  id: string
  type: "cross_domain" | "narrative" | "influence" | "signal"
  title: string
  summary: string
  entities: string[]
  sectors: string[]
  confidence: number
  timestamp: string
  detail: string
}

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

function buildFeed(cd: { links: CrossDomainLink[] }, breaking: BreakingEvent[], narratives: any, influence: any): Discovery[] {
  const items: Discovery[] = []

  // Cross-domain links → discoveries
  for (const link of (cd.links || []).slice(0, 30)) {
    if (link.strength < 3) continue
    items.push({
      id: `cd-${link.source_entity}-${link.target_entity}`,
      type: "cross_domain",
      title: `${link.source_entity} ↔ ${link.target_entity}`,
      summary: `Cross-domain connection bridging ${SECTOR_LABELS[link.source_sector] || link.source_sector} and ${SECTOR_LABELS[link.target_sector] || link.target_sector}.`,
      entities: [link.source_entity, link.target_entity],
      sectors: [link.source_sector, link.target_sector],
      confidence: Math.min(link.strength / 30, 1),
      timestamp: new Date().toISOString(),
      detail: `Co-occurrence count: ${link.cooccurrence_count}. Source diversity: ${link.source_diversity.toFixed(2)}. Sentiment variance: ${link.sentiment_variance.toFixed(2)}.`,
    })
  }

  // Breaking signals → discoveries
  for (const sig of (breaking || []).slice(0, 15)) {
    items.push({
      id: `sig-${sig.keyword || sig.entity || Math.random()}`,
      type: "signal",
      title: `Signal: ${sig.keyword || sig.entity || "unknown"}`,
      summary: `Unusual activity detected — ${sig.signal.replace("_", " ")} with burst factor ${(sig.burst_factor || 1).toFixed(1)}× normal.`,
      entities: sig.entity ? [sig.entity] : [],
      sectors: [],
      confidence: Math.min(sig.score / 100, 1),
      timestamp: new Date().toISOString(),
      detail: `Signal type: ${sig.signal}. Score: ${sig.score.toFixed(1)}. Recent count: ${sig.recent_count || 0}.`,
    })
  }

  // Narrative phase changes
  if (narratives) {
    const emerging = narratives.emerging_topics || []
    for (const topic of emerging.slice(0, 10)) {
      items.push({
        id: `narr-${topic.cluster || topic.topic || Math.random()}`,
        type: "narrative",
        title: `Narrative: ${topic.topic || topic.label || `Cluster ${topic.cluster}`}`,
        summary: `Entering ${topic.phase || "emerging"} phase. This narrative is gaining traction across sources.`,
        entities: topic.keywords?.slice(0, 5) || [],
        sectors: topic.sectors || [],
        confidence: Math.min((topic.acceleration || 0) / 10, 1) || 0.5,
        timestamp: new Date().toISOString(),
        detail: `Phase: ${topic.phase || "emerging"}. Momentum: ${(topic.momentum || 0).toFixed(2)}. Article count: ${topic.count || 0}.`,
      })
    }

    const entities = narratives.entity_narratives || []
    for (const e of entities.slice(0, 10)) {
      items.push({
        id: `ent-${e.entity || Math.random()}`,
        type: "influence",
        title: `Entity: ${e.entity || "unknown"}`,
        summary: `Influence phase: ${e.phase || "stable"}. Sentiment trajectory is ${e.sentiment_trajectory || "neutral"}.`,
        entities: [e.entity].filter(Boolean),
        sectors: e.sectors || [],
        confidence: Math.min((e.acceleration || 0) / 5, 1) || 0.5,
        timestamp: new Date().toISOString(),
        detail: `Phase: ${e.phase || "stable"}. Acceleration: ${(e.acceleration || 0).toFixed(2)}. Momentum: ${(e.momentum || 0).toFixed(2)}.`,
      })
    }
  }

  // Influence shifts
  if (influence) {
    const entities = influence.entity_influence || []
    for (const e of entities.slice(0, 10)) {
      items.push({
        id: `inf-${e.entity || Math.random()}`,
        type: "influence",
        title: `Influence: ${e.entity || "unknown"}`,
        summary: `Influence score ${(e.influence_score || 0).toFixed(2)}. Cross-domain reach across ${e.cross_domain_reach || 0} sectors.`,
        entities: [e.entity].filter(Boolean),
        sectors: [],
        confidence: Math.min((e.influence_score || 0) / 6, 1),
        timestamp: new Date().toISOString(),
        detail: `Score: ${(e.influence_score || 0).toFixed(3)}. Sources: ${e.source_diversity || 0}. Centrality: ${(e.centrality || 0).toFixed(3)}. Propagation: ${e.propagation_speed || 0}.`,
      })
    }
  }

  // Sort by confidence descending, take top 50
  items.sort((a, b) => b.confidence - a.confidence)
  return items.slice(0, 50)
}

const TYPE_LABELS: Record<string, string> = {
  cross_domain: "Cross-Domain Link",
  narrative: "Narrative Shift",
  influence: "Influence Update",
  signal: "Signal Spike",
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
      setDiscoveries(buildFeed(cd, breaking, narratives, influence))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-[var(--color-fg-muted)] font-mono">Loading intelligence feed...</p>
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-[var(--color-border)] p-5 animate-pulse">
            <div className="h-4 w-48 bg-[var(--color-border)] rounded mb-3" />
            <div className="h-3 w-96 bg-[var(--color-border)] rounded mb-2" />
            <div className="h-3 w-64 bg-[var(--color-border)] rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-end justify-between border-b border-[var(--color-border)] pb-4">
        <div>
          <h1 className="text-lg font-medium text-[var(--color-fg)]">Intelligence Feed</h1>
          <p className="text-xs text-[var(--color-fg-muted)] mt-0.5">
            {discoveries.length} discoveries · AI-generated across all domains
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {discoveries.map((d) => (
          <div key={d.id} className="animate-slideUp">
            <button
              onClick={() => setExpanded(expanded === d.id ? null : d.id)}
              className="w-full text-left rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] transition-colors p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-fg-muted)]">
                      {TYPE_LABELS[d.type]}
                    </span>
                    <span className="text-[10px] font-mono text-[var(--color-fg-muted)]">·</span>
                    <span className="text-[10px] font-mono text-[var(--color-fg-muted)]">
                      {d.sectors.map((s) => SECTOR_LABELS[s] || s).filter(Boolean).join(", ") || "general"}
                    </span>
                  </div>
                  <h2 className="text-sm font-medium text-[var(--color-fg)]">{d.title}</h2>
                  <p className="text-xs text-[var(--color-fg-secondary)] mt-1">{d.summary}</p>
                  {d.entities.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {d.entities.map((e) => (
                        <span key={e} className="text-[10px] font-mono text-[var(--color-accent)] bg-[var(--color-accent-subtle)] rounded px-1.5 py-0.5">
                          {e}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="shrink-0 text-right">
                  <div className="font-mono text-xs text-[var(--color-fg)]">
                    {(d.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] text-[var(--color-fg-muted)]">confidence</div>
                </div>
              </div>

              {expanded === d.id && (
                <div className="mt-3 pt-3 border-t border-[var(--color-border)] text-xs text-[var(--color-fg-secondary)] leading-relaxed">
                  {d.detail}
                </div>
              )}
            </button>
          </div>
        ))}
      </div>

      {discoveries.length === 0 && (
        <div className="flex h-40 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs text-[var(--color-fg-muted)] font-mono">No discoveries found. Run the pipeline to generate intelligence.</p>
        </div>
      )}
    </div>
  )
}
