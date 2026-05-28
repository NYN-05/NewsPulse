import type { CrossDomainData, BreakingEvent, SearchResult, NarrativeData, InfluenceData } from "@/types"

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  health: () => fetchJSON<{ status: string }>("/api/health"),

  crossDomain: () => fetchJSON<CrossDomainData>("/api/cross-domain"),

  breaking: () => fetchJSON<BreakingEvent[]>("/api/breaking"),

  search: (q: string, n = 10) =>
    fetchJSON<{ results: SearchResult[] }>(`/api/search?q=${encodeURIComponent(q)}&n=${n}`),

  narratives: () => fetchJSON<NarrativeData>("/api/narratives"),

  influence: () => fetchJSON<InfluenceData>("/api/influence"),

  entityGraph: () => fetchJSON<any>("/api/entity-graph"),

  sources: () => fetchJSON<{ name: string; count: number }[]>("/api/sources"),
}
