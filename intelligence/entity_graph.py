import json
import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("networkx not installed, entity graph disabled")


def build_entity_graph(df: pd.DataFrame) -> Dict:
    if not HAS_NETWORKX:
        return {"error": "networkx not installed"}

    if df.empty or "entities" not in df.columns:
        return {"error": "no entity data"}

    G = nx.Graph()
    cooccurrence = Counter()

    for _, row in df.iterrows():
        entities_str = row.get("entities", "{}")
        if not isinstance(entities_str, str):
            continue
        try:
            entities = json.loads(entities_str)
        except (json.JSONDecodeError, TypeError):
            continue

        all_ents = []
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                normalized = ent.strip().lower()
                if normalized:
                    all_ents.append(normalized)
                    G.add_node(normalized, type=key)

        for i in range(len(all_ents)):
            for j in range(i + 1, len(all_ents)):
                pair = tuple(sorted([all_ents[i], all_ents[j]]))
                cooccurrence[pair] += 1

    for (e1, e2), weight in cooccurrence.most_common(200):
        G.add_edge(e1, e2, weight=weight)

    if G.number_of_nodes() == 0:
        return {"error": "no entities found"}

    try:
        centrality = nx.degree_centrality(G)
        betweenness = nx.betweenness_centrality(G, k=min(50, G.number_of_nodes()))
    except Exception:
        centrality = {n: 0 for n in G.nodes()}
        betweenness = {n: 0 for n in G.nodes()}

    top_entities = sorted(centrality.items(), key=lambda x: -x[1])[:20]

    communities = []
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        coms = greedy_modularity_communities(G)
        for i, com in enumerate(coms):
            communities.append({
                "id": i,
                "size": len(com),
                "members": sorted(com)[:15],
            })
    except Exception as e:
        logger.debug("Community detection: %s", e)

    edges = []
    for e1, e2, data in G.edges(data=True):
        weight = data.get("weight", 1)
        if weight >= 2:
            edges.append({
                "source": e1,
                "target": e2,
                "weight": weight,
                "source_type": G.nodes[e1].get("type", "unknown"),
                "target_type": G.nodes[e2].get("type", "unknown"),
            })

    edges = sorted(edges, key=lambda x: -x["weight"])[:100]

    graph_data = {
        "nodes": [
            {"id": n, "type": G.nodes[n].get("type", "unknown"), "centrality": round(centrality.get(n, 0), 4),
             "betweenness": round(betweenness.get(n, 0), 4)}
            for n, _ in top_entities
        ],
        "edges": edges,
        "stats": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "top_entities": [{"entity": e, "centrality": round(c, 4)} for e, c in top_entities],
            "communities": communities,
        },
    }

    logger.info("Entity graph: %d nodes, %d edges, %d communities", G.number_of_nodes(), G.number_of_edges(), len(communities))
    return graph_data


def get_influential_entities(graph_data: Dict, top_n: int = 10) -> List[Dict]:
    if "stats" not in graph_data:
        return []
    return graph_data["stats"].get("top_entities", [])[:top_n]


def compute_entity_trends(df: pd.DataFrame, window_days: int = 7) -> List[Dict]:
    if df.empty or "entities" not in df.columns or "published" not in df.columns:
        return []

    time_col = "published" if df["published"].notna().sum() > 0 else "scraped_at"
    df = df.copy()
    df["_date"] = pd.to_datetime(df[time_col], errors="coerce").dt.date
    df = df.dropna(subset=["_date"])

    entity_daily = defaultdict(lambda: defaultdict(int))

    for _, row in df.iterrows():
        ents_str = row.get("entities", "{}")
        if not isinstance(ents_str, str):
            continue
        try:
            entities = json.loads(ents_str)
        except (json.JSONDecodeError, TypeError):
            continue
        date = row["_date"]
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                if ent.strip():
                    entity_daily[ent.strip().lower()][date] += 1

    trends = []
    for entity, daily_counts in entity_daily.items():
        dates = sorted(daily_counts.keys())
        if len(dates) < 2:
            continue
        recent = sum(daily_counts.get(d, 0) for d in dates[-window_days:])
        older = sum(daily_counts.get(d, 0) for d in dates[:-window_days]) if len(dates) > window_days else 0
        momentum = recent - older
        if momentum > 0:
            trends.append({
                "entity": entity,
                "total_mentions": sum(daily_counts.values()),
                "recent_mentions": recent,
                "momentum": momentum,
                "peak_date": str(max(daily_counts, key=daily_counts.get)),
            })

    return sorted(trends, key=lambda x: -x["momentum"])[:20]
