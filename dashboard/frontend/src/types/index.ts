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
  verified?: boolean | null
  causal_direction?: string | null
  causal_mechanism?: string | null
  impact_prediction?: string | null
  confidence_label?: string | null
  impact?: {
    predicted_effect: string
    likelihood: number
    timeframe: string
    confidence_weighted: number
  } | null
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

// Phase 3
export interface CausalAnalysisData {
  causal_candidates: CausalCandidate[]
  causal_chains: CausalChain[]
  causal_graph: { nodes: { id: string }[]; edges: any[] }
  summary: {
    total_candidates: number
    total_causal_chains: number
    graph_nodes: number
    graph_edges: number
    avg_causal_score: number
  }
}

export interface CausalCandidate {
  source: string
  target: string
  direction: string
  mean_lag_hours: number
  lag_samples: number
  causal_score: number
  evidence_strength: number
  mechanism: string
}

export interface CausalChain {
  chain: string[]
  length: number
  avg_causal_score: number
  mechanisms: string[]
}

// Phase 4
export interface MultiAgentData {
  analyst: { findings: AgentFinding[]; overall_assessment: string }
  critic: { critiques: Critique[]; confidence_gaps: string[]; overall_quality: string }
  summarizer: { briefing: string; key_developments: string[]; confidence: string; watch_items: string[] }
  generated_at: string
  model: string
}

export interface AgentFinding {
  title: string
  description: string
  significance: string
  entities: string[]
  sectors: string[]
}

export interface Critique {
  finding_index: number
  issue: string
  severity: string
}

export interface TemporalData {
  velocities: EntityVelocity[]
  anomalies: EntityAnomaly[]
  bursts: CitationBurst[]
  phase_transitions: PhaseTransition[]
  summary: {
    total_entities_tracked: number
    total_anomalies: number
    total_bursts: number
    total_phase_transitions: number
    max_velocity: number
    min_velocity: number
  }
}

export interface EntityVelocity {
  entity: string
  total_mentions: number
  unique_days: number
  recent_rate: number
  prior_rate: number
  velocity: number
  acceleration: number
  trend: string
  anomaly_score: number
}

export interface EntityAnomaly extends EntityVelocity {
  z_score: number
  anomaly_type: string
}

export interface CitationBurst {
  entity: string
  date: string
  burst_factor: number
  count: number
  expected: number
}

export interface PhaseTransition {
  entity: string
  current_phase: string
  predicted_phase: string
  confidence: number
  reason: string
  velocity: number
  acceleration: number
}

export interface BriefingData {
  title: string
  type: string
  generated_at: string
  executive_summary: string
  overall_confidence: string
  sector_situations: SectorSituation[]
  key_connections: BriefingConnection[]
  watch_items: WatchItem[]
  predictions: Prediction[]
  statistics: {
    total_links: number
    total_chains: number
    active_sectors: number
    high_confidence_links: number
    llm_verified_links: number
    watch_items_count: number
    predictions_count: number
  }
  analyst_findings: AgentFinding[]
  agent_assessment: string
}

export interface SectorSituation {
  sector: string
  active_entities: number
  cross_domain_links: number
  avg_confidence: number
  high_confidence_links: number
  total_cooccurrences: number
  primary_cross_domain_targets: { sector: string; link_count: number }[]
  status: string
}

export interface BriefingConnection {
  source: string
  target: string
  source_sector: string
  target_sector: string
  confidence: number
  causal_mechanism: string
  impact: string
}

export interface WatchItem {
  type: string
  description: string
  priority: string
}

export interface Prediction {
  entity_pair?: string
  entity?: string
  prediction: string
  likelihood: number
  timeframe: string
  sectors?: string[]
  reason?: string
}

// Phase 5
export interface AlertData {
  alerts: Alert[]
  summary: {
    total_alerts: number
    high_severity: number
    medium_severity: number
    low_severity: number
    alert_types: Record<string, number>
    generated_at: string
  }
}

export interface Alert {
  type: string
  severity: string
  title: string
  description: string
  entities?: string[]
  entity?: string
  sectors?: string[]
  confidence?: number
  acceleration?: number
  velocity?: number
  anomaly_score?: number
  burst_factor?: number
  date?: string
  count?: number
  from_phase?: string
  to_phase?: string
  reason?: string
  timestamp: string
}
