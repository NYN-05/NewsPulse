"""
Causal Reasoning Engine — Phase 3.

Analyzes temporal entity sequences to discover cause-effect patterns:
- Causal link detection from temporal co-occurrence
- Cross-domain causal chain discovery
- Impact propagation modeling
"""

import logging
import networkx as nx
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from config.settings import get
from nlp.entities import get_entity_dict

logger = logging.getLogger(__name__)

SECTOR_CAUSAL_PATTERNS = {
    ("politics", "finance"): "policy_shock",
    ("politics", "technology"): "regulatory_drag",
    ("finance", "energy"): "price_transmission",
    ("technology", "military"): "capability_shift",
    ("energy", "politics"): "resource_conflict",
    ("social", "politics"): "preference_driven",
    ("technology", "energy"): "demand_shock",
    ("finance", "startups"): "capital_flow",
    ("military", "technology"): "procurement_driven",
    ("politics", "military"): "strategic_posture",
}


def detect_causal_candidates(
    df,
    entity_pairs: List[Tuple[str, str, Dict]],
    lookback_days: int = 30,
    min_lag_hours: int = 6,
    max_lag_days: int = 14,
) -> List[Dict]:
    logger.info("Detecting causal candidates with temporal analysis...")
    articles = []
    for row in df.itertuples(index=False):
        date_str = getattr(row, "published", "")
        if not isinstance(date_str, str):
            date_str = getattr(row, "date", "")
        if not isinstance(date_str, str):
            date_str = ""
        text = str(getattr(row, "text", "") or "")
        if date_str and text:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError, AttributeError):
                continue
            entities = set()
            parsed = get_entity_dict(row)
            for key in ("persons", "orgs", "locations"):
                for ent in parsed.get(key, []):
                    e = ent.strip().lower()
                    if e and len(e) > 1:
                        entities.add(e)
            articles.append({"date": dt, "entities": entities, "text": text})

    articles.sort(key=lambda x: x["date"])
    if len(articles) < 5:
        logger.warning("Too few articles with dates for causal analysis")
        return []

    candidates = []
    for src, tgt, _ in entity_pairs:
        src_mentions = [a for a in articles if src in a["entities"]]
        tgt_mentions = [a for a in articles if tgt in a["entities"]]
        if len(src_mentions) < 2 or len(tgt_mentions) < 2:
            continue

        src_times = np.array([a["date"].timestamp() for a in src_mentions])
        tgt_times = np.array([a["date"].timestamp() for a in tgt_mentions])

        lag_hours_list = []
        for st in src_times:
            diffs = (tgt_times - st) / 3600.0
            valid = diffs[(diffs >= min_lag_hours) & (diffs <= max_lag_days * 24)]
            if len(valid) > 0:
                lag_hours_list.extend(valid.tolist())

        reverse_lag = []
        for tt in tgt_times:
            diffs = (src_times - tt) / 3600.0
            valid = diffs[(diffs >= min_lag_hours) & (diffs <= max_lag_days * 24)]
            if len(valid) > 0:
                reverse_lag.extend(valid.tolist())

        evidence = len(src_mentions) + len(tgt_mentions)
        if max(len(lag_hours_list), len(reverse_lag)) < 2:
            continue

        causal_score = 0.0
        direction = "bidirectional"
        if len(lag_hours_list) > len(reverse_lag) * 2:
            direction = f"{src}->{tgt}"
            mean_lag = float(np.mean(lag_hours_list)) if lag_hours_list else 0
            causal_score = min(len(lag_hours_list) / max(evidence, 1) * 0.5 + 0.3, 1.0)
            candidates.append({
                "source": src, "target": tgt,
                "direction": direction, "mean_lag_hours": round(mean_lag, 1),
                "lag_samples": len(lag_hours_list),
                "causal_score": round(causal_score, 3),
                "evidence_strength": evidence,
                "mechanism": "temporal_precedence",
            })
        elif len(reverse_lag) > len(lag_hours_list) * 2:
            direction = f"{tgt}->{src}"
            mean_lag = float(np.mean(reverse_lag)) if reverse_lag else 0
            causal_score = min(len(reverse_lag) / max(evidence, 1) * 0.5 + 0.3, 1.0)
            candidates.append({
                "source": tgt, "target": src,
                "direction": direction, "mean_lag_hours": round(mean_lag, 1),
                "lag_samples": len(reverse_lag),
                "causal_score": round(causal_score, 3),
                "evidence_strength": evidence,
                "mechanism": "temporal_precedence",
            })

    candidates.sort(key=lambda x: -x["causal_score"])
    logger.info("Found %d causal candidates", len(candidates))
    return candidates[:100]


