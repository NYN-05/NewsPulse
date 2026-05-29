export interface CrossDomainLink {
  source_entity: string
  target_entity: string
  source_sector: string
  target_sector: string
  cooccurrence_count: number
  strength: number
  source_diversity: number
  sentiment_variance: number
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

export interface BreakingEvent {
  keyword?: string
  entity?: string
  recent_count?: number
  burst_factor?: number
  signal: string
  score: number
}

export interface SearchResult {
  title: string
  source: string
  category?: string
  sentiment: string
  score: number
  snippet?: string
  link?: string
}
