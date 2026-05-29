"""
Entity Relationship Graph.

Builds a clean NetworkX entity co-occurrence graph storing only:
- important entities (frequency + source diversity filtered)
- validated relationships (minimum 2 co-occurrences)
- high-confidence links (strength-based filtering)

Removed: entity_trends (covered by narrative engine), community detection (overkill)
"""

import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import List, Dict
from config.settings import atomic_write_json
from nlp.entities import get_entity_dict

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


def build_entity_graph(df: pd.DataFrame, max_age_days: int = 90) -> Dict:
    if not HAS_NETWORKX:
        return {"error": "networkx not installed"}
    if df.empty or "entities" not in df.columns:
        return {"error": "no entity data"}

    G = nx.Graph()
    entity_sources = defaultdict(set)
    entity_count = Counter()
    cooccurrence = Counter()

    for row in df.itertuples(index=False):
        entities = get_entity_dict(row)
        source = str(getattr(row, "source", ""))
        all_ents = []
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                normalized = ent.strip().lower()
                if normalized and len(normalized) > 1:
                    all_ents.append(normalized)
                    entity_count[normalized] += 1
                    entity_sources[normalized].add(source)

        for i in range(len(all_ents)):
            for j in range(i + 1, len(all_ents)):
                pair = tuple(sorted([all_ents[i], all_ents[j]]))
                cooccurrence[pair] += 1

    min_mentions = 2
    important = {e for e, c in entity_count.items() if c >= min_mentions and len(entity_sources[e]) >= 1}

    for entity in important:
        G.add_node(entity, count=entity_count[entity], sources=len(entity_sources[entity]))

    for (e1, e2), weight in cooccurrence.most_common(200):
        if e1 in important and e2 in important and weight >= 2:
            G.add_edge(e1, e2, weight=weight)

    if G.number_of_nodes() == 0:
        return {"error": "no important entities found"}

    try:
        centrality = nx.degree_centrality(G)
    except Exception:
        centrality = {n: 0 for n in G.nodes()}

    top_entities = sorted(centrality.items(), key=lambda x: -x[1])[:30]

    edges = [
        {"source": e1, "target": e2, "weight": data.get("weight", 1)}
        for e1, e2, data in G.edges(data=True)
        if data.get("weight", 1) >= 2
    ]
    edges = sorted(edges, key=lambda x: -x["weight"])[:100]

    graph_data = {
        "nodes": [
            {"id": n, "centrality": round(centrality.get(n, 0), 4),
             "count": G.nodes[n].get("count", 0), "sources": G.nodes[n].get("sources", 0)}
            for n, _ in top_entities
        ],
        "edges": edges,
        "stats": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "top_entities": [{"entity": e, "centrality": round(c, 4)} for e, c in top_entities[:10]],
        },
    }
    logger.info("Entity graph: %d important nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return graph_data
