import { useEffect, useState } from "react"
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
  politics: "political dynamics",
  finance: "financial markets",
  technology: "tech sector",
  energy: "energy markets",
  military: "military affairs",
  startups: "startup ecosystem",
  social: "social trends",
  global_events: "global events",
}

const TYPE_META: Record<string, { label: string; dot: string }> = {
  cross_domain: { label: "Cross-Domain Link", dot: "#8b7cf7" },
  narrative: { label: "Narrative Shift", dot: "#6fcf8d" },
  influence: { label: "Influence Update", dot: "#d4a757" },
  signal: { label: "Signal Spike", dot: "#e06c7a" },
  chain: { label: "Impact Chain", dot: "#7bc9e8" },
}

function explainRelationship(source: string, target: string, srcSector: string, tgtSector: string): string {
  const srcLabel = SECTOR_EXPLANATIONS[srcSector] || srcSector
  const tgtLabel = SECTOR_EXPLANATIONS[tgtSector] || tgtSector
  return [
    "Relationship between " + source + " (" + srcLabel + ")",
    "and " + target + " (" + tgtLabel + ") -",
    "changes in one directly affect the other through cross-domain dependencies."
  ].join(" ")
}

function explainChain(chain: string[], sectors: string[]): string {
  if (chain.length < 2) return ""
  const pairs: string[] = []
  for (let i = 0; i < chain.length - 1; i++) {
    pairs.push(chain[i] + " -> " + chain[i + 1])
  }
  return "Narrative propagation: " + pairs.join(" => ") + ". This chain crosses " + sectors.length + " domains, revealing how disruption propagates."
}

