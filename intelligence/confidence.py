"""
Confidence Calibration Engine — Phase 3.

Calibrates intelligence confidence using multiple signals:
- statistical strength, source reliability, temporal density,
- LLM agreement, cross-validation, and sector-specific baselines.
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config.settings import get

logger = logging.getLogger(__name__)

SECTOR_BASELINES = {
    "politics": 0.55, "finance": 0.60, "technology": 0.50,
    "energy": 0.55, "military": 0.50, "startups": 0.45,
    "social": 0.50, "global_events": 0.40,
}

SOURCE_RELIABILITY = {
    "reuters": 0.85, "ap": 0.85, "bbc": 0.80, "bloomberg": 0.80,
    "wsj": 0.80, "ft": 0.80, "cnn": 0.70, "nytimes": 0.75,
    "guardian": 0.70, "washington post": 0.75, "economist": 0.80,
    "al jazeera": 0.65, "npr": 0.75, "dw": 0.70,
}


def calibrate_relationship_confidence(link: Dict, llm_result: Optional[Dict] = None) -> Dict:
    llm_result = llm_result or link.pop("_llm_result", None)
    signals = []

    # 1. Statistical co-occurrence strength
    stat_score = min(link.get("cooccurrence_count", 0) * 0.25 +
                     link.get("source_diversity", 0) * 0.15, 1.0)
    signals.append(("statistical", stat_score, 0.35))

    # 2. Source reliability
    src_rels = []
    for src_key, rel in SOURCE_RELIABILITY.items():
        if src_key in link.get("source_entity", "").lower() or \
           src_key in link.get("target_entity", "").lower():
            src_rels.append(rel)
    source_conf = float(np.mean(src_rels)) if src_rels else 0.5
    signals.append(("source_reliability", source_conf, 0.10))

    # 3. Semantic similarity
    sem_score = link.get("semantic_similarity", 0.0)
    if np.isnan(sem_score):
        sem_score = 0.0
    signals.append(("semantic", min(sem_score * 1.5, 1.0), 0.15))

    # 4. Sector baseline
    src_sec = link.get("source_sector", "global_events")
    tgt_sec = link.get("target_sector", "global_events")
    sector_base = (SECTOR_BASELINES.get(src_sec, 0.5) +
                   SECTOR_BASELINES.get(tgt_sec, 0.5)) / 2.0
    signals.append(("sector_baseline", sector_base, 0.10))

    # 5. LLM verification (if available)
    if llm_result and llm_result.get("verified") is not None:
        llm_conf = llm_result.get("confidence", 0.5)
        llm_weight = 0.20 if llm_result.get("verified") else 0.10
        signals.append(("llm_verification", llm_conf, llm_weight))

    # 6. Causal signal strength
    if link.get("causal_direction") and link.get("causal_mechanism"):
        signals.append(("causal_evidence", 0.75, 0.10))

    # Weighted combination
    total_weight = sum(w for _, _, w in signals)
    if total_weight == 0:
        return 0.5

    confidence = sum(s * w for _, s, w in signals) / total_weight
    confidence = max(0.05, min(0.99, confidence))

    link["confidence"] = round(confidence, 3)
    link["confidence_signals"] = {name: round(score, 3) for name, score, _ in signals}
    link["confidence_label"] = (
        "high" if confidence >= 0.7 else
        "medium" if confidence >= 0.4 else
        "low"
    )
    return link


def calibrate_narrative_confidence(narrative: Dict) -> Dict:
    acceleration = abs(narrative.get("acceleration", 0))
    mention_count = narrative.get("total_mentions", 0) or narrative.get("total_articles", 0)
    recent = narrative.get("recent_7_days", 0)
    phase = narrative.get("phase", "dormant")

    phase_conf = {
        "emerging": 0.3, "accelerating": 0.6, "growing": 0.7,
        "peaked": 0.8, "declining": 0.6, "fading": 0.4,
        "resurging": 0.5, "stable": 0.5, "dormant": 0.2,
    }.get(phase, 0.4)

    vel_conf = min(acceleration * 0.3 + mention_count * 0.05 + recent * 0.1, 1.0)
    confidence = phase_conf * 0.5 + vel_conf * 0.5
    confidence = max(0.1, min(0.98, confidence))

    narrative["confidence"] = round(confidence, 3)
    narrative["confidence_label"] = (
        "high" if confidence >= 0.7 else
        "medium" if confidence >= 0.4 else
        "low"
    )
    return narrative


def calibrate_signal_confidence(signal: Dict) -> Dict:
    score = signal.get("score") or 0
    signal_type = signal.get("type", "general")
    burst = abs(signal.get("burst_factor") or 0)
    recent = signal.get("recent_count") or 0

    type_baseline = {
        "emerging_relationship": 0.3,
        "cross_domain_spillover": 0.5,
        "anomaly": 0.4,
        "narrative_acceleration": 0.6,
    }.get(signal_type, 0.4)

    sig_conf = min(score / 10.0 + burst * 0.2 + recent * 0.03, 1.0)
    confidence = type_baseline * 0.4 + sig_conf * 0.6
    confidence = max(0.1, min(0.98, confidence))

    signal["confidence"] = round(confidence, 3)
    signal["confidence_label"] = (
        "high" if confidence >= 0.7 else
        "medium" if confidence >= 0.4 else
        "low"
    )
    return signal


def calibrate_batch(items: List[Dict], item_type: str = "relationship") -> List[Dict]:
    calibrators = {
        "relationship": calibrate_relationship_confidence,
        "narrative": calibrate_narrative_confidence,
        "signal": calibrate_signal_confidence,
    }
    calibrator = calibrators.get(item_type)
    if not calibrator:
        return items
    return [calibrator(item) for item in items]
