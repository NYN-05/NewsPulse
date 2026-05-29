"""
Intelligence Alert Engine — Phase 5.

Configurable alert triggers that fire when specific intelligence conditions are met:
- High-confidence cross-domain relationship discovered
- Anomalous entity velocity spike
- Narrative phase transition
- Burst detection threshold breached
- Sector activity level change
"""

import json
import logging
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from config.settings import get, atomic_read_json

logger = logging.getLogger(__name__)


def eval_relationship_alerts(links: List[Dict], previous_links: List[Dict]) -> List[Dict]:
    alerts = []
    prev_entity_pairs = set()
    for pl in previous_links:
        prev_entity_pairs.add((pl["source_entity"], pl["target_entity"]))

    for link in links:
        pair = (link["source_entity"], link["target_entity"])
        is_new = pair not in prev_entity_pairs

        if link.get("confidence", 0) >= 0.8 and is_new:
            alerts.append({
                "type": "high_confidence_relationship",
                "severity": "high",
                "title": f"High-confidence relationship: {link['source_entity']} <-> {link['target_entity']}",
                "description": (
                    f"New cross-domain relationship ({link['source_sector']}-{link['target_sector']}) "
                    f"with confidence {link['confidence']:.2f}"
                ),
                "entities": [link["source_entity"], link["target_entity"]],
                "sectors": [link["source_sector"], link["target_sector"]],
                "confidence": link["confidence"],
                "timestamp": datetime.now().isoformat(),
            })

        if link.get("confidence", 0) >= 0.7 and link.get("verified") and is_new:
            alerts.append({
                "type": "verified_relationship",
                "severity": "medium",
                "title": f"LLM-verified: {link['source_entity']} <-> {link['target_entity']}",
                "description": link.get("explanation", "LLM verified cross-domain relationship"),
                "entities": [link["source_entity"], link["target_entity"]],
                "sectors": [link["source_sector"], link["target_sector"]],
                "confidence": link["confidence"],
                "timestamp": datetime.now().isoformat(),
            })

    return alerts


def eval_velocity_alerts(velocities: List[Dict], thresholds: Dict = None) -> List[Dict]:
    alerts = []
    thresholds = thresholds or {"acceleration": 3.0, "velocity": 2.0}

    for v in velocities:
        accel = abs(v.get("acceleration", 0))
        vel = abs(v.get("velocity", 0))

        if accel > thresholds["acceleration"] and vel > thresholds["velocity"]:
            alerts.append({
                "type": "velocity_spike",
                "severity": "high",
                "title": f"Velocity spike: {v['entity']}",
                "description": (
                    f"Entity '{v['entity']}' showing {v['trend']} trend "
                    f"(acceleration={v.get('acceleration', 0):.1f}, "
                    f"velocity={v.get('velocity', 0):.1f})"
                ),
                "entity": v["entity"],
                "acceleration": v.get("acceleration", 0),
                "velocity": v.get("velocity", 0),
                "anomaly_score": v.get("anomaly_score", 0),
                "timestamp": datetime.now().isoformat(),
            })

    return alerts


def eval_burst_alerts(bursts: List[Dict], threshold: float = 3.0) -> List[Dict]:
    alerts = []
    for b in bursts:
        if b.get("burst_factor", 0) >= threshold:
            alerts.append({
                "type": "citation_burst",
                "severity": "high",
                "title": f"Citation burst: {b['entity']}",
                "description": (
                    f"'{b['entity']}' appearing {b['burst_factor']:.1f}x expected rate "
                    f"({b.get('count', 0)} occurrences on {b.get('date', '?')})"
                ),
                "entity": b["entity"],
                "burst_factor": b["burst_factor"],
                "date": b.get("date", ""),
                "count": b.get("count", 0),
                "timestamp": datetime.now().isoformat(),
            })
    return alerts


def eval_phase_alerts(transitions: List[Dict]) -> List[Dict]:
    alerts = []
    for t in transitions:
        if t.get("confidence", 0) >= 0.7:
            alerts.append({
                "type": "phase_transition",
                "severity": "medium",
                "title": f"Phase transition: {t['entity']}",
                "description": f"{t['entity']}: {t['current_phase']} -> {t['predicted_phase']}",
                "entity": t["entity"],
                "from_phase": t["current_phase"],
                "to_phase": t["predicted_phase"],
                "confidence": t["confidence"],
                "reason": t.get("reason", ""),
                "timestamp": datetime.now().isoformat(),
            })
    return alerts


def alerting_pipeline(
    links: List[Dict],
    velocities: List[Dict],
    bursts: List[Dict],
    transitions: List[Dict],
) -> Dict:
    logger.info("=" * 60)
    logger.info("PHASE 5 — INTELLIGENCE ALERT ENGINE")
    logger.info("=" * 60)

    import os
    links_path = os.path.join(path_for("output_dir"), "cross_domain_links.json")
    previous_links = atomic_read_json(links_path)
    if not isinstance(previous_links, list):
        previous_links = []

    alerts = []
    alerts.extend(eval_relationship_alerts(links, previous_links))
    alerts.extend(eval_velocity_alerts(velocities))
    alerts.extend(eval_burst_alerts(bursts))
    alerts.extend(eval_phase_alerts(transitions))

    alerts.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["severity"], 3))

    severity_counts = defaultdict(int)
    type_counts = defaultdict(int)
    for a in alerts:
        severity_counts[a["severity"]] += 1
        type_counts[a["type"]] += 1

    result = {
        "alerts": alerts,
        "summary": {
            "total_alerts": len(alerts),
            "high_severity": severity_counts.get("high", 0),
            "medium_severity": severity_counts.get("medium", 0),
            "low_severity": severity_counts.get("low", 0),
            "alert_types": dict(type_counts),
            "generated_at": datetime.now().isoformat(),
        },
    }

    return result
