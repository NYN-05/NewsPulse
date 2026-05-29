import type { CrossDomainData, BreakingEvent, SearchResult } from "@/types"

async function fetchJSON<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${r.status}`)
  return r.json()
}

export const api = {
  health: () => fetchJSON<{ status: string }>("/api/health"),
  crossDomain: () => fetchJSON<CrossDomainData>("/api/cross-domain"),
  breaking: () => fetchJSON<BreakingEvent[]>("/api/breaking"),
  search: (q: string, n = 10) => fetchJSON<{ results: SearchResult[] }>(`/api/search?q=${encodeURIComponent(q)}&n=${n}`),
  narratives: () => fetchJSON<any>("/api/narratives"),
  influence: () => fetchJSON<any>("/api/influence"),
}
