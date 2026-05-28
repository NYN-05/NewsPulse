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


def compute_entity_influence(df: pd.DataFrame, cross_domain_links: List[Dict] = None) -> List[Dict]:
    """Score each entity on its influence based on centrality, acceleration, cross-domain reach, and sentiment impact."""
    time_col = _resolve_time_col(df)
    if time_col is None:
        return []

    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_date"])

    entity_stats = defaultdict(lambda: {
        "mentions": 0, "recent_mentions": 0, "sources": set(),
        "categories": set(), "sentiments": [], "cross_domain_links": 0,
    })

    cutoff = df["_date"].max() - pd.Timedelta(days=7)
    for _, row in df.iterrows():
        ents_str = row.get("entities", "{}")
        if not isinstance(ents_str, str):
            continue
        try:
            entities = json.loads(ents_str)
        except (json.JSONDecodeError, TypeError):
            continue
        is_recent = row["_date"] >= cutoff
        source = str(row.get("source", ""))
        category = str(row.get("category", ""))
        sent = row.get("compound", 0)
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                ek = ent.strip().lower()
                if ek and len(ek) > 2 and "##" not in ek:
                    entity_stats[ek]["mentions"] += 1
                    entity_stats[ek]["sources"].add(source)
                    entity_stats[ek]["categories"].add(category)
                    entity_stats[ek]["sentiments"].append(sent)
                    if is_recent:
                        entity_stats[ek]["recent_mentions"] += 1

    cross_domain_entity_links = Counter()
    if cross_domain_links:
        for l in cross_domain_links:
            cross_domain_entity_links[l["source_entity"]] += 1
            cross_domain_entity_links[l["target_entity"]] += 1

    try:
        graph_path = None
        from config.settings import path_for
        import os
        graph_path = os.path.join(path_for("output_dir"), "entity_graph.json")
        graph_data = None
        if os.path.exists(graph_path):
            with open(graph_path) as f:
                graph_data = json.load(f)
    except Exception:
        graph_data = None

    centrality_map = {}
    if graph_data and "stats" in graph_data:
        for e in graph_data["stats"].get("top_entities", []):
            centrality_map[e["entity"]] = e["centrality"]

    influences = []
    for entity, stats in entity_stats.items():
        if stats["mentions"] < 2:
            continue

        mention_score = min(stats["mentions"] / 10, 10)
        recency_ratio = stats["recent_mentions"] / max(stats["mentions"], 1)
        recency_score = recency_ratio * 5
        source_diversity = min(len(stats["sources"]) / 2, 5)
        category_diversity = min(len(stats["categories"]) / 2, 3)
        cross_domain_score = min(cross_domain_entity_links.get(entity, 0) / 2, 5)
        centrality = centrality_map.get(entity, 0)
        centrality_score = centrality * 100

        if stats["sentiments"]:
            sent_mean = float(np.mean(stats["sentiments"]))
            sentiment_impact = abs(sent_mean) * 2 if not np.isnan(sent_mean) else 0
        else:
            sentiment_impact = 0

        influence_score = round(
            (mention_score or 0) * 0.25 +
            (recency_score or 0) * 0.20 +
            (source_diversity or 0) * 0.20 +
            (category_diversity or 0) * 0.10 +
            (cross_domain_score or 0) * 0.15 +
            (centrality_score or 0) * 0.05 +
            (sentiment_impact or 0) * 0.05,
            3
        )
        if np.isnan(influence_score):
            influence_score = 0

        influences.append({
            "entity": entity,
            "influence_score": influence_score,
            "total_mentions": stats["mentions"],
            "recent_mentions": stats["recent_mentions"],
            "source_count": len(stats["sources"]),
            "category_count": len(stats["categories"]),
            "cross_domain_links": cross_domain_entity_links.get(entity, 0),
            "centrality": round(centrality, 4),
            "avg_sentiment": round(float(np.mean(stats["sentiments"])), 3) if stats["sentiments"] else 0,
        })

    influences.sort(key=lambda x: -x["influence_score"])
    logger.info("Entity influence computed: %d entities scored", len(influences))
    for e in influences[:5]:
        logger.info("  Top: %s (score=%.3f, mentions=%d, sources=%d, cross-domain links=%d)",
                     e["entity"], e["influence_score"], e["total_mentions"],
                     e["source_count"], e["cross_domain_links"])
    return influences


