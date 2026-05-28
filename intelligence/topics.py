import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict

logger = logging.getLogger(__name__)


def track_topic_evolution(df: pd.DataFrame) -> Dict:
    if df.empty or "cluster" not in df.columns or "published" not in df.columns:
        return {"error": "missing cluster or published column"}

    time_col = "published" if df["published"].notna().sum() > len(df) * 0.5 else "scraped_at"
    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce").dt.date
    df = df.dropna(subset=["_date"])

    topic_daily = defaultdict(lambda: defaultdict(int))
    for _, row in df.iterrows():
        cluster = row.get("cluster", -1)
        date = row["_date"]
        topic_daily[cluster][date] += 1

    evolution = []
    for cluster, daily_counts in topic_daily.items():
        dates = sorted(daily_counts.keys())
        if len(dates) < 2:
            continue
        trajectory = []
        for d in dates:
            trajectory.append({"date": str(d), "count": daily_counts[d]})
        total = sum(daily_counts.values())
        evolution.append({
            "cluster": int(cluster),
            "label": str(cluster),
            "total_articles": total,
            "first_seen": str(dates[0]),
            "last_seen": str(dates[-1]),
            "trajectory": trajectory,
            "momentum": daily_counts.get(dates[-1], 0) - daily_counts.get(dates[-2], 0) if len(dates) >= 2 else 0,
        })

    evolution.sort(key=lambda x: -x["total_articles"])

    cluster_labels = {}
    if "cluster_label" in df.columns:
        cluster_labels = df.set_index("cluster")["cluster_label"].to_dict()

    for item in evolution:
        cl = item["cluster"]
        if cl in cluster_labels:
            item["label"] = cluster_labels[cl]

    logger.info("Topic evolution: %d clusters tracked over %d dates", len(evolution), len(df["_date"].unique()))
    return {
        "clusters": evolution,
        "total_clusters": len(evolution),
        "date_range": [str(df["_date"].min()), str(df["_date"].max())],
    }
