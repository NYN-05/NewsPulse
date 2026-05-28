import { useMemo, useCallback, useState } from "react"
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeProps,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { Badge } from "@/components/ui/badge"
import type { EntityNode, EntityEdge, CrossDomainLink } from "@/types"

const TYPE_COLORS: Record<string, string> = {
  persons: "#6366f1",
  orgs: "#22d3ee",
  locations: "#f59e0b",
  unknown: "#a1a1aa",
}

const SECTOR_COLORS: Record<string, string> = {
  politics: "#ef4444",
  finance: "#22c55e",
  technology: "#3b82f6",
  energy: "#f59e0b",
  military: "#dc2626",
  startups: "#a855f7",
  social: "#ec4899",
  global_events: "#06b6d4",
  unknown: "#a1a1aa",
}

function EntityGraphNode({ data }: NodeProps) {
  const color = data.sectorColor || TYPE_COLORS[data.entityType] || "#a1a1aa"
  return (
    <div
      className="rounded-xl border-2 px-3 py-2 text-xs shadow-lg backdrop-blur-sm"
      style={{
        borderColor: color,
        background: `${color}15`,
        minWidth: 90,
      }}
    >
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center gap-2">
        <div className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
        <span className="font-medium capitalize">{data.label}</span>
      </div>
      {data.entityType && (
        <Badge variant="outline" className="mt-1 text-[10px]">{data.entityType}</Badge>
      )}
      {data.sector && (
        <div className="mt-0.5 text-[9px] text-[var(--color-muted-foreground)]">{data.sector}</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

const nodeTypes = { entityNode: EntityGraphNode }

export function EntityGraphFlow({ nodes: inNodes, edges: inEdges, height = 500 }: {
  nodes: (EntityNode | { id: string; type?: string; label: string; sector?: string })[]
  edges: (EntityEdge | { source: string; target: string; weight?: number })[]
  height?: number
}) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const rfNodes: Node[] = useMemo(() => {
    const positions = [
      { x: 0, y: 0 }, { x: 200, y: -100 }, { x: -180, y: -80 },
      { x: 100, y: 120 }, { x: -150, y: 100 }, { x: 250, y: 80 },
      { x: -250, y: -40 }, { x: 50, y: -180 }, { x: -80, y: -160 },
      { x: 200, y: 180 }, { x: -200, y: 160 }, { x: 300, y: 0 },
      { x: 150, y: -50 }, { x: -100, y: 50 }, { x: 0, y: 100 },
    ]
    return inNodes.slice(0, 50).map((n, i) => ({
      id: n.id,
      type: "entityNode",
      position: positions[i % positions.length],
      data: {
        label: n.id,
        entityType: (n as EntityNode).type || n.type || "unknown",
        sector: (n as { sector?: string }).sector || undefined,
        sectorColor: (n as { sector?: string }).sector ? SECTOR_COLORS[(n as { sector?: string }).sector!] : undefined,
      },
    }))
  }, [inNodes])

  const rfEdges: Edge[] = useMemo(() => {
    const nodeIds = new Set(rfNodes.map((n) => n.id))
    return inEdges
      .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
      .slice(0, 100)
      .map((e, i) => ({
        id: `e-${i}`,
        source: e.source,
        target: e.target,
        animated: true,
        style: {
          stroke: "var(--color-border)",
          strokeWidth: Math.max(1, Math.min((e.weight || 1) * 0.5, 6)),
        },
        label: (e.weight || 0) > 2 ? String(e.weight) : undefined,
      }))
  }, [rfNodes, inEdges])

  const [nodes, , onNodesChange] = useNodesState(rfNodes)
  const [edges, , onEdgesChange] = useEdgesState(rfEdges)

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node.id === selectedNode ? null : node.id)
  }, [selectedNode])

  return (
    <div className="relative" style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="var(--color-border)" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={(n) => {
            const d = n.data
            return d?.sectorColor || TYPE_COLORS[d?.entityType] || "#a1a1aa"
          }}
          style={{ background: "var(--color-card)", border: "1px solid var(--color-border)" }}
        />
      </ReactFlow>
    </div>
  )
}

export function CrossDomainGraph({ links, sectorMap, height = 500 }: {
  links: CrossDomainLink[]
  sectorMap: Record<string, { entity: string; sector: string; type: string }>
  height?: number
}) {
  const { nodes: cdNodes, edges: cdEdges } = useMemo(() => {
    const entityMap = new Map<string, { sector: string; type: string }>()
    links.forEach((l) => {
      if (!entityMap.has(l.source_entity)) {
        entityMap.set(l.source_entity, { sector: l.source_sector, type: "unknown" })
      }
      if (!entityMap.has(l.target_entity)) {
        entityMap.set(l.target_entity, { sector: l.target_sector, type: "unknown" })
      }
    })
    const topLinks = links.filter((l) => entityMap.has(l.source_entity) && entityMap.has(l.target_entity)).slice(0, 80)

    const positions = [
      { x: 0, y: 0 }, { x: 220, y: -120 }, { x: -200, y: -100 },
      { x: 120, y: 140 }, { x: -170, y: 120 }, { x: 280, y: 60 },
      { x: -260, y: 20 }, { x: 60, y: -200 }, { x: -90, y: -180 },
      { x: 200, y: 200 }, { x: -220, y: 180 }, { x: 320, y: -40 },
      { x: 160, y: -60 }, { x: -120, y: 60 }, { x: 30, y: 120 },
    ]

    const nArr: Node[] = []
    const eArr: Edge[] = []
    let idx = 0

    entityMap.forEach((info, entity) => {
      nArr.push({
        id: entity,
        type: "entityNode",
        position: positions[idx % positions.length],
        data: {
          label: entity,
          entityType: info.type,
          sector: info.sector,
          sectorColor: SECTOR_COLORS[info.sector] || "#a1a1aa",
        },
      })
      idx++
    })

    topLinks.forEach((l, i) => {
      eArr.push({
        id: `cd-e-${i}`,
        source: l.source_entity,
        target: l.target_entity,
        animated: true,
        style: {
          stroke: SECTOR_COLORS[l.source_sector] || "#a1a1aa",
          strokeWidth: Math.max(1, Math.min(l.strength * 0.3, 5)),
          opacity: 0.6,
        },
        label: l.cooccurrence_count > 3 ? String(l.cooccurrence_count) : undefined,
      })
    })

    return { nodes: nArr, edges: eArr }
  }, [links])

  const [nodes, , onNodesChange] = useNodesState(cdNodes)
  const [edges, , onEdgesChange] = useEdgesState(cdEdges)

  return (
    <div style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="var(--color-border)" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={(n) => SECTOR_COLORS[n.data?.sector] || "#a1a1aa"}
          style={{ background: "var(--color-card)", border: "1px solid var(--color-border)" }}
        />
      </ReactFlow>
    </div>
  )
}
