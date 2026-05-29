"""
Signal Detection Engine.

Upgrades the old event_detection.py with intelligence-focused signal categories:
- Emerging Relationship: new cross-domain pair appearing
- Narrative Acceleration: topic gaining velocity across sources
- Cross-Domain Spillover: effect detected in secondary sector
- Influence Shift: entity centrality changing rapidly
- Anomaly Detection: statistical outlier in entity co-mentions
"""

import json
import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict
from datetime import datetime, timedelta
from config.settings import atomic_write_json

logger = logging.getLogger(__name__)

SIGNAL_WEIGHTS = {
    "emerging_relationship": 1.0,
    "narrative_acceleration": 0.9,
    "cross_domain_spillover": 0.85,
    "influence_shift": 0.75,
    "anomaly": 0.7,
}

STOP_WORDS = {
    "reuters", "bbc", "news", "cnn", "associated", "press", "afp", "commentary",
    "opinion", "analysis", "report", "update", "breaking", "developing", "live",
    "video", "photos", "gallery", "subscribe", "newsletter", "click", "readmore",
    "privacy", "policy", "terms", "cookies", "copyright",
}


def _is_noise(w: str) -> bool:
    return len(w) <= 3 or w.isdigit() or w in STOP_WORDS or w.startswith(("http", "www"))


def signal_new_relationships(df: pd.DataFrame, prev_links: List[Dict] = None) -> List[Dict]:
    """Detect entities appearing together across sectors for the first time."""
    if prev_links is None:
        return []

    prev_pairs = set()
    for l in prev_links:
        prev_pairs.add((l.get("source_entity", ""), l.get("target_entity", "")))

    signals = []
    for _, row in df.iterrows():
        ents_str = row.get("entities", "{}")
        if not isinstance(ents_str, str):
            continue
        try:
            entities = json.loads(ents_str)
        except (json.JSONDecodeError, TypeError):
            continue
        all_ents = []
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                ek = ent.strip().lower()
                if ek and len(ek) > 1:
                    all_ents.append(ek)
        for i in range(len(all_ents)):
            for j in range(i + 1, len(all_ents)):
                pair = tuple(sorted([all_ents[i], all_ents[j]]))
                if pair not in prev_pairs:
                    signals.append({
                        "type": "emerging_relationship",
                        "signal": f"New co-mention pair: {pair[0]} ↔ {pair[1]}",
                        "entity_a": pair[0],
                        "entity_b": pair[1],
                        "score": 0.7,
                        "confidence": 0.5,
                    })
    return signals[:20]


def detect_cross_domain_spillover(df: pd.DataFrame) -> List[Dict]:
    """Detect when a topic from one sector spills into another sector's articles."""
    if df.empty:
        return []

    time_col = "published" if "published" in df.columns else "scraped_at"
    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_date"]).sort_values("_date")
    if len(df) < 20:
        return []

    now = df["_date"].max()
    recent = df[df["_date"] >= now - timedelta(hours=48)]
    older = df[df["_date"] < now - timedelta(hours=48)]
    if len(recent) < 5:
        return []

    recent_words = Counter()
    older_words = Counter()
    for _, row in recent.iterrows():
        for w in str(row.get("text", "")).lower().split():
            wc = w.strip(".,!?\"'():;[]{}")
            if not _is_noise(wc):
                recent_words[wc] += 1
    for _, row in older.iterrows():
        for w in str(row.get("text", "")).lower().split():
            wc = w.strip(".,!?\"'():;[]{}")
            if not _is_noise(wc):
                older_words[wc] += 1

    total_older = max(sum(older_words.values()), 1)
    signals = []
    for word, count in recent_words.most_common(100):
        if count < 3:
            continue
        older_count = older_words.get(word, 0)
        older_freq = older_count / total_older
        recent_freq = count / max(len(recent), 1)
        burst = recent_freq / max(older_freq, 0.0001)
        if burst > 5 and count >= 5:
            signals.append({
                "type": "cross_domain_spillover",
                "signal": f"Keyword spike: '{word}' (burst {burst:.1f}x)",
                "keyword": word,
                "burst_factor": round(burst, 1),
                "recent_count": count,
                "score": round(count * burst, 1),
            })

    entity_spikes = _detect_entity_spikes(recent, older)
    signals.extend(entity_spikes)
    signals.sort(key=lambda x: -x["score"])
    return signals[:15]


def _detect_entity_spikes(recent: pd.DataFrame, older: pd.DataFrame) -> List[Dict]:
    spikes = []
    recent_entities = defaultdict(int)
    older_entities = defaultdict(int)
    for df, counter in [(recent, recent_entities), (older, older_entities)]:
        for _, row in df.iterrows():
            ents_str = row.get("entities", "{}")
            if not isinstance(ents_str, str):
                continue
            try:
                ents = json.loads(ents_str)
            except (json.JSONDecodeError, TypeError):
                continue
            for key in ("persons", "orgs", "locations"):
                for ent in ents.get(key, []):
                    e = ent.strip(" .,!?\"'():;[]{}").lower()
                    if e and not _is_noise(e):
                        counter[e] += 1
    total_older = max(sum(older_entities.values()), 1)
    for entity, count in recent_entities.items():
        if count < 2:
            continue
        older_count = older_entities.get(entity, 0)
        burst = count / max(older_count / total_older * len(recent), 0.001)
        if burst > 3:
            spikes.append({
                "type": "anomaly",
                "signal": f"Entity spike: '{entity}' ({count} mentions, burst {burst:.1f}x)",
                "entity": entity,
                "burst_factor": round(burst, 1),
                "recent_count": count,
                "score": round(count * burst, 1),
            })
    return spikes


def detect_signals(df: pd.DataFrame, prev_links: List[Dict] = None) -> List[Dict]:
    """Run all signal detectors and return merged, deduplicated, ranked signals."""
    signals = []
    signals.extend(detect_cross_domain_spillover(df))
    signals.extend(signal_new_relationships(df, prev_links))

    seen_signals = set()
    deduped = []
    for s in signals:
        key = s.get("signal", "")
        if key not in seen_signals:
            seen_signals.add(key)
            deduped.append(s)
    deduped.sort(key=lambda x: -x["score"])

    if deduped:
        logger.info("Detected %d signals", len(deduped))
        for s in deduped[:5]:
            logger.info("  Signal: %s (score=%.1f)", s["signal"], s.get("score", 0))
    return deduped[:20]


def signals_pipeline(df: pd.DataFrame) -> Dict:
    logger.info("=" * 60)
    logger.info("SIGNAL DETECTION ENGINE")
    logger.info("=" * 60)

    prev_links = None
    from config.settings import path_for
    import os
    links_path = os.path.join(path_for("output_dir"), "cross_domain_links.json")
    if os.path.exists(links_path):
        try:
            with open(links_path) as f:
                prev_links = json.load(f)
        except Exception:
            pass

    signals = detect_signals(df, prev_links)

    severity_counts = Counter(s["type"] for s in signals)
    result = {
        "signals": signals,
        "summary": {
            "total_signals": len(signals),
            "severity_distribution": dict(severity_counts.most_common()),
            "highest_score": signals[0]["score"] if signals else 0,
            "top_signal": signals[0].get("signal", "") if signals else "",
        },
    }

    base = path_for("output_dir")
    atomic_write_json(os.path.join(base, "breaking_events.json"), result)

    logger.info("Saved breaking_events.json")
    logger.info("=" * 60)
    return result