def compute_source_amplification(df: pd.DataFrame) -> List[Dict]:
    """Score each source on amplification power: breadth, speed, cross-domain coverage, sentiment extremity."""
    time_col = _resolve_time_col(df)
    if time_col is None:
        return []

    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_date"]).sort_values("_date")

    source_stats = defaultdict(lambda: {
        "articles": 0, "entities": set(), "categories": set(),
        "sentiments": [], "sensationalism": [], "daily_counts": defaultdict(int),
        "first_seen": None,
    })

    for _, row in df.iterrows():
        source = str(row.get("source", ""))
        if not source:
            continue
        stats = source_stats[source]
        stats["articles"] += 1
        date = row["_date"].date()
        stats["daily_counts"][date] += 1
        if stats["first_seen"] is None or date < stats["first_seen"]:
            stats["first_seen"] = date

        ents_str = row.get("entities", "{}")
        if isinstance(ents_str, str):
            try:
                entities = json.loads(ents_str)
                for key in ("persons", "orgs", "locations"):
                    for ent in entities.get(key, []):
                        ek = ent.strip().lower()
                        if ek and len(ek) > 2:
                            stats["entities"].add(ek)
            except (json.JSONDecodeError, TypeError):
                pass

        cat = str(row.get("category", ""))
        if cat:
            stats["categories"].add(cat)
        sent = row.get("compound", 0)
        if not np.isnan(sent):
            stats["sentiments"].append(sent)
        sens = row.get("sensationalism_score", 0)
        if not np.isnan(sens):
            stats["sensationalism"].append(sens)

    all_first_seen = [s["first_seen"] for s in source_stats.values() if s["first_seen"]]
    global_first = min(all_first_seen) if all_first_seen else datetime.now().date()

    amplifications = []
    for source, stats in source_stats.items():
        if stats["articles"] < 3:
            continue

        reach = min(len(stats["entities"]) / 10, 8)
        category_breadth = min(len(stats["categories"]) * 1.5, 6)
        article_volume = min(stats["articles"] / 20, 5)

        if stats["sentiments"]:
            extremity = abs(float(np.mean(stats["sentiments"]))) * 3
        else:
            extremity = 0

        if stats["sensationalism"]:
            sens_mean = float(np.mean(stats["sensationalism"])) * 2
        else:
            sens_mean = 0

        days_active = max((datetime.now().date() - stats["first_seen"]).days, 1)
        daily_rate = stats["articles"] / days_active

        amp_score = round(
            reach * 0.30 +
            category_breadth * 0.20 +
            article_volume * 0.15 +
            extremity * 0.15 +
            sens_mean * 0.10 +
            daily_rate * 0.10,
            3
        )

        amplifications.append({
            "source": source,
            "amplification_score": amp_score,
            "total_articles": stats["articles"],
            "entity_count": len(stats["entities"]),
            "category_count": len(stats["categories"]),
            "avg_sentiment": round(float(np.mean(stats["sentiments"])), 3) if stats["sentiments"] else 0,
            "avg_sensationalism": round(float(np.mean(stats["sensationalism"])), 4) if stats["sensationalism"] else 0,
            "sentiment_extremity": round(extremity, 3),
            "daily_article_rate": round(daily_rate, 2),
        })

    amplifications.sort(key=lambda x: -x["amplification_score"])
    logger.info("Source amplification computed: %d sources scored", len(amplifications))
    for s in amplifications[:5]:
        logger.info("  Top: %s (score=%.3f, articles=%d, entities=%d, categories=%d)",
                     s["source"], s["amplification_score"], s["total_articles"],
                     s["entity_count"], s["category_count"])
    return amplifications


