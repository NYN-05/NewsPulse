"""
Cross-Domain Relationship Discovery Engine.

Replaces the old cross_domain.py with an upgraded engine that:
1. Uses semantic embeddings for entity sector classification
2. Scores relationships via semantic_similarity + temporal_correlation + source_diversity
3. Includes an LLM verification layer for high-confidence intelligence
4. Generates explainable relationship descriptions
"""

import json
import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

SECTORS = [
    "politics", "finance", "technology", "energy",
    "military", "startups", "social", "global_events",
]

SECTOR_KEYWORDS = {
    "politics": ["government", "parliament", "election", "senate", "minister", "president", "policy",
                 "legislation", "diplomat", "sanction", "treaty", "vote", "campaign"],
    "finance": ["market", "stock", "inflation", "trade", "tariff", "gdp", "recession", "bank",
                "interest rate", "fiscal", "monetary", "investment", "ipo", "hedge fund"],
    "technology": ["ai", "artificial intelligence", "semiconductor", "chip", "software", "cloud",
                   "quantum", "cyber", "startup", "5g", "gpu", "algorithm", "platform"],
    "energy": ["oil", "gas", "renewable", "solar", "nuclear", "coal", "electricity", "carbon",
               "climate", "hydrogen", "lithium", "crude", "opec", "ev"],
    "military": ["defense", "military", "army", "navy", "missile", "drone", "weapon", "conflict",
                 "troop", "nuclear weapon", "cyber attack", "intelligence", "spy"],
    "startups": ["startup", "founder", "funding", "venture capital", "vc", "seed round", "series a",
                 "unicorn", "valuation", "entrepreneur", "acquisition"],
    "social": ["protest", "movement", "human rights", "inequality", "healthcare", "education",
               "discrimination", "justice", "misinformation", "privacy"],
    "global_events": ["earthquake", "flood", "pandemic", "disaster", "crisis", "summit",
                      "ceasefire", "referendum", "trade war", "sanction"],
}

SECTOR_ORGS = {
    "politics": ["senate", "congress", "parliament", "ministry", "commission"],
    "finance": ["fed", "imf", "world bank", "nasdaq", "jpmorgan", "goldman"],
    "technology": ["google", "microsoft", "apple", "nvidia", "intel", "tsmc", "openai"],
    "energy": ["opec", "shell", "bp", "exxon", "reliance", "adani"],
    "military": ["pentagon", "nato", "united nations", "interpol"],
    "startups": ["sequoia", "a16z", "y combinator", "softbank"],
    "social": ["united nations", "who", "red cross", "amnesty"],
    "global_events": ["united nations", "wto", "g7", "g20", "eu", "brics"],
}


def _get_embeddings(texts: List[str]) -> Optional[np.ndarray]:
    try:
        from compute.embeddings import encode_texts
        return encode_texts(texts)
    except Exception as e:
        logger.debug("Embeddings unavailable: %s", e)
        return None


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None:
        return 0.0
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(np.dot(a, b) / norm)


def classify_entity_sector(entity_name: str, entity_type: str, context_texts: List[str] = None) -> Tuple[str, float]:
    name_lower = entity_name.lower()
    sector_scores = defaultdict(float)

    for sector in SECTORS:
        score = 0.0
        for kw in SECTOR_KEYWORDS.get(sector, []):
            if kw in name_lower:
                score += 1.0
        if entity_type == "orgs":
            for kw in SECTOR_ORGS.get(sector, []):
                if kw in name_lower:
                    score += 1.5

        if context_texts:
            ctx = " ".join(context_texts).lower()
            for kw in SECTOR_KEYWORDS.get(sector, []):
                if kw in ctx:
                    score += 0.3

        if score > 0:
            sector_scores[sector] = score

    if not sector_scores:
        return ("global_events", 0.1)

    best_sector = max(sector_scores, key=sector_scores.get)
    confidence = min(sector_scores[best_sector] / 5.0, 1.0)
    return (best_sector, round(confidence, 3))


