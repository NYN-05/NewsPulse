"""
Intelligence Explanation Engine — Phase 3 (upgraded).

Generates human-readable, evidence-based explanations with confidence calibration:
- Why are two entities connected? (with calibrated confidence)
- What evidence supports this connection?
- What is the impact across domains?
- What downstream effects should be monitored?
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from intelligence.confidence import calibrate_relationship_confidence

logger = logging.getLogger(__name__)


def explain_relationship(
    source_entity: str,
    target_entity: str,
    source_sector: str,
    target_sector: str,
    cooccurrence_count: int,
    source_diversity: int,
    strength: float,
    example_articles: List[str] = None,
    confidence: float = None,
    causal_direction: str = None,
    causal_mechanism: str = None,
    impact_prediction: str = None,
) -> Dict:
    impact_level = _assess_impact(strength, cooccurrence_count, source_diversity)
    downstream = _suggest_downstream_effects(source_sector, target_sector)

    explanation = {
        "summary": (
            f"{source_entity} ({source_sector}) and {target_entity} ({target_sector}) "
            f"exhibit a cross-domain intelligence relationship. "
            f"They co-occur in {cooccurrence_count} articles across {source_diversity} distinct sources, "
            f"indicating a {impact_level['label'].lower()} connection that spans {source_sector} and {target_sector} sectors."
        ),
        "why_connected": _generate_why_explanation(source_entity, target_entity, source_sector, target_sector),
        "evidence": {
            "cooccurrence_count": cooccurrence_count,
            "source_diversity": source_diversity,
            "relationship_strength": round(strength, 2),
            "confidence": round(confidence, 3) if confidence else None,
            "example_articles": (example_articles or [])[:3],
        },
        "impact_assessment": impact_level,
        "downstream_effects": downstream,
        "domains_involved": [source_sector, target_sector],
    }

    if causal_direction:
        explanation["causal"] = {
            "direction": causal_direction,
            "mechanism": causal_mechanism or "",
        }
    if impact_prediction:
        explanation["impact_prediction"] = impact_prediction

    calibrated = calibrate_relationship_confidence({
        "source_entity": source_entity,
        "target_entity": target_entity,
        "source_sector": source_sector,
        "target_sector": target_sector,
        "cooccurrence_count": cooccurrence_count,
        "source_diversity": source_diversity,
        "semantic_similarity": 0.0,
        "confidence": confidence or 0.5,
    })
    explanation["calibrated_confidence"] = calibrated.get("confidence", confidence or 0.5)
    explanation["confidence_label"] = calibrated.get("confidence_label", "medium")
    explanation["confidence_signals"] = calibrated.get("confidence_signals", {})

    return explanation


def _assess_impact(strength: float, cooccurrence: int, diversity: int) -> Dict:
    score = min(strength * 10 + cooccurrence * 0.5 + diversity * 2, 100)
    if score >= 70:
        return {"label": "High", "score": round(score, 1), "description": "Significant cross-domain relationship with strong evidence"}
    elif score >= 40:
        return {"label": "Medium", "score": round(score, 1), "description": "Notable cross-domain relationship with moderate evidence"}
    return {"label": "Low", "score": round(score, 1), "description": "Emerging cross-domain relationship with limited evidence"}


def _generate_why_explanation(src: str, tgt: str, src_sec: str, tgt_sec: str) -> str:
    templates = {
        ("politics", "finance"): f"Political decisions involving {src} create direct fiscal and market consequences for {tgt}.",
        ("politics", "technology"): f"Regulatory and policy actions ({src}) shape the technology landscape ({tgt}) through legislation and funding.",
        ("politics", "energy"): f"Government policy ({src}) directly impacts energy markets, extraction rights, and climate targets ({tgt}).",
        ("politics", "military"): f"Political leadership and diplomacy ({src}) drive military posture and defense strategy ({tgt}).",
        ("finance", "technology"): f"Capital markets and investment flows ({src}) fund or constrain technology development ({tgt}).",
        ("finance", "energy"): f"Energy prices ({tgt}) directly affect inflation, trade balances, and market stability ({src}).",
        ("technology", "energy"): f"Technology sector ({src}) drives energy demand, grid modernization, and renewable innovation ({tgt}).",
        ("technology", "military"): f"Technology capabilities ({src}) directly enable military advantage in cyber, AI, and autonomous systems ({tgt}).",
        ("energy", "military"): f"Energy security ({src}) is a strategic military concern; conflicts often center on energy resources ({tgt}).",
        ("technology", "startups"): f"Technology infrastructure and platforms ({src}) create the foundation for startup innovation and funding ({tgt}).",
        ("finance", "startups"): f"Investment capital and market conditions ({src}) directly determine startup viability and growth ({tgt}).",
        ("social", "politics"): f"Social movements and public opinion ({src}) drive political agenda-setting and policy change ({tgt}).",
    }
    if (src_sec, tgt_sec) in templates:
        return templates[(src_sec, tgt_sec)]
    if (tgt_sec, src_sec) in templates:
        return templates[(tgt_sec, src_sec)]
    return (
        f"Entities in {src_sec} and {tgt_sec} are connected through shared dependencies. "
        f"Changes in {src_sec} create measurable effects in {tgt_sec} through cross-domain propagation channels."
    )


def _suggest_downstream_effects(src_sector: str, tgt_sector: str) -> List[str]:
    effects = {
        ("politics", "finance"): ["Market volatility index changes", "Currency fluctuation risk", "Sector-specific regulatory impact"],
        ("politics", "technology"): ["Regulatory compliance costs shift", "R&D investment reallocation", "International tech competition dynamics"],
        ("technology", "energy"): ["Energy grid modernization acceleration", "EV adoption rate changes", "Data center energy demand shift"],
        ("finance", "technology"): ["Venture capital reallocation", "IPO market activity shift", "Tech sector valuation adjustments"],
        ("energy", "military"): ["Supply chain security adjustments", "Strategic resource allocation", "Alliance realignment"],
        ("social", "politics"): ["Policy priority shifts", "Election outcome influence", "Regulatory timeline acceleration"],
    }
    if (src_sector, tgt_sector) in effects:
        return effects[(src_sector, tgt_sector)]
    if (tgt_sector, src_sector) in effects:
        return effects[(tgt_sector, src_sector)]
    return [
        f"Cross-domain propagation between {src_sector} and {tgt_sector}",
        "Secondary effects in connected sectors",
        "Potential narrative amplification across sources",
    ]


def explain_narrative_shift(entity: str, phase: str, acceleration: float, total_mentions: int) -> str:
    phase_descriptions = {
        "emerging": f"'{entity}' has recently appeared in coverage and is gaining initial traction.",
        "accelerating": f"'{entity}' is rapidly gaining momentum — mention velocity is increasing significantly.",
        "growing": f"'{entity}' shows steady growth in coverage across multiple sources.",
        "peaked": f"'{entity}' has reached maximum coverage intensity and may begin to decline.",
        "declining": f"'{entity}' is receiving decreasing attention across sources.",
        "fading": f"'{entity}' is rapidly disappearing from coverage.",
        "resurging": f"'{entity}' shows renewed interest after a period of decline.",
        "stable": f"'{entity}' maintains consistent coverage levels.",
        "dormant": f"'{entity}' has minimal current activity.",
    }
    return phase_descriptions.get(phase, f"'{entity}' is in {phase} phase ({acceleration:.0f} acceleration, {total_mentions} total mentions).")


def explain_signal(signal_type: str, signal_text: str, score: float) -> str:
    if signal_type == "emerging_relationship":
        return f"NEW CONNECTION DETECTED: {signal_text}. This previously unknown cross-domain relationship may indicate an emerging intelligence pattern."
    elif signal_type == "cross_domain_spillover":
        return f"CROSS-DOMAIN SPILLOVER: {signal_text}. A development in one sector is now manifesting in another."
    elif signal_type == "anomaly":
        return f"ANOMALY DETECTED: {signal_text}. This entity is appearing at rates significantly above normal."
    return signal_text
