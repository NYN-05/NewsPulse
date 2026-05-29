import { useMemo, useCallback } from "react"
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import type { CrossDomainLink } from "@/types"

const SECTOR_COLORS: Record<string, string> = {
  politics: "#4a7cf7",
  finance: "#4fcf8d",
  technology: "#5bc0eb",
  energy: "#d4a757",
  military: "#e06c7a",
  startups: "#8b7cf7",
  social: "#f0a5d4",
  global_events: "#45c4b0",
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

function EntityNode({ data }: NodeProps) {
  const sector = data.sector as string
  const color = SECTOR_COLORS[sector] || "#4a7cf7"
  const isSelected = data.selected as boolean
  return (
    <div
      className="relative px-4 py-2.5 rounded-lg border shadow-lg cursor-pointer transition-all hover:shadow-xl"
      style={{
        background: isSelected ? "var(--color-accent-subtle)" : "var(--color-card)",
        borderColor: isSelected ? "var(--color-accent)" : color,
        borderWidth: isSelected ? 2 : 1.5,
        minWidth: 120,
        boxShadow: isSelected ? `0 0 20px rgba(74, 124, 247, 0.15)` : undefined,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: color, width: 8, height: 8 }} />
      <div className="flex flex-col gap-0.5">
        <span className="text-xs font-mono font-medium leading-tight truncate max-w-[140px]" style={{ color: "var(--color-fg)" }}>
          {data.label as string}
        </span>
        <span className="text-[9px] font-mono uppercase tracking-wider" style={{ color }}>{SECTOR_LABELS[sector] || sector}</span>
      </div>
      <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2" style={{ background: color, borderColor: "var(--color-bg)" }} />
      <Handle type="source" position={Position.Right} style={{ background: color, width: 8, height: 8 }} />
      {data.strength !== undefined && (
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 text-[8px] font-mono px-1.5 rounded" style={{ background: "var(--color-bg)", color: "var(--color-fg-muted)" }}>
          {(data.strength as number).toFixed(1)}
        </div>
      )}
    </div>
  )
}

const nodeTypes = { entityNode: EntityNode }

function buildPositions(count: number) {
  const positions: { x: number; y: number }[] = []
  const cx = 400
  const cy = 250
  const radius = Math.min(400, 250) * 0.4
  for (let i = 0; i < count; i++) {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2
    positions.push({ x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) })
  }
  return positions
}

function explainRelationship(src: string, tgt: string, srcSec: string, tgtSec: string): string {
  const sl = SECTOR_EXPLANATIONS[srcSec] || srcSec
  const tl = SECTOR_EXPLANATIONS[tgtSec] || tgtSec
  return `Changes in ${src} (${sl}) directly affect ${tgt} (${tl}) through cross-domain dependencies.`
}

