import { useMemo, useEffect } from "react"
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import type { CrossDomainLink } from "@/types"

const SECTOR_COLORS: Record<string, string> = {
  politics: "#4a7cf7", finance: "#4fcf8d", technology: "#5bc0eb",
  energy: "#d4a757", military: "#e06c7a", startups: "#8b7cf7",
  social: "#f0a5d4", global_events: "#45c4b0",
}

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

function EntityNode({ data }: NodeProps) {
  const sector = data.sector as string
  const color = SECTOR_COLORS[sector] || "#4a7cf7"
  const isSelected = data.selected as boolean
  const isCenter = data.isCenter as boolean
  return (
    <div
      className="relative px-3 py-2 rounded-lg border cursor-pointer transition-all hover:shadow-xl"
      style={{
        background: isCenter ? "var(--color-accent-subtle)" : "var(--color-card)",
        borderColor: isCenter ? "var(--color-accent)" : color,
        borderWidth: isCenter ? 2 : 1,
        minWidth: 100,
        boxShadow: isCenter ? "0 0 24px rgba(74, 124, 247, 0.2)" : undefined,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: color, width: 6, height: 6 }} />
      <div className="flex flex-col gap-0.5">
        <span className="text-[11px] font-mono font-medium leading-tight truncate max-w-[120px]" style={{ color: "var(--color-fg)" }}>
          {data.label as string}
        </span>
        <span className="text-[8px] font-mono uppercase tracking-wider" style={{ color }}>{SECTOR_LABELS[sector] || sector}</span>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: color, width: 6, height: 6 }} />
      {data.strength !== undefined && (
        <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 text-[7px] font-mono px-1 rounded" style={{ background: "var(--color-bg)", color: "var(--color-fg-muted)" }}>
          {(data.strength as number).toFixed(1)}
        </div>
      )}
    </div>
  )
}

const nodeTypes = { entityNode: EntityNode }

const SECTOR_LABELS_MAP: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

const SECTOR_COLORS_MAP: Record<string, string> = {
  politics: "#4a7cf7", finance: "#4fcf8d", technology: "#5bc0eb",
  energy: "#d4a757", military: "#e06c7a", startups: "#8b7cf7",
  social: "#f0a5d4", global_events: "#45c4b0",
}

