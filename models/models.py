from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ImpactPrediction(BaseModel):
    predicted_effect: str
    likelihood: float = Field(ge=0.0, le=1.0)
    timeframe: str = Field(pattern=r"^(short|medium|long)$")
    confidence_weighted: float


class SectorInfo(BaseModel):
    entity: str
    type: str
    sector: str
    confidence: float
    mention_count: int


class CrossDomainLink(BaseModel):
    source_entity: str
    target_entity: str
    source_sector: str
    target_sector: str
    cooccurrence_count: int
    source_diversity: int
    strength: float
    semantic_similarity: float
    explanation: Optional[str] = None
    confidence: Optional[float] = None
    verified: Optional[bool] = None
    causal_direction: Optional[str] = None
    causal_mechanism: Optional[str] = None
    impact_prediction: Optional[str] = None
    impact: Optional[ImpactPrediction] = None
    confidence_label: Optional[str] = None


class CrossDomainSummary(BaseModel):
    total_entities_mapped: int = 0
    sector_distribution: Dict[str, int] = {}
    total_cross_domain_links: int = 0
    total_impact_chains: int = 0
    confidence_distribution: Dict[str, int] = {}
    llm_verified: int = 0
    causal_explanations: int = 0
    avg_confidence: float = 0.0


class ImpactChain(BaseModel):
    chain: List[str]
    sectors: List[str]
    chain_key: str
    length: int
    cross_domain_hops: int
    total_weight: int


class CrossDomainResult(BaseModel):
    sector_map: Dict[str, SectorInfo] = {}
    cross_domain_links: List[CrossDomainLink] = []
    impact_chains: List[ImpactChain] = []
    summary: CrossDomainSummary = Field(default_factory=CrossDomainSummary)


class NarrativeMutation(BaseModel):
    window: str
    prev_window: str
    curr_window: str
    prev_articles: int
    curr_articles: int
    retained_keywords: int
    emerged_keywords: List[str] = []
    disappeared_keywords: List[str] = []
    keyword_retention_pct: float = 0.0
    drift_score: float = 0.0
    article_growth_pct: float = 0.0


class TrajectoryPoint(BaseModel):
    date: str
    count: int


class EntityNarrative(BaseModel):
    entity: str
    phase: str
    acceleration: int = 0
    total_mentions: int = 0
    recent_7_days: int = 0
    first_seen: str = ""
    last_seen: str = ""
    trajectory: List[TrajectoryPoint] = []


class ClusterNarrative(BaseModel):
    cluster: int
    phase: str
    acceleration: int = 0
    total_articles: int = 0
    recent_7_days: int = 0
    first_seen: str = ""
    last_seen: str = ""
    trajectory: List[TrajectoryPoint] = []
    top_keywords: List[str] = []


class EmergingTopic(BaseModel):
    type: str = Field(pattern=r"^(entity|cluster)$")
    name: str
    phase: str
    acceleration: int = 0
    total_mentions: int = 0
    recent_7_days: int = 0
    first_seen: str = ""
    keywords: List[str] = []


class DisappearingTopic(BaseModel):
    type: str = Field(pattern=r"^(entity|cluster)$")
    name: str
    phase: str
    acceleration: int = 0
    total_mentions: int = 0
    last_seen: str = ""
    keywords: List[str] = []


class NarrativeSummary(BaseModel):
    total_entity_narratives: int = 0
    total_cluster_narratives: int = 0
    total_mutations: int = 0
    phase_distribution: Dict[str, int] = {}
    emerging_count: int = 0
    disappearing_count: int = 0


class NarrativeResult(BaseModel):
    mutations: List[NarrativeMutation] = []
    entity_narratives: List[EntityNarrative] = []
    cluster_narratives: List[ClusterNarrative] = []
    emerging_topics: List[EmergingTopic] = []
    disappearing_topics: List[DisappearingTopic] = []
    summary: NarrativeSummary = Field(default_factory=NarrativeSummary)


class Signal(BaseModel):
    type: str
    signal: str
    entity: Optional[str] = None
    entity_a: Optional[str] = None
    entity_b: Optional[str] = None
    keyword: Optional[str] = None
    burst_factor: Optional[float] = None
    recent_count: Optional[int] = None
    score: float = 0.0
    confidence: Optional[float] = None


class SignalSummary(BaseModel):
    total_signals: int = 0
    severity_distribution: Dict[str, int] = {}
    highest_score: float = 0.0
    top_signal: str = ""


class SignalResult(BaseModel):
    signals: List[Signal] = []
    summary: SignalSummary = Field(default_factory=SignalSummary)


class CausalCandidate(BaseModel):
    source: str
    target: str
    direction: str
    mean_lag_hours: float
    lag_samples: int = 0
    causal_score: float = 0.0
    evidence_strength: int = 0
    mechanism: str = "temporal_precedence"


class CausalChain(BaseModel):
    chain: List[str]
    length: int = 0
    avg_causal_score: float = 0.0
    mechanisms: List[str] = []


class CausalGraphNode(BaseModel):
    id: str


class CausalGraphEdge(BaseModel):
    source: str
    target: str
    weight: float = 0.0
    mechanism: str = ""
    pattern: str = ""
    mean_lag_hours: float = 0.0


