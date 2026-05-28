export interface Summary {
  total_articles: number
  avg_sentiment: number
  avg_sensationalism: number
  avg_virality: number
  sources: number
  categories: number
  vector_indexed: number
}

export interface SentimentData {
  distribution: Record<string, number>
  avg_compound: number
}

export interface CategoryData {
  name: string
  count: number
}

export interface TrendData {
  word: string
  count: number
}

export interface ClusterData {
  label: string
  count: number
  avg_sentiment: number
  top_source: string
}

export interface EntityNode {
  id: string
  type: string
  centrality: number
  betweenness: number
}

export interface EntityEdge {
  source: string
  target: string
  weight: number
  source_type: string
  target_type: string
}

export interface EntityGraph {
  nodes: EntityNode[]
  edges: EntityEdge[]
  stats: {
    total_nodes: number
    total_edges: number
    top_entities: { entity: string; centrality: number }[]
    communities: { id: number; size: number; members: string[] }[]
  }
}

export interface EntityTrend {
  entity: string
  total_mentions: number
  recent_mentions: number
  momentum: number
  peak_date: string
}

export interface BreakingEvent {
  keyword?: string
  entity?: string
  recent_count?: number
  burst_factor?: number
  signal: string
  score: number
}

export interface TopicCluster {
  cluster: number
  label?: string
  total_articles: number
  momentum: number
  trajectory: { date: string; count: number }[]
}

export interface SourceReliability {
  [source: string]: {
    reliability_score: number
    total_articles: number
  }
}

export interface ViralityData {
  distribution: number[]
  avg_virality: number
  top_viral: { title: string; source: string; virality_score: number; sentiment: string; link: string }[]
}

export interface BiasData {
  political_leaning: Record<string, number>
  avg_clickbait: number
  avg_emotional: number
}

export interface LanguageData {
  code: string
  count: number
}

export interface SearchResult {
  id: string
  title: string
  source: string
  category: string
  sentiment: string
  link: string
  score: number
  snippet: string
}

export interface ArticleRecord {
  title: string
  source: string
  sentiment: string
  category: string
  link: string
  published: string
  language?: string
  virality_score?: number
  political_leaning?: string
  clickbait_score?: number
  cluster_label?: string
  [key: string]: unknown
}

export interface SourceCount {
  name: string
  count: number
}

export interface CrossDomainLink {
  source_entity: string
  target_entity: string
  source_sector: string
  target_sector: string
  cooccurrence_count: number
  source_diversity: number
  strength: number
  sentiment_variance: number
  example_articles: string[]
}

export interface ImpactChain {
  chain: string[]
  sectors: string[]
  chain_key: string
  length: number
  cross_domain_hops: number
  total_weight: number
}

export interface CrossDomainData {
  links: CrossDomainLink[]
  chains: ImpactChain[]
  sector_map: Record<string, { entity: string; type: string; sector: string; confidence: number; mention_count: number }>
}

export interface SectorColor {
  [sector: string]: string
}
