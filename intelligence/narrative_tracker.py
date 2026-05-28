import json
import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _resolve_time_col(df: pd.DataFrame) -> Optional[str]:
    for col in ["published", "scraped_at", "analyzed_at"]:
        if col in df.columns and df[col].notna().sum() > len(df) * 0.3:
            return col
    return None


def compute_narrative_mutation(df: pd.DataFrame, window_days: int = 7) -> List[Dict]:
    """Track how entity/keyword narratives evolve across consecutive time windows."""
    time_col = _resolve_time_col(df)
    if time_col is None:
        return []

    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_date"]).sort_values("_date")

    if df.empty:
        return []

    date_range = (df["_date"].max() - df["_date"].min()).days
    num_windows = max(1, date_range // window_days)

    windows = []
    for i in range(num_windows + 1):
        start = df["_date"].min() + pd.Timedelta(days=i * window_days)
        end = start + pd.Timedelta(days=window_days)
        win = df[(df["_date"] >= start) & (df["_date"] < end)]
        if len(win) < 3:
            continue

        words = Counter()
        for t in win["text"].dropna():
            for w in str(t).lower().split():
                wc = w.strip(".,!?\"'():;")
                if len(wc) > 3:
                    words[wc] += 1
        total = max(sum(words.values()), 1)
        top_words = set(w for w, c in words.most_common(20))
        windows.append({
            "window_start": str(start.date()),
            "window_end": str(end.date()),
            "article_count": len(win),
            "top_words": list(top_words),
            "word_freqs": {w: c / total for w, c in words.most_common(50)},
        })

    mutations = []
    for i in range(1, len(windows)):
        prev_words = set(windows[i - 1]["top_words"])
        curr_words = set(windows[i]["top_words"])
        retained = prev_words & curr_words
        emerged = curr_words - prev_words
        disappeared = prev_words - curr_words
        retention_pct = round(len(retained) / max(len(prev_words), 1) * 100, 1) if prev_words else 0

        overlap = 0
        for w in retained:
            pf = windows[i - 1]["word_freqs"].get(w, 0)
            cf = windows[i]["word_freqs"].get(w, 0)
            overlap += min(pf, cf)
        drift = round(1 - overlap, 3)

        mutations.append({
            "window": f"{windows[i-1]['window_start']} -> {windows[i]['window_start']}",
            "prev_window": windows[i - 1]["window_start"],
            "curr_window": windows[i]["window_start"],
            "prev_articles": windows[i - 1]["article_count"],
            "curr_articles": windows[i]["article_count"],
            "retained_keywords": len(retained),
            "emerged_keywords": sorted(emerged)[:10],
            "disappeared_keywords": sorted(disappeared)[:10],
            "keyword_retention_pct": retention_pct,
            "drift_score": drift,
            "article_growth_pct": round((windows[i]["article_count"] - windows[i - 1]["article_count"]) / max(windows[i - 1]["article_count"], 1) * 100, 1),
        })

    return mutations


def detect_narrative_phases(trajectory: List[Dict], window: int = 3) -> str:
    """Classify narrative into lifecycle phase based on recent trajectory."""
    if len(trajectory) < 3:
        return "emerging"

    counts = [t["count"] for t in trajectory]
    recent = counts[-window:]
    older = counts[:-window] if len(counts) > window else counts[:1]

    recent_avg = np.mean(recent)
    older_avg = np.mean(older) if older else 0

    if recent_avg == 0:
        return "dormant"

    if older_avg == 0:
        return "emerging"

    growth_rate = (recent_avg - older_avg) / older_avg
    acceleration = 0
    if len(recent) >= 3:
        d1 = recent[-1] - recent[-2]
        d2 = recent[-2] - recent[-3]
        acceleration = d1 - d2

    if acceleration > 0 and growth_rate > 0.5:
        return "accelerating"
    elif growth_rate > 0.2:
        return "growing"
    elif growth_rate < -0.2 and acceleration < 0:
        return "declining"
    elif growth_rate < -0.5:
        return "fading"
    elif abs(growth_rate) <= 0.2 and recent_avg > older_avg * 0.5:
        return "peaked"
    elif acceleration > 0 and growth_rate < 0:
        return "resurging"
    else:
        return "stable"


def compute_narrative_sentiment_trajectory(df: pd.DataFrame, entity_name: str = None, cluster_id: int = None, window_days: int = 7) -> Dict:
    """Track sentiment over time for a specific narrative."""
    time_col = _resolve_time_col(df)
    if time_col is None:
        return {}

    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_date"])

    if entity_name:
        mask = df["entities"].fillna("").apply(
            lambda e: isinstance(e, str) and entity_name.lower() in e.lower()
        )
        df = df[mask]
    elif cluster_id is not None and "cluster" in df.columns:
        df = df[df["cluster"] == cluster_id]

    if df.empty:
        return {}

    dates = df["_date"].sort_values()
    date_range = (dates.max() - dates.min()).days
    stride = max(1, date_range // max(1, min(20, date_range // window_days)))

    points = []
    for i in range(0, len(dates), stride):
        chunk = df[(df["_date"] >= dates.iloc[i]) & (df["_date"] < dates.iloc[min(i + stride, len(dates) - 1)])]
        if chunk.empty:
            continue
        avg_sent = chunk["compound"].mean() if "compound" in chunk.columns else 0
        points.append({
            "date": str(dates.iloc[i].date()),
            "avg_sentiment": round(float(avg_sent), 3),
            "article_count": len(chunk),
        })

    return {
        "trajectory": points,
        "overall_trend": round(float(df["compound"].mean()), 3) if "compound" in df.columns else 0,
        "volatility": round(float(df["compound"].std()), 3) if "compound" in df.columns and len(df) > 1 else 0,
    }


def compute_entity_narratives(df: pd.DataFrame) -> List[Dict]:
    """Build full narrative evolution for each tracked entity."""
    time_col = _resolve_time_col(df)
    if time_col is None:
        return []

    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_date"])

    entity_daily = defaultdict(lambda: defaultdict(int))
    entity_sentiments = defaultdict(list)

    for _, row in df.iterrows():
        ents_str = row.get("entities", "{}")
        if not isinstance(ents_str, str):
            continue
        try:
            entities = json.loads(ents_str)
        except (json.JSONDecodeError, TypeError):
            continue
        date = row["_date"].date()
        sent = row.get("compound", 0)
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                ek = ent.strip().lower()
                if ek and len(ek) > 3 and "##" not in ek:
                    entity_daily[ek][date] += 1
                    entity_sentiments[ek].append(sent)

    narratives = []
    for entity, daily_counts in entity_daily.items():
        dates = sorted(daily_counts.keys())
        if len(dates) < 2:
            continue

        trajectory = [{"date": str(d), "count": daily_counts[d]} for d in dates]
        phase = detect_narrative_phases(trajectory)

        total = sum(daily_counts.values())
        recent_7 = sum(daily_counts.get(d, 0) for d in dates[-7:]) if len(dates) >= 7 else total
        prev_7 = sum(daily_counts.get(d, 0) for d in dates[-14:-7]) if len(dates) >= 14 else 0
        acceleration = recent_7 - prev_7

        avg_sent = float(np.mean(entity_sentiments[entity])) if entity_sentiments[entity] else 0
        sent_traj = compute_narrative_sentiment_trajectory(df, entity_name=entity)

        narratives.append({
            "entity": entity,
            "phase": phase,
            "acceleration": acceleration,
            "total_mentions": total,
            "recent_7_days": recent_7,
            "first_seen": str(dates[0]),
            "last_seen": str(dates[-1]),
            "trajectory": trajectory,
            "avg_sentiment": round(avg_sent, 3),
            "sentiment_trajectory": sent_traj.get("trajectory", []),
            "sentiment_volatility": sent_traj.get("volatility", 0),
        })

    return sorted(narratives, key=lambda x: -x["total_mentions"])


def compute_cluster_narratives(df: pd.DataFrame) -> List[Dict]:
    """Build narrative evolution for topic clusters."""
    if "cluster" not in df.columns or "published" not in df.columns:
        return []

    time_col = _resolve_time_col(df)
    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_date"])

    cluster_daily = defaultdict(lambda: defaultdict(int))
    for _, row in df.iterrows():
        cluster = row.get("cluster", -1)
        date = row["_date"].date()
        cluster_daily[cluster][date] += 1

    narratives = []
    for cluster, daily_counts in cluster_daily.items():
        dates = sorted(daily_counts.keys())
        if len(dates) < 2:
            continue

        trajectory = [{"date": str(d), "count": daily_counts[d]} for d in dates]
        phase = detect_narrative_phases(trajectory)

        total = sum(daily_counts.values())
        recent_7 = sum(daily_counts.get(d, 0) for d in dates[-7:]) if len(dates) >= 7 else total
        prev_7 = sum(daily_counts.get(d, 0) for d in dates[-14:-7]) if len(dates) >= 14 else 0
        acceleration = recent_7 - prev_7

        sent_traj = compute_narrative_sentiment_trajectory(df, cluster_id=cluster)

        cluster_df = df[df["cluster"] == cluster]
        top_keywords = []
        texts = cluster_df["text"].dropna().tolist()
        if texts:
            words = Counter()
            for t in texts:
                for w in str(t).lower().split():
                    wc = w.strip(".,!?\"'():;")
                    if len(wc) > 3:
                        words[wc] += 1
            top_keywords = [w for w, _ in words.most_common(10)]

        narratives.append({
            "cluster": int(cluster),
            "phase": phase,
            "acceleration": acceleration,
            "total_articles": total,
            "recent_7_days": recent_7,
            "first_seen": str(dates[0]),
            "last_seen": str(dates[-1]),
            "trajectory": trajectory,
            "top_keywords": top_keywords,
            "avg_sentiment": sent_traj.get("overall_trend", 0),
            "sentiment_trajectory": sent_traj.get("trajectory", []),
        })

    return sorted(narratives, key=lambda x: -x["total_articles"])


def find_emerging_topics(entity_narratives: List[Dict], cluster_narratives: List[Dict], top_n: int = 10) -> List[Dict]:
    """Find newly emerging topics based on acceleration and recency."""
    emerging = []
    for n in entity_narratives:
        if n["phase"] in ("emerging", "accelerating", "growing"):
            emerging.append({
                "type": "entity",
                "name": n["entity"],
                "phase": n["phase"],
                "acceleration": n["acceleration"],
                "total_mentions": n["total_mentions"],
                "recent_7_days": n["recent_7_days"],
                "first_seen": n["first_seen"],
                "avg_sentiment": n["avg_sentiment"],
            })
    for n in cluster_narratives:
        if n["phase"] in ("emerging", "accelerating", "growing"):
            emerging.append({
                "type": "cluster",
                "name": f"Cluster {n['cluster']}",
                "phase": n["phase"],
                "acceleration": n["acceleration"],
                "total_articles": n["total_articles"],
                "recent_7_days": n["recent_7_days"],
                "first_seen": n["first_seen"],
                "keywords": n.get("top_keywords", [])[:5],
                "avg_sentiment": n["avg_sentiment"],
            })

    emerging.sort(key=lambda x: (-x["acceleration"], -x["recent_7_days"]))
    return emerging[:top_n]


def find_disappearing_topics(entity_narratives: List[Dict], cluster_narratives: List[Dict], top_n: int = 10) -> List[Dict]:
    """Find topics that are fading away."""
    disappearing = []
    for n in entity_narratives:
        if n["phase"] in ("declining", "fading", "dormant"):
            disappearing.append({
                "type": "entity",
                "name": n["entity"],
                "phase": n["phase"],
                "acceleration": n["acceleration"],
                "total_mentions": n["total_mentions"],
                "last_seen": n["last_seen"],
            })
    for n in cluster_narratives:
        if n["phase"] in ("declining", "fading", "dormant"):
            disappearing.append({
                "type": "cluster",
                "name": f"Cluster {n['cluster']}",
                "phase": n["phase"],
                "acceleration": n["acceleration"],
                "total_articles": n["total_articles"],
                "last_seen": n["last_seen"],
                "keywords": n.get("top_keywords", [])[:5],
            })

    disappearing.sort(key=lambda x: (x["acceleration"], -x["total_mentions"]))
    return disappearing[:top_n]


def narrative_pipeline(df: pd.DataFrame) -> Dict:
    logger.info("=" * 60)
    logger.info("NARRATIVE EVOLUTION TRACKER")
    logger.info("=" * 60)

    mutations = compute_narrative_mutation(df)
    entity_narratives = compute_entity_narratives(df)
    cluster_narratives = compute_cluster_narratives(df)
    emerging = find_emerging_topics(entity_narratives, cluster_narratives)
    disappearing = find_disappearing_topics(entity_narratives, cluster_narratives)

    phase_counts = Counter(n["phase"] for n in entity_narratives)
    logger.info("Narrative phases: %s", dict(phase_counts.most_common()))
    logger.info("Entity narratives: %d | Cluster narratives: %d | Mutations: %d",
                len(entity_narratives), len(cluster_narratives), len(mutations))
    logger.info("Emerging: %d | Disappearing: %d", len(emerging), len(disappearing))

    result = {
        "mutations": mutations,
        "entity_narratives": entity_narratives[:50],
        "cluster_narratives": cluster_narratives[:20],
        "emerging_topics": emerging,
        "disappearing_topics": disappearing,
        "summary": {
            "total_entity_narratives": len(entity_narratives),
            "total_cluster_narratives": len(cluster_narratives),
            "total_mutations": len(mutations),
            "phase_distribution": dict(phase_counts.most_common()),
            "emerging_count": len(emerging),
            "disappearing_count": len(disappearing),
        },
    }

    from config.settings import path_for
    import os
    base = path_for("output_dir")
    with open(os.path.join(base, "narrative_evolution.json"), "w") as f:
        json.dump(result, f, indent=2)

    logger.info("Saved narrative_evolution.json")
    logger.info("=" * 60)
    return result