export function EmptyGraphOverlay({
  allLinks,
  stats,
}: {
  allLinks: CrossDomainLink[]
  stats: { entityCount: number; sectorCount: number; topSectors: [string, number][] }
}) {
  const top5 = useMemo(() => [...allLinks].sort((a, b) => b.strength - a.strength).slice(0, 5), [allLinks])
  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
      <div className="max-w-lg w-full mx-8 pointer-events-auto">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--color-accent)] animate-pulseGlow" />
            <span className="text-[10px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Intelligence Canvas</span>
          </div>
          <div className="grid grid-cols-3 gap-3 text-[11px] font-mono">
            <div className="border border-[var(--color-border)] rounded-lg p-3 bg-[var(--color-card)]">
              <p className="text-[var(--color-fg-muted)] text-[9px] tracking-wider uppercase">Connections</p>
              <p className="text-[var(--color-accent)] text-lg mt-1 font-medium">{allLinks.length}</p>
            </div>
            <div className="border border-[var(--color-border)] rounded-lg p-3 bg-[var(--color-card)]">
              <p className="text-[var(--color-fg-muted)] text-[9px] tracking-wider uppercase">Entities</p>
              <p className="text-[var(--color-fg)] text-lg mt-1 font-medium">{stats.entityCount}</p>
            </div>
            <div className="border border-[var(--color-border)] rounded-lg p-3 bg-[var(--color-card)]">
              <p className="text-[var(--color-fg-muted)] text-[9px] tracking-wider uppercase">Domains</p>
              <p className="text-[var(--color-fg)] text-lg mt-1 font-medium">{stats.sectorCount}</p>
            </div>
          </div>
          {top5.length > 0 && (
            <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-card)] p-3">
              <p className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase mb-2">Top Cross-Domain Relationships</p>
              <div className="space-y-1.5">
                {top5.map((l, i) => (
                  <div key={i} className="flex items-center gap-2 text-[10px] font-mono">
                    <span className="text-[var(--color-fg-muted)] w-4 shrink-0 text-right">{i + 1}.</span>
                    <span className="text-[var(--color-fg)] truncate">{l.source_entity}</span>
                    <span className="text-[var(--color-accent)] shrink-0">&harr;</span>
                    <span className="text-[var(--color-fg)] truncate">{l.target_entity}</span>
                    <span className="text-[var(--color-fg-muted)] shrink-0 ml-auto">{l.strength.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {stats.topSectors.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {stats.topSectors.map(([s, c]) => (
                <span key={s} className="text-[9px] font-mono px-2 py-1 rounded border"
                  style={{ color: SECTOR_COLORS_MAP[s] || "#4a7cf7", borderColor: SECTOR_COLORS_MAP[s] || "#4a7cf7", background: `${SECTOR_COLORS_MAP[s] || "#4a7cf7"}10` }}>
                  {SECTOR_LABELS_MAP[s] || s} &middot; {c}
                </span>
              ))}
            </div>
          )}
          <p className="text-[9px] font-mono text-[var(--color-fg-muted)] leading-relaxed">
            Select an entity from the discovery panel to explore its cross-domain relationships on this canvas.
          </p>
        </div>
      </div>
    </div>
  )
}

export function FocusedGraph({
  selectEntity,
  selectedEntity,
  connectedLinks,
  onNodeClick,
  onEdgeClick,
  allLinks,
  stats,
}: {
  selectEntity: (e: string) => void
  selectedEntity: string | null
  connectedLinks: CrossDomainLink[]
  onNodeClick?: (entity: string) => void
  onEdgeClick?: (link: CrossDomainLink) => void
  allLinks: CrossDomainLink[]
  stats: { entityCount: number; sectorCount: number; topSectors: [string, number][] }
}) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!selectedEntity || connectedLinks.length === 0) return { nodes: [], edges: [] }

    const connected = new Set<string>()
    connectedLinks.forEach((l) => {
      connected.add(l.source_entity)
      connected.add(l.target_entity)
    })
    const allEntities = Array.from(connected)
    const isSmall = allEntities.length <= 15
    const visible = isSmall ? allEntities : [selectedEntity, ...allEntities.filter((e) => e !== selectedEntity).slice(0, 14)]

    const centerX = 350; const centerY = 250
    const radius = Math.min(220, 80 + visible.length * 18)

    const nodes: Node[] = visible.map((entity, i) => {
      let x: number, y: number
      if (entity === selectedEntity) {
        x = centerX; y = centerY
      } else {
        const angle = (2 * Math.PI * (i - 1)) / Math.max(visible.length - 1, 1) - Math.PI / 2
        x = centerX + radius * Math.cos(angle)
        y = centerY + radius * Math.sin(angle)
      }
      const link = connectedLinks.find((l) => l.source_entity === entity || l.target_entity === entity)
      const sector = link ? (link.source_entity === entity ? link.source_sector : link.target_sector) : "politics"
      const strength = link?.strength || 0
      return {
        id: entity,
        type: "entityNode",
        position: { x, y },
        data: { label: entity, sector, strength, isCenter: entity === selectedEntity, selected: entity === selectedEntity },
        draggable: true,
      }
    })

    const maxStrength = Math.max(...connectedLinks.map((l) => l.strength), 1)
    const edges: Edge[] = connectedLinks
      .filter((l) => visible.includes(l.source_entity) && visible.includes(l.target_entity))
      .map((link, i) => {
        const thickness = Math.max(1, (link.strength / maxStrength) * 4)
        const opacity = Math.max(0.3, link.strength / maxStrength)
        return {
          id: `e-${i}`,
          source: link.source_entity,
          target: link.target_entity,
          animated: false,
          style: { stroke: "var(--color-accent)", strokeWidth: thickness, opacity },
          label: link.strength.toFixed(1),
          labelStyle: { fontSize: 8, fontFamily: "JetBrains Mono, monospace", fill: "var(--color-fg-muted)" },
          labelBgStyle: { fill: "var(--color-bg)" },
          labelBgPadding: [3, 1] as [number, number],
          labelBgBorderRadius: 2,
          data: { originalLink: link },
          interactionWidth: 20,
        }
      })

    return { nodes, edges }
  }, [selectedEntity, connectedLinks])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  useEffect(() => {
    setNodes(initialNodes)
    setEdges(initialEdges)
  }, [initialNodes, initialEdges])

  return (
    <div className="relative h-full w-full">
      {!selectedEntity && <EmptyGraphOverlay allLinks={allLinks} stats={stats} />}
      {selectedEntity && connectedLinks.length === 0 && (
        <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
          <p className="text-xs font-mono text-[var(--color-fg-muted)]">No connections found for this entity.</p>
        </div>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.15}
        maxZoom={5}
        proOptions={{ hideAttribution: true }}
        style={{ background: "var(--color-bg)", width: "100%", height: "100%" }}
        onNodeClick={(_, node) => onNodeClick?.(node.id)}
        onEdgeClick={(_, edge) => {
          const original = (edge.data as any)?.originalLink as CrossDomainLink | undefined
          if (original) onEdgeClick?.(original)
        }}
      >
        <Background color="var(--color-border)" gap={30} size={0.5} />
        <Controls className="[&>button]:bg-[var(--color-card)] [&>button]:border-[var(--color-border)] [&>button]:text-[var(--color-fg-muted)] [&>button:hover]:bg-[var(--color-card-hover)]" />
      </ReactFlow>
    </div>
  )
}