def compute_information_propagation(df: pd.DataFrame) -> Dict:
    """Track how fast narratives propagate across the source ecosystem."""
    time_col = _resolve_time_col(df)
    if time_col is None:
        return {}

    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["_date"]).sort_values("_date")

    entity_first_seen = {}
    entity_source_timeline = defaultdict(lambda: defaultdict(list))

    for _, row in df.iterrows():
        ents_str = row.get("entities", "{}")
        if not isinstance(ents_str, str):
            continue
        try:
            entities = json.loads(ents_str)
        except (json.JSONDecodeError, TypeError):
            continue
        date = row["_date"]
        source = str(row.get("source", ""))
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                ek = ent.strip().lower()
                if ek and len(ek) > 2 and "##" not in ek:
                    if ek not in entity_first_seen:
                        entity_first_seen[ek] = date
                    entity_source_timeline[ek][source].append(date)

    propagation_data = []
    for entity, source_dates in entity_source_timeline.items():
        all_dates = sorted([d for dates in source_dates.values() for d in dates])
        if len(all_dates) < 3:
            continue

        first_date = all_dates[0]
        last_date = all_dates[-1]
        timespan = (last_date - first_date).total_seconds() / 3600
        days_span = max(timespan / 24, 1)

        source_count = len(source_dates)
        article_count = len(all_dates)
        density = article_count / days_span

        if source_count > 1:
            source_first_dates = sorted([min(dates) for dates in source_dates.values()])
            adoption_times = []
            for i in range(1, len(source_first_dates)):
                gap = (source_first_dates[i] - source_first_dates[0]).total_seconds() / 3600
                adoption_times.append(gap)
            mean_adoption = float(np.mean(adoption_times)) if adoption_times else 0
            spread_speed = round(source_count / max(mean_adoption / 24, 1), 2) if mean_adoption > 0 else 99
        else:
            mean_adoption = 0
            spread_speed = 0

        propagation_data.append({
            "entity": entity,
            "first_seen": str(first_date),
            "timespan_hours": round(timespan, 1),
            "source_count": source_count,
            "article_count": article_count,
            "density_articles_per_day": round(density, 2),
            "mean_adoption_hours": round(mean_adoption, 1),
            "spread_speed": spread_speed,
        })

    propagation_data.sort(key=lambda x: (-x["spread_speed"], -x["source_count"]))

    logger.info("Information propagation: %d entities tracked", len(propagation_data))
    for p in propagation_data[:5]:
        logger.info("  Fastest: %s (speed=%.1f, sources=%d, articles=%d, density=%.1f/day)",
                     p["entity"], p["spread_speed"], p["source_count"],
                     p["article_count"], p["density_articles_per_day"])

    return {
        "propagation": propagation_data[:50],
        "summary": {
            "total_tracked": len(propagation_data),
            "fastest_spread": propagation_data[0] if propagation_data else None,
        },
    }


def influence_pipeline(df: pd.DataFrame) -> Dict:
    logger.info("=" * 60)
    logger.info("INFLUENCE MAPPING ENGINE")
    logger.info("=" * 60)

    cross_domain_links = []
    from config.settings import path_for
    import os
    links_path = os.path.join(path_for("output_dir"), "cross_domain_links.json")
    if os.path.exists(links_path):
        try:
            with open(links_path) as f:
                cross_domain_links = json.load(f)
        except Exception:
            pass

    entity_influence = compute_entity_influence(df, cross_domain_links)
    source_amplification = compute_source_amplification(df)
    propagation = compute_information_propagation(df)

    result = {
        "entity_influence": entity_influence[:100],
        "source_amplification": source_amplification[:50],
        "propagation": propagation.get("propagation", []),
        "summary": {
            "total_entities_scored": len(entity_influence),
            "total_sources_scored": len(source_amplification),
            "total_propagation_tracked": propagation.get("summary", {}).get("total_tracked", 0),
            "top_influencer": entity_influence[0]["entity"] if entity_influence else None,
            "top_amplifier": source_amplification[0]["source"] if source_amplification else None,
        },
    }

    base = path_for("output_dir")
    with open(os.path.join(base, "influence_map.json"), "w") as f:
        json.dump(result, f, indent=2)

    logger.info("Saved influence_map.json")
    logger.info("=" * 60)
    return result