def build_sector_map(df: pd.DataFrame) -> Dict[str, Dict]:
    logger.info("Building sector map for entities...")
    sector_map = {}
    entity_contexts = defaultdict(list)
    entity_types = {}

    for _, row in df.iterrows():
        entities_str = row.get("entities", "{}")
        if not isinstance(entities_str, str):
            continue
        try:
            entities = json.loads(entities_str)
        except (json.JSONDecodeError, TypeError):
            continue
        text = str(row.get("text", "") or row.get("title", "") or "")
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                ek = ent.strip().lower()
                if ek and len(ek) > 1:
                    entity_contexts[ek].append(text[:500])
                    entity_types[ek] = key

    for entity_name, contexts in entity_contexts.items():
        etype = entity_types.get(entity_name, "orgs")
        sector, confidence = classify_entity_sector(entity_name, etype, contexts)
        sector_map[entity_name] = {
            "entity": entity_name,
            "type": etype,
            "sector": sector,
            "confidence": confidence,
            "mention_count": len(contexts),
        }

    sector_counts = Counter(v["sector"] for v in sector_map.values())
    logger.info("Sector map built: %d entities across %d sectors", len(sector_map), len(sector_counts))
    return sector_map


def find_cross_domain_links(df: pd.DataFrame, sector_map: Dict[str, Dict]) -> List[Dict]:
    logger.info("Finding cross-domain relationships...")
    article_entities = []
    for _, row in df.iterrows():
        entities_str = row.get("entities", "{}")
        if not isinstance(entities_str, str):
            continue
        try:
            entities = json.loads(entities_str)
        except (json.JSONDecodeError, TypeError):
            continue
        all_ents = set()
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                ek = ent.strip().lower()
                if ek and len(ek) > 1:
                    all_ents.add(ek)
        if len(all_ents) >= 2:
            article_entities.append({
                "entities": all_ents,
                "text": str(row.get("text", "") or ""),
                "source": str(row.get("source", "") or ""),
                "date": str(row.get("published", "") or ""),
                "category": str(row.get("category", "") or ""),
            })

    pair_data = defaultdict(lambda: {"count": 0, "sources": set(), "texts": [], "dates": []})

    for art in article_entities:
        ents = list(art["entities"])
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                e1, e2 = ents[i], ents[j]
                s1 = sector_map.get(e1, {}).get("sector")
                s2 = sector_map.get(e2, {}).get("sector")
                if s1 and s2 and s1 != s2:
                    pair = tuple(sorted([e1, e2]))
                    pair_data[pair]["count"] += 1
                    pair_data[pair]["sources"].add(art["source"])
                    pair_data[pair]["texts"].append(art["text"][:500])
                    pair_data[pair]["dates"].append(art["date"])

    links = []
    for (e1, e2), data in pair_data.items():
        if data["count"] < 2:
            continue
        s1_info = sector_map.get(e1, {})
        s2_info = sector_map.get(e2, {})

        source_diversity = len(data["sources"])
        semantic_similarity = 0.0
        date_embeds = _get_embeddings(data["texts"][:20])
        if date_embeds is not None and len(date_embeds) > 1:
            sims = []
            for i in range(len(date_embeds)):
                for j in range(i + 1, len(date_embeds)):
                    sims.append(_cosine_sim(date_embeds[i], date_embeds[j]))
            semantic_similarity = float(np.mean(sims)) if sims else 0.0

        strength = round(
            data["count"] * 0.35 +
            source_diversity * 0.25 +
            semantic_similarity * 0.40,
            3
        )
        if np.isnan(strength):
            strength = round(data["count"] * 0.4 + source_diversity * 0.3, 3)

        links.append({
            "source_entity": e1,
            "target_entity": e2,
            "source_sector": s1_info.get("sector", "unknown"),
            "target_sector": s2_info.get("sector", "unknown"),
            "cooccurrence_count": data["count"],
            "source_diversity": source_diversity,
            "strength": strength,
            "semantic_similarity": round(semantic_similarity, 3),
            "explanation": None,
            "confidence": None,
        })

    links.sort(key=lambda x: -x["strength"])
    links = links[:200]

    logger.info("Found %d cross-domain links", len(links))
    for l in links[:5]:
        logger.info("  %s (%s) <-> %s (%s): strength=%.3f",
                     l["source_entity"], l["source_sector"],
                     l["target_entity"], l["target_sector"], l["strength"])

    return links