def build_causal_graph(candidates: List[Dict], sector_map: Dict) -> nx.DiGraph:
    G = nx.DiGraph()
    for c in candidates:
        src_sec = sector_map.get(c["source"], {}).get("sector", "unknown")
        tgt_sec = sector_map.get(c["target"], {}).get("sector", "unknown")
        pattern = SECTOR_CAUSAL_PATTERNS.get((src_sec, tgt_sec)) or \
                  SECTOR_CAUSAL_PATTERNS.get((tgt_sec, src_sec)) or "general"
        G.add_edge(c["source"], c["target"],
                   weight=c["causal_score"],
                   mechanism=c.get("mechanism", "unknown"),
                   pattern=pattern,
                   mean_lag_hours=c.get("mean_lag_hours", 0))
    return G


def find_causal_chains(G: nx.DiGraph, max_depth: int = 5) -> List[Dict]:
    chains = []
    if G.number_of_nodes() == 0:
        return chains

    sources = [n for n in G.nodes() if G.in_degree(n) == 0 and G.out_degree(n) > 0]
    if not sources:
        sources = list(G.nodes())[:10]

    for src in sources[:20]:
        try:
            paths = nx.single_source_shortest_path(G, src, cutoff=max_depth)
            for target, path in paths.items():
                if len(path) >= 3:
                    chain_score = sum(G[path[i]][path[i+1]]["weight"] for i in range(len(path)-1))
                    chain_score /= (len(path) - 1)
                    chains.append({
                        "chain": path,
                        "length": len(path),
                        "avg_causal_score": round(chain_score, 3),
                        "mechanisms": [G[path[i]][path[i+1]].get("pattern", "general")
                                       for i in range(len(path)-1)],
                    })
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

    chains.sort(key=lambda x: (-x["avg_causal_score"], -x["length"]))
    unique = []
    seen = set()
    for c in chains:
        key = "->".join(c["chain"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    logger.info("Found %d unique causal chains", len(unique))
    return unique[:30]


def causal_pipeline(df, sector_map: Dict, entity_pairs: List[Tuple[str, str, Dict]]) -> Dict:
    logger.info("=" * 60)
    logger.info("CAUSAL REASONING ENGINE")
    logger.info("=" * 60)

    candidates = detect_causal_candidates(df, entity_pairs)
    causal_graph = build_causal_graph(candidates, sector_map)
    chains = find_causal_chains(causal_graph)
    G = causal_graph

    summary = {
        "total_candidates": len(candidates),
        "total_causal_chains": len(chains),
        "graph_nodes": G.number_of_nodes(),
        "graph_edges": G.number_of_edges(),
        "avg_causal_score": round(float(np.mean([c["causal_score"] for c in candidates])), 3) if candidates else 0,
    }

    result = {
        "causal_candidates": candidates,
        "causal_chains": chains,
        "causal_graph": {
            "nodes": [{"id": n} for n in G.nodes()],
            "edges": [{"source": u, "target": v, **d} for u, v, d in G.edges(data=True)],
        },
        "summary": summary,
    }

    logger.info("Candidates: %d | Chains: %d | Graph: %d nodes, %d edges",
                len(candidates), len(chains), G.number_of_nodes(), G.number_of_edges())
    return result
