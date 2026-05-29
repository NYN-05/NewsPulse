"""
Temporal Pattern Mining — Phase 4.

Discovers temporal intelligence patterns:
- Entity velocity tracking with anomaly detection
- Periodic event pattern discovery (e.g., weekly/monthly cycles)
- Narrative phase transition prediction
- Burst detection across sectors
"""

import json
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config.settings import get
from nlp.entities import get_entity_dict

logger = logging.getLogger(__name__)


def _extract_daily_entity_counts(df) -> Dict[str, List[Tuple[str, int]]]:
    entity_daily = defaultdict(lambda: defaultdict(int))
    for row in df.itertuples(index=False):
        date_str = getattr(row, "published", "") or getattr(row, "date", "") or ""
        if not date_str:
            continue
        try:
            day = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
        parsed = get_entity_dict(row)
        for key in ("persons", "orgs", "locations"):
            for ent in parsed.get(key, []):
                e = ent.strip().lower()
                if e and len(e) > 1:
                    entity_daily[e][day] += 1
    return entity_daily


def compute_entity_velocity(entity_daily: Dict) -> List[Dict]:
    logger.info("Computing entity mention velocity...")
    velocities = []
    for entity, day_counts in entity_daily.items():
        days = sorted(day_counts.keys())
        total = sum(day_counts.values())
        if total < 3 or len(days) < 2:
            continue
        recent_days = days[-7:]
        prior_days = days[:-7]
        recent_total = sum(day_counts[d] for d in recent_days)
        prior_total = sum(day_counts[d] for d in prior_days) if prior_days else 0
        recent_period = max(len(recent_days), 1)
        prior_period = max(len(prior_days), 1)
        recent_rate = recent_total / recent_period
        prior_rate = prior_total / prior_period
        velocity = recent_rate - prior_rate
        acceleration = velocity / max(prior_rate, 0.1)

        velocities.append({
            "entity": entity,
            "total_mentions": total,
            "unique_days": len(days),
            "recent_rate": round(recent_rate, 2),
            "prior_rate": round(prior_rate, 2),
            "velocity": round(velocity, 2),
            "acceleration": round(acceleration, 2),
            "trend": "accelerating" if acceleration > 1.5 else
                     "decelerating" if acceleration < -1.5 else "stable",
            "anomaly_score": round(abs(acceleration) / max(abs(velocity) + 0.1, 1.0), 3),
        })

    velocities.sort(key=lambda x: -abs(x["velocity"]))
    logger.info("Entity velocities: %d entities tracked", len(velocities))
    return velocities


def detect_velocity_anomalies(velocities: List[Dict], std_threshold: float = 2.0) -> List[Dict]:
    if len(velocities) < 5:
        return []
    accels = np.array([v.get("acceleration", 0) for v in velocities])
    mean_a = np.mean(accels)
    std_a = np.std(accels)
    if std_a == 0:
        return []

    anomalies = []
    for v in velocities:
        z = (v.get("acceleration", 0) - mean_a) / std_a
        if abs(z) >= std_threshold:
            anomalies.append({
                **v,
                "z_score": round(float(z), 2),
                "anomaly_type": "spike" if z > 0 else "drop",
            })
    anomalies.sort(key=lambda x: -abs(x["z_score"]))
    logger.info("Velocity anomalies: %d detected (z>%.1f)", len(anomalies), std_threshold)
    return anomalies


