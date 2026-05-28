import type {
  Summary, SentimentData, CategoryData, TrendData, ClusterData,
  EntityGraph, EntityTrend, BreakingEvent, TopicCluster,
  SourceReliability, ViralityData, BiasData, LanguageData,
  SearchResult, ArticleRecord, SourceCount, CrossDomainData,
} from "@/types"

const BASE = "/api"

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
  return res.json()
}

export const api = {
  health: () => fetchJSON<{ status: string }>(`${BASE}/health`),

  summary: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params) : ""
    return fetchJSON<Summary>(`${BASE}/summary${q}`)
  },

  sentiment: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params) : ""
    return fetchJSON<SentimentData>(`${BASE}/sentiment${q}`)
  },

  categories: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params) : ""
    return fetchJSON<CategoryData[]>(`${BASE}/categories${q}`)
  },

  trends: () => fetchJSON<{ top_keywords: TrendData[] }>(`${BASE}/trends`),

  clusters: () => fetchJSON<ClusterData[]>(`${BASE}/clusters`),

  entityGraph: () => fetchJSON<EntityGraph>(`${BASE}/entity-graph`),

  entityTrends: () => fetchJSON<EntityTrend[]>(`${BASE}/entity-trends`),

  breaking: () => fetchJSON<BreakingEvent[]>(`${BASE}/breaking`),

  topicEvolution: () => fetchJSON<{ clusters: TopicCluster[] }>(`${BASE}/topic-evolution`),

  sourceReliability: () => fetchJSON<SourceReliability>(`${BASE}/source-reliability`),

  virality: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params) : ""
    return fetchJSON<ViralityData>(`${BASE}/virality${q}`)
  },

  bias: () => fetchJSON<BiasData>(`${BASE}/bias`),

  languages: () => fetchJSON<LanguageData[]>(`${BASE}/languages`),

  search: (q: string, n = 10) =>
    fetchJSON<{ results: SearchResult[] }>(`${BASE}/search?q=${encodeURIComponent(q)}&n=${n}`),

  data: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params) : ""
    return fetchJSON<ArticleRecord[]>(`${BASE}/data${q}`)
  },

  sources: () => fetchJSON<SourceCount[]>(`${BASE}/sources`),

  crossDomain: () => fetchJSON<CrossDomainData>(`${BASE}/cross-domain`),
}
