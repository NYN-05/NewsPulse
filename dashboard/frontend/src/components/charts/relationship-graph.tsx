import { useMemo } from "react"
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
  type DefaultEdgeOptions,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import type { CrossDomainLink } from "@/types"

const SECTOR_COLORS: Record<string, string> = {
  politics: "#8b7cf7",
  finance: "#6fcf8d",
  technology: "#7bc9e8",
  energy: "#d4a757",
  military: "#e06c7a",
  startups: "#a399fa",
  social: "#f0a5d4",
  global_events: "#7ae0c0",
}

const SECTOR_LABELS: Record<string, string> = {
  politics: "Politics", finance: "Finance", technology: "Technology",
  energy: "Energy", military: "Military", startups: "Startups",
  social: "Social", global_events: "Global Events",
}

function EntityNode({ data }: NodeProps) {
  const sector = data.sector as string
  const color = SECTOR_COLORS[sector] || "#8b7cf7"
  return (
    <div
      className="relative px-4 py-2.5 rounded-lg border shadow-lg cursor-pointer transition-shadow hover:shadow-xl"
      style={{
        background: "var(--color-card)",
        borderColor: color,
        borderWidth: 2,
        minWidth: 120,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: color, width: 8, height: 8 }} />
      <div className="flex flex-col gap-0.5">
        <span
          className="text-xs font-mono font-medium leading-tight truncate max-w-[140px]"
          style={{ color: "var(--color-fg)" }}
        >
          {data.label as string}
        </span>
        <span className="text-[9px] font-mono uppercase tracking-wider" style={{ color }}>
          {SECTOR_LABELS[sector] || sector}
        </span>
      </div>
      <div
        className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2"
        style={{ background: color, borderColor: "var(--color-bg)" }}
      />
      <Handle type="source" position={Position.Right} style={{ background: color, width: 8, height: 8 }} />
      {data.strength !== undefined && (
        <div
          className="absolute -bottom-1 left-1/2 -translate-x-1/2 text-[8px] font-mono px-1.5 rounded"
          style={{ background: "var(--color-bg)", color: "var(--color-fg-muted)" }}
        >
          {(data.strength as number).toFixed(1)}
        </div>
      )}
    </div>
  )
}

const nodeTypes = { entityNode: EntityNode }

function buildPositions(count: number, width: number, height: number) {
  const positions: { x: number; y: number }[] = []
  const cx = width / 2
  const cy = height / 2
  const radius = Math.min(width, height) * 0.35
  for (let i = 0; i < count; i++) {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2
    positions.push({
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    })
  }
  return positions
}

export function RelationshipGraph({
  links,
  onNodeClick,
}: {
  links: CrossDomainLink[]
  onNodeClick?: (entity: string) => void
}) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const entityMap = new Map<string, { sectors: Set<string>; strength: number; linkCount: number }>()
    for (const link of links) {
      for (const ent of [link.source_entity, link.target_entity]) {
        if (!entityMap.has(ent)) {
          entityMap.set(ent, { sectors: new Set(), strength: 0, linkCount: 0 })
        }
        const record = entityMap.get(ent)!
        record.sectors.add(link.source_entity === ent ? link.source_sector : link.target_sector)
        record.strength += link.strength
        record.linkCount++
      }
    }

    const entities = Array.from(entityMap.keys())
    const positions = buildPositions(entities.length, 800, 500)

    const nodes: Node[] = entities.map((entity, i) => {
      const record = entityMap.get(entity)!
      const primarySector = Array.from(record.sectors)[0] || "politics"
      return {
        id: entity,
        type: "entityNode",
        position: positions[i],
        data: {
          label: entity,
          sector: primarySector,
          strength: record.strength / record.linkCount,
          linkCount: record.linkCount,
        },
        draggable: true,
      }
    })

    const maxStrength = Math.max(...links.map((l) => l.strength), 1)
    const edges: Edge[] = links.map((link, i) => {
      const thickness = Math.max(1, (link.strength / maxStrength) * 6)
      const opacity = Math.max(0.2, link.strength / maxStrength)
      return {
        id: `e-${i}`,
        source: link.source_entity,
        target: link.target_entity,
        animated: link.strength > 15,
        style: {
          stroke: "var(--color-accent)",
          strokeWidth: thickness,
          opacity,
        },
        label: link.strength.toFixed(1),
        labelStyle: {
          fontSize: 9,
          fontFamily: "JetBrains Mono, monospace",
          fill: "var(--color-fg-muted)",
        },
        labelBgStyle: { fill: "var(--color-bg)" },
        labelBgPadding: [4, 2] as [number, number],
        labelBgBorderRadius: 2,
        data: {
          strength: link.strength,
          sourceSector: link.source_sector,
          targetSector: link.target_sector,
          cooccurrenceCount: link.cooccurrence_count,
        },
      }
    })

    return { nodes, edges }
  }, [links])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const defaultEdgeOptions: DefaultEdgeOptions = {
    style: { stroke: "var(--color-accent)", strokeWidth: 2 },
  }

  if (!links || links.length === 0) {
    return (
      <div className="flex h-[500px] items-center justify-center rounded-lg border border-dashed border-[var(--color-border)]">
        <p className="text-xs font-mono text-[var(--color-fg-muted)]">No relationships to display.</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] overflow-hidden" style={{ height: 560 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.2}
        maxZoom={3}
        proOptions={{ hideAttribution: true }}
        style={{ background: "var(--color-bg)", width: "100%", height: "100%" }}
        onNodeClick={(_, node) => onNodeClick?.(node.id)}
      >
        <Background color="var(--color-border)" gap={24} size={1} />
        <Controls
          className="[&>button]:bg-[var(--color-card)] [&>button]:border-[var(--color-border)] [&>button]:text-[var(--color-fg-muted)] [&>button:hover]:bg-[var(--color-card-hover)]"
        />
        <MiniMap
          nodeColor={(node) => {
            const d = node.data as { sector?: string }
            return SECTOR_COLORS[d.sector || ""] || "#8b7cf7"
          }}
          maskColor="rgba(8, 7, 12, 0.7)"
          style={{ background: "var(--color-card)", border: "1px solid var(--color-border)" }}
        />
      </ReactFlow>
    </div>
  )
}