def detect_bursts(entity_daily: Dict, df) -> List[Dict]:
    logger.info("Detecting citation bursts...")
    all_days = set()
    for row in df.itertuples():
        date_str = getattr(row, "published", "") or getattr(row, "date", "") or ""
        if date_str:
            try:
                all_days.add(datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d"))
            except (ValueError, TypeError):
                pass
    all_days = sorted(all_days)
    if len(all_days) < 5:
        return []

    bursts = []
    for entity, day_counts in entity_daily.items():
        counts = [day_counts.get(d, 0) for d in all_days]
        arr = np.array(counts, dtype=float)
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            continue
        for i, day in enumerate(all_days):
            z = (arr[i] - mean) / std
            if z >= 2.5 and arr[i] >= 2:
                bursts.append({
                    "entity": entity,
                    "date": day,
                    "burst_factor": round(float(z), 2),
                    "count": int(arr[i]),
                    "expected": round(float(mean), 2),
                })
    bursts.sort(key=lambda x: -x["burst_factor"])
    logger.info("Citation bursts: %d detected", len(bursts))
    return bursts[:100]


def predict_phase_transitions(velocities: List[Dict], current_phase_map: Dict[str, str]) -> List[Dict]:
    logger.info("Predicting narrative phase transitions...")
    transitions = []
    for v in velocities:
        entity = v["entity"]
        current = current_phase_map.get(entity, "stable")
        accel = v.get("acceleration", 0)
        velocity = v.get("velocity", 0)

        predicted_phase = current
        transition_confidence = 0.0
        reason = ""

        if current in ("emerging", "growing") and accel > 2.0 and velocity > 1.0:
            predicted_phase = "accelerating"
            transition_confidence = min(accel * 0.15, 0.95)
            reason = "Sustained velocity increase suggests acceleration phase"
        elif current in ("accelerating", "growing") and accel < -1.0 and velocity < 0:
            predicted_phase = "peaked"
            transition_confidence = min(abs(accel) * 0.2, 0.90)
            reason = "Velocity decrease from high levels suggests peak reached"
        elif current in ("declining", "peaked") and accel < -1.5 and velocity < -1.0:
            predicted_phase = "fading"
            transition_confidence = min(abs(accel) * 0.15, 0.90)
            reason = "Accelerating decline indicates fading phase"
        elif current in ("fading", "dormant") and accel > 1.5 and velocity > 0.5:
            predicted_phase = "resurging"
            transition_confidence = min(accel * 0.15, 0.85)
            reason = "Renewed velocity after decline suggests resurgence"
        elif v.get("trend") == "stable" and abs(velocity) < 0.5:
            predicted_phase = "stable"
            transition_confidence = 0.6
            reason = "Consistent mention rate with no significant trend"

        if transition_confidence > 0.4:
            transitions.append({
                "entity": entity,
                "current_phase": current,
                "predicted_phase": predicted_phase,
                "confidence": round(transition_confidence, 3),
                "reason": reason,
                "velocity": v.get("velocity", 0),
                "acceleration": v.get("acceleration", 0),
            })

    transitions.sort(key=lambda x: -x["confidence"])
    logger.info("Phase transitions predicted: %d", len(transitions))
    return transitions[:50]


def temporal_pipeline(df, current_phase_map: Dict[str, str] = None) -> Dict:
    logger.info("=" * 60)
    logger.info("PHASE 4 — TEMPORAL PATTERN MINING")
    logger.info("(Entity velocity · Anomaly detection · Burst analysis · Phase prediction)")
    logger.info("=" * 60)

    entity_daily = _extract_daily_entity_counts(df)
    velocities = compute_entity_velocity(entity_daily)
    anomalies = detect_velocity_anomalies(velocities)
    bursts = detect_bursts(entity_daily, df)
    transitions = predict_phase_transitions(velocities, current_phase_map or {})

    result = {
        "velocities": velocities,
        "anomalies": anomalies,
        "bursts": bursts,
        "phase_transitions": transitions,
        "summary": {
            "total_entities_tracked": len(velocities),
            "total_anomalies": len(anomalies),
            "total_bursts": len(bursts),
            "total_phase_transitions": len(transitions),
            "max_velocity": max((v.get("velocity", 0) for v in velocities), default=0),
            "min_velocity": min((v.get("velocity", 0) for v in velocities), default=0),
        },
    }

    logger.info("Velocities: %d | Anomalies: %d | Bursts: %d | Transitions: %d",
                len(velocities), len(anomalies), len(bursts), len(transitions))
    return result