function explainRelationship(src: string, tgt: string, srcSec: string, tgtSec: string): string {
  const m: Record<string, string> = {
    politics: "political dynamics", finance: "financial markets", technology: "tech sector",
    energy: "energy markets", military: "military affairs", startups: "startup ecosystem",
    social: "social trends", global_events: "global events",
  }
  return `${src} (${m[srcSec] || srcSec}) and ${tgt} (${m[tgtSec] || tgtSec}) are connected through cross-domain dependencies. Changes in one directly create measurable effects in the other.`
}

export function IntelligencePanel({
  link,
  totalLinks,
}: {
  link: CrossDomainLink
  totalLinks: number
}) {
  const relPct = Math.min((link.strength / 50) * 100, 100)
  const impact = relPct > 70 ? "High" : relPct > 40 ? "Medium" : "Low"
  const impactColor = impact === "High" ? "var(--color-red)" : impact === "Medium" ? "var(--color-amber)" : "var(--color-fg-muted)"

  return (
    <div className="space-y-4 animate-slideUp">
      <div className="rounded-lg border border-[var(--color-accent)] bg-[var(--color-accent-subtle)] p-4 space-y-3">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)]" />
          <span className="text-[10px] font-mono text-[var(--color-accent)] tracking-wider uppercase">Intelligence Assessment</span>
        </div>
        <div className="flex items-center gap-2 text-sm font-serif text-[var(--color-fg)]">
          <span>{link.source_entity}</span>
          <span className="text-[var(--color-accent)] font-mono text-xs">↔</span>
          <span>{link.target_entity}</span>
        </div>
        <p className="text-xs text-[var(--color-fg-secondary)] leading-relaxed">
          {explainRelationship(link.source_entity, link.target_entity, link.source_sector, link.target_sector)}
        </p>
        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
          <div className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-2">
            <div className="text-[var(--color-fg-muted)]">Relationship Strength</div>
            <div className="text-[var(--color-accent)] mt-0.5 text-sm">{relPct.toFixed(0)}%</div>
          </div>
          <div className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-2">
            <div className="text-[var(--color-fg-muted)]">Impact Assessment</div>
            <div className="mt-0.5 text-sm" style={{ color: impactColor }}>{impact}</div>
          </div>
          <div className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-2">
            <div className="text-[var(--color-fg-muted)]">Co-occurrences</div>
            <div className="text-[var(--color-fg)] mt-0.5 text-sm">{link.cooccurrence_count}</div>
          </div>
          <div className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-2">
            <div className="text-[var(--color-fg-muted)]">Source Diversity</div>
            <div className="text-[var(--color-fg)] mt-0.5 text-sm">{link.source_diversity.toFixed(1)}</div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4">
        <div className="text-[10px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase mb-2">Domains</div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="rounded px-1.5 py-0.5 border" style={{ color: SECTOR_COLORS[link.source_sector], borderColor: SECTOR_COLORS[link.source_sector], background: `${SECTOR_COLORS[link.source_sector]}10` }}>
            {SECTOR_LABELS[link.source_sector] || link.source_sector}
          </span>
          <span className="text-[var(--color-fg-muted)]">→</span>
          <span className="rounded px-1.5 py-0.5 border" style={{ color: SECTOR_COLORS[link.target_sector], borderColor: SECTOR_COLORS[link.target_sector], background: `${SECTOR_COLORS[link.target_sector]}10` }}>
            {SECTOR_LABELS[link.target_sector] || link.target_sector}
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4">
        <div className="text-[10px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase mb-2">Evidence</div>
        <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
          <div><span className="text-[var(--color-accent)]">{link.cooccurrence_count}</span> <span className="text-[var(--color-fg-muted)]">articles</span></div>
          <div><span className="text-[var(--color-accent)]">{Math.round(link.source_diversity)}</span> <span className="text-[var(--color-fg-muted)]">sources</span></div>
          <div><span className="text-[var(--color-accent)]">{totalLinks}</span> <span className="text-[var(--color-fg-muted)]">connections</span></div>
        </div>
      </div>

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4">
        <div className="text-[10px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase mb-2">Potential Downstream Effects</div>
        <p className="text-[10px] font-mono text-[var(--color-fg-secondary)] leading-relaxed">
          This cross-domain relationship may affect supply chains, policy decisions, and market dynamics across connected sectors.
        </p>
      </div>
    </div>
  )
}