class CausalGraph(BaseModel):
    nodes: List[CausalGraphNode] = []
    edges: List[CausalGraphEdge] = []


class CausalSummary(BaseModel):
    total_candidates: int = 0
    total_causal_chains: int = 0
    graph_nodes: int = 0
    graph_edges: int = 0
    avg_causal_score: float = 0.0


class CausalResult(BaseModel):
    causal_candidates: List[CausalCandidate] = []
    causal_chains: List[CausalChain] = []
    causal_graph: CausalGraph = Field(default_factory=CausalGraph)
    summary: CausalSummary = Field(default_factory=CausalSummary)


class TemporalVelocity(BaseModel):
    entity: str
    total_mentions: int = 0
    unique_days: int = 0
    recent_rate: float = 0.0
    prior_rate: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0
    trend: str = "stable"
    anomaly_score: float = 0.0


class TemporalAnomaly(TemporalVelocity):
    z_score: float = 0.0
    anomaly_type: str = ""


class TemporalBurst(BaseModel):
    entity: str
    date: str
    burst_factor: float = 0.0
    count: int = 0
    expected: float = 0.0


class PhaseTransition(BaseModel):
    entity: str
    current_phase: str
    predicted_phase: str
    confidence: float = 0.0
    reason: str = ""
    velocity: float = 0.0
    acceleration: float = 0.0


class TemporalSummary(BaseModel):
    total_entities_tracked: int = 0
    total_anomalies: int = 0
    total_bursts: int = 0
    total_phase_transitions: int = 0
    max_velocity: float = 0.0
    min_velocity: float = 0.0


class TemporalResult(BaseModel):
    velocities: List[TemporalVelocity] = []
    anomalies: List[TemporalAnomaly] = []
    bursts: List[TemporalBurst] = []
    phase_transitions: List[PhaseTransition] = []
    summary: TemporalSummary = Field(default_factory=TemporalSummary)


class Alert(BaseModel):
    type: str
    severity: str = Field(pattern=r"^(high|medium|low)$")
    title: str
    description: str
    entities: List[str] = []
    sectors: List[str] = []
    entity: Optional[str] = None
    from_phase: Optional[str] = None
    to_phase: Optional[str] = None
    confidence: Optional[float] = None
    burst_factor: Optional[float] = None
    acceleration: Optional[float] = None
    velocity: Optional[float] = None
    anomaly_score: Optional[float] = None
    date: Optional[str] = None
    count: Optional[int] = None
    reason: Optional[str] = None
    timestamp: str = ""


class AlertSummary(BaseModel):
    total_alerts: int = 0
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0
    alert_types: Dict[str, int] = {}
    generated_at: str = ""


class AlertResult(BaseModel):
    alerts: List[Alert] = []
    summary: AlertSummary = Field(default_factory=AlertSummary)


class AgentFinding(BaseModel):
    title: str = ""
    description: str = ""
    significance: str = "medium"
    entities: List[str] = []
    sectors: List[str] = []


class AgentCritique(BaseModel):
    finding_index: int = 0
    issue: str = ""
    severity: str = "low"


class MultiAgentResult(BaseModel):
    analyst: Dict = Field(default_factory=lambda: {"findings": [], "overall_assessment": ""})
    critic: Dict = Field(default_factory=lambda: {"critiques": [], "confidence_gaps": [], "overall_quality": ""})
    summarizer: Dict = Field(default_factory=lambda: {"briefing": "", "key_developments": [], "confidence": "", "watch_items": []})
    generated_at: str = ""
    model: str = "qwen3:14b"


class SectorSituation(BaseModel):
    sector: str
    active_entities: int = 0
    cross_domain_links: int = 0
    avg_confidence: float = 0.0
    high_confidence_links: int = 0
    total_cooccurrences: int = 0
    primary_cross_domain_targets: List[Dict] = []
    status: str = "stable"


class KeyConnection(BaseModel):
    source: str
    target: str
    source_sector: str
    target_sector: str
    confidence: float = 0.0
    causal_mechanism: str = ""
    impact: str = ""


class WatchItem(BaseModel):
    type: str
    description: str
    priority: str = "medium"


class Prediction(BaseModel):
    entity_pair: Optional[str] = None
    entity: Optional[str] = None
    prediction: str = ""
    likelihood: float = 0.0
    timeframe: str = ""
    sectors: List[str] = []
    reason: Optional[str] = None


class BriefingStatistics(BaseModel):
    total_links: int = 0
    total_chains: int = 0
    active_sectors: int = 0
    high_confidence_links: int = 0
    llm_verified_links: int = 0
    watch_items_count: int = 0
    predictions_count: int = 0


class BriefingResult(BaseModel):
    title: str = ""
    type: str = "standard"
    generated_at: str = ""
    executive_summary: str = ""
    overall_confidence: str = "medium"
    sector_situations: List[SectorSituation] = []
    key_connections: List[KeyConnection] = []
    watch_items: List[WatchItem] = []
    predictions: List[Prediction] = []
    statistics: BriefingStatistics = Field(default_factory=BriefingStatistics)
    analyst_findings: List[Dict] = []
    agent_assessment: str = ""