function buildFeed(
  links: CrossDomainLink[],
  breaking: BreakingEvent[],
  narratives: any,
  influence: any,
): Discovery[] {
  const items: Discovery[] = []

  for (const link of (links || []).slice(0, 20)) {
    if (link.strength < 3) continue
    const srcLabel = SECTOR_LABELS[link.source_sector] || link.source_sector
    const tgtLabel = SECTOR_LABELS[link.target_sector] || link.target_sector
    items.push({
      id: "cd-" + link.source_entity + "-" + link.target_entity,
      type: "cross_domain",
      title: link.source_entity + " <-> " + link.target_entity,
      body: "Connection bridging " + srcLabel + " and " + tgtLabel + ". Co-occurring in " + link.cooccurrence_count + " articles.",
      explanation: explainRelationship(link.source_entity, link.target_entity, link.source_sector, link.target_sector),
      entities: [link.source_entity, link.target_entity],
      sectors: [link.source_sector, link.target_sector],
      confidence: Math.min(link.strength / 30, 0.99),
      meta: link.cooccurrence_count + " co-occurrences - diversity " + link.source_diversity.toFixed(2),
    })
  }

  for (const sig of (breaking || []).slice(0, 8)) {
    items.push({
      id: "sig-" + (sig.keyword || sig.entity || Math.random()),
      type: "signal",
      title: sig.keyword || sig.entity || "Unknown",
      body: (sig.signal || "").replace("_", " ") + " - burst factor " + (sig.burst_factor || 1).toFixed(1) + "x above normal.",
      explanation: "Unusual activity detected: \"" + (sig.keyword || sig.entity) + "\" is being mentioned at " + (sig.burst_factor || 1).toFixed(1) + "x the expected rate. This may indicate an emerging event.",
      entities: sig.entity ? [sig.entity] : [],
      sectors: [],
      confidence: Math.min(sig.score / 100, 0.99),
      meta: "score " + sig.score.toFixed(1) + " - " + (sig.recent_count || 0) + " articles",
    })
  }

  if (narratives) {
    const emerging = narratives.emerging_topics || []
    for (const t of emerging.slice(0, 6)) {
      items.push({
        id: "narr-" + (t.cluster || Math.random()),
        type: "narrative",
        title: t.topic || "Emerging trend",
        body: "Entering " + (t.phase || "emerging") + " phase with acceleration " + (t.acceleration || 0).toFixed(1) + ".",
        explanation: "This topic is gaining momentum (acceleration: " + (t.acceleration || 0).toFixed(2) + "). If sustained, it could signal a major narrative shift.",
        entities: (t.keywords || []).slice(0, 5),
        sectors: t.sectors || [],
        confidence: Math.min(Math.abs(t.acceleration || 0) / 10, 0.99) || 0.5,
        meta: (t.count || 0) + " articles - momentum " + (t.momentum || 0).toFixed(1),
      })
    }

    const mutations = narratives.mutations || []
    for (const m of mutations.slice(0, 4)) {
      items.push({
        id: "mut-" + (m.id || Math.random()),
        type: "narrative",
        title: m.topic || "Narrative mutation",
        body: "Narrative shifted from \"" + m.from + "\" to \"" + m.to + "\" across " + (m.affected_count || 0) + " articles.",
        explanation: m.explanation || "A significant narrative transformation detected - the conversation is evolving in a new direction.",
        entities: [],
        sectors: m.sectors || [],
        confidence: m.confidence || 0.5,
        meta: (m.affected_count || 0) + " articles affected",
      })
    }
  }

  if (influence) {
    const entities = influence.entity_influence || []
    for (const e of entities.slice(0, 6)) {
      const reach = e.cross_domain_reach || e.cross_domain_links || 0
      items.push({
        id: "inf-" + (e.entity || Math.random()),
        type: "influence",
        title: e.entity || "Unknown",
        body: "Influence score " + (e.influence_score || 0).toFixed(2) + " - cross-domain reach across " + reach + " sectors.",
        explanation: "\"" + e.entity + "\" is increasingly central across domains. Its influence score of " + (e.influence_score || 0).toFixed(2) + " suggests growing cross-domain significance.",
        entities: [e.entity].filter(Boolean),
        sectors: [],
        confidence: Math.min((e.influence_score || 0) / 6, 0.99),
        meta: "score " + (e.influence_score || 0).toFixed(2) + " - " + (e.source_diversity || 0) + " sources",
      })
    }
  }

  items.sort((a, b) => b.confidence - a.confidence)
  return items.slice(0, 30)
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
      const feed = buildFeed((cd as any).links || [], breaking, narratives, influence)
      const chains = ((cd as any).chains || []) as ImpactChain[]
      for (const c of chains.slice(0, 4)) {
        if (c.chain && c.chain.length >= 2) {
          feed.push({
            id: "chain-" + (c.chain_key || Math.random()),
            type: "chain",
            title: c.chain.join(" -> "),
            body: "Impact chain spanning " + c.length + " steps across " + c.cross_domain_hops + " domains. Total weight: " + c.total_weight.toFixed(1) + ".",
            explanation: explainChain(c.chain, c.sectors),
            entities: c.chain,
            sectors: c.sectors,
            confidence: Math.min(c.total_weight / 50, 0.99),
            meta: c.length + " hops - " + c.cross_domain_hops + " domains crossed",
          })
        }
      }
      feed.sort((a, b) => b.confidence - a.confidence)
      setDiscoveries(feed.slice(0, 30))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="space-y-5">
        <p className="text-xs font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Analyzing intelligence...</p>
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
          {discoveries.length} discoveries surfacing hidden cross-domain relationships
        </p>
      </div>

      <div className="space-y-3">
        {discoveries.map((d, i) => {
          const meta = TYPE_META[d.type]
          return (
            <div
              key={d.id}
              className="animate-slideUp rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-card-hover)] hover:border-[var(--color-border-hover)] transition-all"
              style={{ animationDelay: (i * 30) + "ms" }}
            >
              <button
                onClick={() => setExpanded(expanded === d.id ? null : d.id)}
                className="w-full text-left p-5"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: meta.dot }} />
                  <span className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-widest uppercase">{meta.label}</span>
                  <span className="text-[10px] font-mono text-[var(--color-fg-muted)] ml-auto">
                    {(d.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>

                <h2 className="text-base font-serif text-[var(--color-fg)] leading-snug">{d.title}</h2>
                <p className="text-sm text-[var(--color-fg-secondary)] mt-1.5 leading-relaxed">{d.body}</p>

                {!expanded && d.explanation && (
                  <p className="text-xs text-[var(--color-accent)] mt-2 font-mono italic opacity-80">
                    {"// "}{d.explanation}
                  </p>
                )}

                <div className="flex flex-wrap gap-1.5 mt-3">
                  {d.entities.slice(0, 4).map((e) => (
                    <span key={e} className="text-[10px] font-mono text-[var(--color-accent)] bg-[var(--color-accent-subtle)] rounded px-1.5 py-0.5">
                      {e}
                    </span>
                  ))}
                </div>

                <div className="mt-3 text-[10px] font-mono text-[var(--color-fg-muted)]">{d.meta}</div>

                {expanded === d.id && (
                  <div className="mt-4 pt-4 border-t border-[var(--color-border)] space-y-2">
                    {d.explanation && (
                      <p className="text-xs text-[var(--color-fg-secondary)] leading-relaxed">{d.explanation}</p>
                    )}
                    <div className="text-[10px] font-mono text-[var(--color-fg-muted)] space-y-0.5">
                      <div>Confidence: {(d.confidence * 100).toFixed(1)}%</div>
                      {d.sectors.length > 0 && (
                        <div>Sectors: {d.sectors.map((s) => SECTOR_LABELS[s] || s).join(", ") || "general"}</div>
                      )}
                    </div>
                  </div>
                )}
              </button>
            </div>
          )
        })}
      </div>

      {discoveries.length === 0 && (
        <div className="flex h-48 items-center justify-center border border-dashed border-[var(--color-border)] rounded-lg">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">
            No discoveries yet. Run the pipeline to surface cross-domain intelligence.
          </p>
        </div>
      )}
    </div>
  )
}