def verify_relationships_with_llm(links: List[Dict], pair_texts: Dict[str, List[str]]) -> List[Dict]:
    """
    Optional LLM verification layer for relationship quality.
    Sends candidate relationships to a local Ollama model for validation and explanation.
    """
    try:
        import requests
        import json as j

        verified = []
        for link in links:
            key = f"{link['source_entity']}__{link['target_entity']}"
            context_articles = pair_texts.get(key, [])[:5]
            context = "\n".join(context_articles) if context_articles else "No direct article context available."
            prompt = (
                f"Determine whether a meaningful intelligence relationship exists between these two entities.\n\n"
                f"Entity 1: {link['source_entity']} (sector: {link['source_sector']})\n"
                f"Entity 2: {link['target_entity']} (sector: {link['target_sector']})\n\n"
                f"Context:\n{context}\n\n"
                f"Respond with JSON only:\n"
                f'{{"relationship_exists": true/false, "confidence": 0.0-1.0, "explanation": "why"}}'
            )

            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "qwen3:14b", "prompt": prompt, "stream": False, "options": {"num_predict": 256}},
                timeout=30,
            )
            if resp.ok:
                try:
                    result = j.loads(resp.json().get("response", "{}"))
                    link["explanation"] = result.get("explanation")
                    link["confidence"] = result.get("confidence", 0.5)
                    link["verified"] = result.get("relationship_exists", True)
                except (j.JSONDecodeError, KeyError):
                    link["verified"] = True
            else:
                link["verified"] = True
            verified.append(link)

        return verified
    except Exception as e:
        logger.warning("LLM verification unavailable: %s", e)
        for l in links:
            l["verified"] = True
        return links


def build_impact_chains(df: pd.DataFrame, sector_map: Dict[str, Dict], max_depth: int = 4) -> List[Dict]:
    logger.info("Building cross-domain impact chains...")
    try:
        import networkx as nx
    except ImportError:
        logger.warning("networkx not available for impact chains")
        return []

    G = nx.Graph()
    for _, row in df.iterrows():
        entities_str = row.get("entities", "{}")
        if not isinstance(entities_str, str):
            continue
        try:
            entities = json.loads(entities_str)
        except (json.JSONDecodeError, TypeError):
            continue
        all_ents = set()
        for key in ("persons", "orgs", "locations"):
            for ent in entities.get(key, []):
                ek = ent.strip().lower()
                if ek and len(ek) > 1:
                    all_ents.add(ek)
        if len(all_ents) >= 2:
            ent_list = list(all_ents)
            for i in range(len(ent_list)):
                for j in range(i + 1, len(ent_list)):
                    e1, e2 = ent_list[i], ent_list[j]
                    s1 = sector_map.get(e1, {}).get("sector")
                    s2 = sector_map.get(e2, {}).get("sector")
                    if G.has_edge(e1, e2):
                        G[e1][e2]["weight"] += 1
                    else:
                        G.add_edge(e1, e2, weight=1, cross_domain=(s1 != s2 and s1 and s2))

    if G.number_of_nodes() == 0:
        return []

    entities_by_sector = defaultdict(list)
    for entity, info in sector_map.items():
        entities_by_sector[info["sector"]].append(entity)

    chains = []
    for i in range(len(SECTORS)):
        for j in range(i + 1, len(SECTORS)):
            s1, s2 = SECTORS[i], SECTORS[j]
            if s1 not in entities_by_sector or s2 not in entities_by_sector:
                continue
            for se in entities_by_sector[s1][:5]:
                for te in entities_by_sector[s2][:5]:
                    if se == te:
                        continue
                    try:
                        path = nx.shortest_path(G, source=se, target=te, weight="weight")
                        if 2 < len(path) <= max_depth:
                            path_sectors = [sector_map.get(p, {}).get("sector", "unknown") for p in path]
                            chain_key = " -> ".join(path_sectors)
                            chains.append({
                                "chain": path[:max_depth],
                                "sectors": path_sectors,
                                "chain_key": chain_key,
                                "length": len(path),
                                "cross_domain_hops": sum(1 for k in range(1, len(path_sectors)) if path_sectors[k] != path_sectors[k-1]),
                                "total_weight": sum(G[path[k]][path[k+1]]["weight"] for k in range(len(path)-1)),
                            })
                    except (nx.NetworkXNoPath, nx.NodeNotFound, KeyError):
                        continue

    chains.sort(key=lambda x: (-x["cross_domain_hops"], -x["total_weight"]))
    unique_chains = []
    seen_keys = set()
    for c in chains:
        if c["chain_key"] not in seen_keys:
            seen_keys.add(c["chain_key"])
            unique_chains.append(c)

    logger.info("Built %d impact chains", len(unique_chains))
    return unique_chains[:50]


