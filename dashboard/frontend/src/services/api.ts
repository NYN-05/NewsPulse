import type {
  CrossDomainData, SignalsData, SearchResult, NarrativeData, PipelineStatus,
  CausalAnalysisData, MultiAgentData, TemporalData, BriefingData, AlertData,
} from "@/types"

async function fetchJSON<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${r.status}`)
  return r.json()
}

export const api = {
  health: () => fetchJSON<{ status: string; timestamp: string; version: string; pipeline: PipelineStatus }>("/api/health"),
  pipelineStatus: () => fetchJSON<PipelineStatus>("/api/pipeline-status"),
  triggerPipeline: () => fetchJSON<{ status: string; message: string }>("/api/trigger-pipeline"),
  crossDomain: () => fetchJSON<CrossDomainData>("/api/cross-domain"),
  entityGraph: () => fetchJSON<{ nodes: any[]; edges: any[] }>("/api/entity-graph"),
  signals: () => fetchJSON<SignalsData>("/api/signals"),
  search: (q: string, n = 10) => fetchJSON<{ results: SearchResult[] }>(`/api/search?q=${encodeURIComponent(q)}&n=${n}`),
  narratives: () => fetchJSON<NarrativeData>("/api/narratives"),
  explain: (source: string, target: string) =>
    fetchJSON<{ link: any; explanation: any }>(`/api/explain?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`),
  // Phase 3
  causalAnalysis: () => fetchJSON<CausalAnalysisData>("/api/causal-analysis"),
  // Phase 4
  multiAgentAnalysis: () => fetchJSON<MultiAgentData>("/api/multi-agent-analysis"),
  temporalPatterns: () => fetchJSON<TemporalData>("/api/temporal-patterns"),
  briefing: () => fetchJSON<BriefingData>("/api/briefing"),
  // Phase 5
  alerts: () => fetchJSON<AlertData>("/api/alerts"),
  export: (fmt: string) => fetchJSON<{ status: string; path: string; format: string }>(`/api/export?fmt=${fmt}`),
  neo4jStatus: () => fetchJSON<any>("/api/neo4j-status"),
}