export function RelationshipSummary({ selectedEntity, connectedLinks }: { selectedEntity: string | null; connectedLinks: CrossDomainLink[] }) {
  if (!selectedEntity) return null
  const domains = new Set(connectedLinks.flatMap((l) => [l.source_sector, l.target_sector]))
  const strongest = connectedLinks.reduce((a, b) => (a.strength > b.strength ? a : b), connectedLinks[0])
  const avgStrength = connectedLinks.length > 0 ? connectedLinks.reduce((a, l) => a + l.strength, 0) / connectedLinks.length : 0

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-3 space-y-2">
      <div className="text-[9px] font-mono text-[var(--color-fg-muted)] tracking-wider uppercase">Relationship Summary</div>
      <div className="space-y-1.5 text-[10px] font-mono">
        <div className="flex justify-between"><span className="text-[var(--color-fg-muted)]">Selected Entity</span><span className="text-[var(--color-fg)]">{selectedEntity}</span></div>
        <div className="flex justify-between"><span className="text-[var(--color-fg-muted)]">Connected Domains</span><span className="text-[var(--color-accent)]">{domains.size}</span></div>
        {strongest && <div className="flex justify-between"><span className="text-[var(--color-fg-muted)]">Strongest Relationship</span><span className="text-[var(--color-fg)]">{strongest.source_entity === selectedEntity ? strongest.target_entity : strongest.source_entity}</span></div>}
        <div className="flex justify-between"><span className="text-[var(--color-fg-muted)]">Avg Relationship Score</span><span className="text-[var(--color-accent)]">{avgStrength.toFixed(1)}</span></div>
        <div className="flex justify-between"><span className="text-[var(--color-fg-muted)]">Total Connections</span><span className="text-[var(--color-cyan)]">{connectedLinks.length}</span></div>
      </div>
    </div>
  )
}
