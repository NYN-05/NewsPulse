import type { CrossDomainData, SignalsData, SearchResult, NarrativeData, PipelineStatus } from "@/types"

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
}