export function RelationshipGraph({
  links,
  onNodeClick,
  selectedEntity,
}: {
  links: CrossDomainLink[]
  onNodeClick?: (entity: string) => void
  selectedEntity?: string | null
}) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const entityMap = new Map<string, { sectors: Set<string>; strength: number; linkCount: number }>()
    for (const link of links) {
      for (const ent of [link.source_entity, link.target_entity]) {
        if (!entityMap.has(ent)) entityMap.set(ent, { sectors: new Set(), strength: 0, linkCount: 0 })
        const record = entityMap.get(ent)!
        record.sectors.add(link.source_entity === ent ? link.source_sector : link.target_sector)
        record.strength += link.strength
        record.linkCount++
      }
    }
    const entities = Array.from(entityMap.keys())
    const positions = buildPositions(entities.length)
    const nodes: Node[] = entities.map((entity, i) => {
      const record = entityMap.get(entity)!
      return {
        id: entity,
        type: "entityNode",
        position: positions[i],
        data: {
          label: entity,
          sector: Array.from(record.sectors)[0] || "politics",
          strength: record.strength / record.linkCount,
          linkCount: record.linkCount,
          selected: entity === selectedEntity,
        },
        draggable: true,
      }
    })
    const maxStrength = Math.max(...links.map((l) => l.strength), 1)
    const edges: Edge[] = links.map((link, i) => {
      const thickness = Math.max(1, (link.strength / maxStrength) * 5)
      const opacity = Math.max(0.2, link.strength / maxStrength)
      const isConnected = selectedEntity && (link.source_entity === selectedEntity || link.target_entity === selectedEntity)
      return {
        id: `e-${i}`,
        source: link.source_entity,
        target: link.target_entity,
        animated: link.strength > 15,
        style: {
          stroke: isConnected ? "var(--color-accent)" : "var(--color-border)",
          strokeWidth: isConnected ? thickness : 0.5,
          opacity: isConnected ? opacity : 0.15,
        },
        label: isConnected ? link.strength.toFixed(1) : "",
        labelStyle: { fontSize: 9, fontFamily: "JetBrains Mono, monospace", fill: "var(--color-fg-muted)" },
        labelBgStyle: { fill: "var(--color-bg)" },
        labelBgPadding: [4, 2] as [number, number],
        labelBgBorderRadius: 2,
        data: { strength: link.strength, sourceSector: link.source_sector, targetSector: link.target_sector, cooccurrenceCount: link.cooccurrence_count },
      }
    })
    return { nodes, edges }
  }, [links, selectedEntity])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  if (!links || links.length === 0) {
    return (
      <div className="flex h-[500px] items-center justify-center rounded-lg border border-dashed border-[var(--color-border)]">
        <p className="text-xs font-mono text-[var(--color-fg-muted)]">No relationships to display.</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] overflow-hidden" style={{ height: 520 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.2}
        maxZoom={3}
        proOptions={{ hideAttribution: true }}
        style={{ background: "var(--color-bg)", width: "100%", height: "100%" }}
        onNodeClick={(_, node) => onNodeClick?.(node.id)}
      >
        <Background color="var(--color-border)" gap={24} size={1} />
        <Controls className="[&>button]:bg-[var(--color-card)] [&>button]:border-[var(--color-border)] [&>button]:text-[var(--color-fg-muted)] [&>button:hover]:bg-[var(--color-card-hover)]" />
        <MiniMap
          nodeColor={(node) => { const d = node.data as { sector?: string }; return SECTOR_COLORS[d.sector || ""] || "#4a7cf7" }}
          maskColor="rgba(8, 12, 20, 0.7)"
          style={{ background: "var(--color-card)", border: "1px solid var(--color-border)" }}
        />
      </ReactFlow>
    </div>
  )
}

export function RelationshipExplanation({ link }: { link: CrossDomainLink }) {
  return (
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
      <div className="grid grid-cols-3 gap-3 text-[10px] font-mono">
        <div className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-2">
          <div className="text-[var(--color-fg-muted)]">Strength</div>
          <div className="text-[var(--color-accent)] mt-0.5">{link.strength.toFixed(1)}</div>
        </div>
        <div className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-2">
          <div className="text-[var(--color-fg-muted)]">Co-occurrences</div>
          <div className="text-[var(--color-fg)] mt-0.5">{link.cooccurrence_count}</div>
        </div>
        <div className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-2">
          <div className="text-[var(--color-fg-muted)]">Source Diversity</div>
          <div className="text-[var(--color-fg)] mt-0.5">{link.source_diversity.toFixed(1)}</div>
        </div>
      </div>
      <div className="flex items-center gap-2 text-[10px] font-mono text-[var(--color-fg-muted)]">
        <span className="rounded px-1.5 py-0.5 bg-[var(--color-card)] border border-[var(--color-border)]" style={{ color: SECTOR_COLORS[link.source_sector] }}>
          {SECTOR_LABELS[link.source_sector] || link.source_sector}
        </span>
        <span>→</span>
        <span className="rounded px-1.5 py-0.5 bg-[var(--color-card)] border border-[var(--color-border)]" style={{ color: SECTOR_COLORS[link.target_sector] }}>
          {SECTOR_LABELS[link.target_sector] || link.target_sector}
        </span>
      </div>
    </div>
  )
}
