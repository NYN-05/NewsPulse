import json
import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


BREAKING_STOP_WORDS = {
    "reuters", "bbc", "news", "cnn", "apnews", "aljazeera", "associated",
    "press", "wires", "afp", "dpa", "upi", "itartass", "xinhua", "kyodo",
    "commentary", "opinion", "analysis", "report", "update", "breaking",
    "developing", "justin", "live", "video", "photos", "gallery", "explainer",
    "summary", "recap", "watch", "listen", "subscribe", "newsletter",
    "click", "readmore", "read", "story", "articles", "article", "page",
    "home", "menu", "search", "login", "signup", "register", "email",
    "please", "privacy", "policy", "terms", "cookies", "copyright",
    "2024", "2025", "2026", "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "january", "february", "march", "april",
    "june", "july", "august", "september", "october", "november", "december",
    "http", "https", "www", "com", "org", "net", "html", "index", "php",
}

def _is_noise_keyword(word: str) -> bool:
    if len(word) <= 3:
        return True
    if word.isdigit():
        return True
    if word in BREAKING_STOP_WORDS:
        return True
    if word.startswith("http") or word.startswith("www"):
        return True
    return False


def detect_breaking_events(df: pd.DataFrame) -> List[Dict]:
    if df.empty:
        return []

    time_col = "published" if "published" in df.columns and df["published"].notna().sum() > 0 else "scraped_at"
    df = df.copy()
    df["_ts"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_ts"]).sort_values("_ts")

    if len(df) < 20:
        return []

    now = df["_ts"].max()
    recent_cutoff = now - timedelta(hours=24)
    recent = df[df["_ts"] >= recent_cutoff]
    older = df[df["_ts"] < recent_cutoff]

    if len(recent) < 5:
        return []

    recent_words = Counter()
    older_words = Counter()

    for _, row in recent.iterrows():
        text = str(row.get("text", "") or "")
        for w in text.lower().split():
            wc = w.strip(".,!?\"'():;[]{}")
            if not _is_noise_keyword(wc):
                recent_words[wc] += 1

    for _, row in older.iterrows():
        text = str(row.get("text", "") or "")
        for w in text.lower().split():
            wc = w.strip(".,!?\"'():;[]{}")
            if not _is_noise_keyword(wc):
                older_words[wc] += 1

    total_older = max(sum(older_words.values()), 1)

    events = []
    for word, count in recent_words.most_common(100):
        if count < 3:
            continue
        older_count = older_words.get(word, 0)
        older_freq = older_count / total_older
        recent_freq = count / max(len(recent), 1)
        burst_factor = recent_freq / max(older_freq, 0.0001)

        if burst_factor > 5 and count >= 5:
            events.append({
                "keyword": word,
                "recent_count": count,
                "burst_factor": round(burst_factor, 1),
                "signal": "keyword_burst",
                "score": round(count * burst_factor, 1),
            })

    entity_spikes = _detect_entity_spikes(recent, older)
    events.extend(entity_spikes)

    events = sorted(events, key=lambda x: -x["score"])[:15]

    if events:
        logger.info("Detected %d breaking signals", len(events))
        for e in events[:5]:
            logger.info("  Breaking: %s (burst=%.1f, count=%d)", e.get("keyword", e.get("entity", "?")), e.get("burst_factor", e.get("score", 0)), e.get("recent_count", e.get("count", 0)))

    return events


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
                    if e and not _is_noise_keyword(e):
                        counter[e] += 1

    total_older = max(sum(older_entities.values()), 1)
    for entity, count in recent_entities.items():
        if count < 2:
            continue
        older_count = older_entities.get(entity, 0)
        burst = count / max(older_count / total_older * len(recent), 0.001)
        if burst > 3:
            spikes.append({
                "entity": entity,
                "recent_count": count,
                "burst_factor": round(burst, 1),
                "signal": "entity_spike",
                "score": round(count * burst, 1),
            })

    return spikes
