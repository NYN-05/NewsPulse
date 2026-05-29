export interface CrossDomainLink {
  source_entity: string
  target_entity: string
  source_sector: string
  target_sector: string
  cooccurrence_count: number
  strength: number
  source_diversity: number
  semantic_similarity?: number
  explanation?: string | null
  confidence?: number | null
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
  sector_map: Record<string, string>
}

export interface Signal {
  type: string
  signal: string
  entity?: string
  keyword?: string
  burst_factor?: number
  recent_count?: number
  score: number
  confidence?: number
}

export interface SignalsData {
  signals: Signal[]
  summary: {
    total_signals: number
    highest_score: number
    top_signal: string
    severity_distribution: Record<string, number>
  }
}

export interface SearchResult {
  title: string
  source: string
  category?: string
  sentiment: string
  score: number
  snippet?: string
  link?: string
  published?: string
}

export interface Narrative {
  entity?: string
  cluster?: number
  phase: string
  acceleration: number
  total_mentions?: number
  total_articles?: number
  recent_7_days: number
  first_seen: string
  last_seen: string
  trajectory: { date: string; count: number }[]
  top_keywords?: string[]
}

export interface PipelineStatus {
  status: string
  last_run_at: string | null
  last_run_duration: number | null
  last_run_success: boolean | null
  last_error: string | null
  next_run_at: string | null
  run_count: number
  articles_analyzed: number
}

export interface NarrativeData {
  mutations: any[]
  entity_narratives: Narrative[]
  cluster_narratives: Narrative[]
  emerging_topics: any[]
  disappearing_topics: any[]
  summary: {
    total_entity_narratives: number
    total_cluster_narratives: number
    total_mutations: number
    emerging_count: number
    disappearing_count: number
  }
}