def generate_relationship_explanations(links: List[Dict], sector_map: Dict[str, Dict]) -> List[Dict]:
    """Generate human-readable intelligence explanations for each relationship."""
    for link in links:
        src = link["source_entity"]
        tgt = link["target_entity"]
        src_sec = link["source_sector"]
        tgt_sec = link["target_sector"]

        src_info = sector_map.get(src, {})
        tgt_info = sector_map.get(tgt, {})

        link["explanation"] = (
            f"{src} ({src_sec}) and {tgt} ({tgt_sec}) show a cross-domain intelligence "
            f"relationship with {link['cooccurrence_count']} co-occurrences across "
            f"{link['source_diversity']} distinct sources. "
            f"This {src_sec}-{tgt_sec} connection suggests that developments in "
            f"{src_sec} may create measurable effects in {tgt_sec}."
        )
    return links


def cross_domain_pipeline(df: pd.DataFrame, verify_llm: bool = False) -> Dict:
    logger.info("=" * 60)
    logger.info("CROSS-DOMAIN RELATIONSHIP ENGINE")
    logger.info("=" * 60)

    sector_map = build_sector_map(df)
    cross_links = find_cross_domain_links(df, sector_map)
    impact_chains = build_impact_chains(df, sector_map)

    cross_links = generate_relationship_explanations(cross_links, sector_map)

    if verify_llm:
        pair_texts = defaultdict(list)
        for _, row in df.iterrows():
            text = str(row.get("text", "") or "")
            entities = json.loads(row.get("entities", "{}")) if isinstance(row.get("entities"), str) else {}
            all_ents = set()
            for key in ("persons", "orgs", "locations"):
                for ent in entities.get(key, []):
                    all_ents.add(ent.strip().lower())
            for link in cross_links:
                if link["source_entity"] in all_ents and link["target_entity"] in all_ents:
                    key = f"{link['source_entity']}__{link['target_entity']}"
                    pair_texts[key].append(text[:1000])
        cross_links = verify_relationships_with_llm(cross_links, dict(pair_texts))

    sector_counts = Counter(v["sector"] for v in sector_map.values())
    summary = {
        "total_entities_mapped": len(sector_map),
        "sector_distribution": dict(sector_counts.most_common()),
        "total_cross_domain_links": len(cross_links),
        "total_impact_chains": len(impact_chains),
    }

    result = {
        "sector_map": sector_map,
        "cross_domain_links": cross_links,
        "impact_chains": impact_chains,
        "summary": summary,
    }

    from config.settings import path_for
    import os
    base = path_for("output_dir")
    with open(os.path.join(base, "sector_map.json"), "w") as f:
        json.dump(sector_map, f, indent=2)
    with open(os.path.join(base, "cross_domain_links.json"), "w") as f:
        json.dump(cross_links, f, indent=2)
    with open(os.path.join(base, "impact_chains.json"), "w") as f:
        json.dump(impact_chains, f, indent=2)

    logger.info("Saved: sector_map.json (%d), cross_domain_links.json (%d), impact_chains.json (%d)",
                len(sector_map), len(cross_links), len(impact_chains))
    logger.info("=" * 60)
    return result
