"""
Cross-Domain Relationship Discovery Engine — Phase 3.

LLM-verified relationship discovery with:
- Fully integrated LLM verification (active by default when Ollama available)
- Causal relationship reasoning (cause → effect with confidence)
- Cross-domain impact prediction
- Confidence calibration across all outputs
"""

import json
import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from config.settings import atomic_write_json, get

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


# ---------------------------------------------------------------------------
# Phase 3: LLM verification with causal reasoning
# ---------------------------------------------------------------------------

def _llm_verify_relationship(source: str, target: str, src_sec: str, tgt_sec: str, contexts: List[str]) -> Optional[Dict]:
    """Verify a candidate relationship using Ollama, returning causal + confidence data."""
    try:
        import requests
    except ImportError:
        return None

    context = "\n".join(contexts[:5]) if contexts else "No direct article context available."
    prompt = (
        f"Analyze the intelligence relationship between these two entities.\n\n"
        f"Entity 1: {source} (sector: {src_sec})\n"
        f"Entity 2: {target} (sector: {tgt_sec})\n\n"
        f"Context:\n{context}\n\n"
        f"Respond with JSON only — no other text:\n"
        f'{{\n'
        f'  "relationship_exists": true/false,\n'
        f'  "confidence": 0.0-1.0,\n'
        f'  "causal_direction": "{source}" or "{target}" or "bidirectional",\n'
        f'  "causal_mechanism": "one-sentence explaining the causal link",\n'
        f'  "impact_prediction": "what downstream effects are likely",\n'
        f'  "explanation": "why these are connected"\n'
        f'}}'
    )

    model = get("intelligence.llm_model", "qwen3:14b")
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": 384}},
            timeout=45,
        )
        if not resp.ok:
            return None
        result = resp.json().get("response", "{}")
        parsed = json.loads(result)
        return {
            "verified": parsed.get("relationship_exists", True),
            "confidence": float(parsed.get("confidence", 0.5)),
            "causal_direction": parsed.get("causal_direction", "bidirectional"),
            "causal_mechanism": parsed.get("causal_mechanism", ""),
            "impact_prediction": parsed.get("impact_prediction", ""),
            "explanation": parsed.get("explanation", ""),
        }
    except Exception as e:
        logger.debug("LLM verification failed for %s<->%s: %s", source, target, e)
        return None


def _calibrate_confidence(link: Dict, llm_result: Optional[Dict] = None) -> Dict:
    """
    Calibrate relationship confidence using multiple signals:
    - Statistical strength (co-occurrence, source diversity)
    - Semantic similarity
    - LLM verification (if available)
    - Temporal density
    """
    stat_score = min(link["cooccurrence_count"] * 0.3 + link["source_diversity"] * 0.2, 5.0) / 5.0
    sem_score = link.get("semantic_similarity", 0.0)

    base_confidence = stat_score * 0.5 + sem_score * 0.5
    link["confidence"] = round(base_confidence, 3)

    if llm_result:
        llm_conf = llm_result.get("confidence", 0.5)
        link["confidence"] = round(base_confidence * 0.4 + llm_conf * 0.6, 3)
        link["verified"] = llm_result.get("verified", True)
        link["causal_direction"] = llm_result.get("causal_direction", "bidirectional")
        link["causal_mechanism"] = llm_result.get("causal_mechanism", "")
        link["impact_prediction"] = llm_result.get("impact_prediction", "")
        if llm_result.get("explanation"):
            link["explanation"] = llm_result["explanation"]

    link["confidence_label"] = (
        "high" if link["confidence"] >= 0.7 else
        "medium" if link["confidence"] >= 0.4 else
        "low"
    )
    return link


# ---------------------------------------------------------------------------
# Phase 3: Cross-domain impact prediction
# ---------------------------------------------------------------------------

def predict_cross_domain_impact(links: List[Dict], sector_map: Dict[str, Dict]) -> List[Dict]:
    """Predict the downstream impact of each relationship based on sector pair + strength."""
    impact_patterns = {
        ("politics", "finance"): {"likelihood": 0.85, "timeframe": "short", "effect": "Market volatility"},
        ("politics", "technology"): {"likelihood": 0.75, "timeframe": "medium", "effect": "Regulatory shift"},
        ("politics", "energy"): {"likelihood": 0.80, "timeframe": "short", "effect": "Energy price adjustment"},
        ("politics", "military"): {"likelihood": 0.90, "timeframe": "short", "effect": "Defense posture change"},
        ("finance", "technology"): {"likelihood": 0.70, "timeframe": "medium", "effect": "Capital reallocation"},
        ("finance", "energy"): {"likelihood": 0.75, "timeframe": "short", "effect": "Commodity price shift"},
        ("technology", "energy"): {"likelihood": 0.65, "timeframe": "long", "effect": "Infrastructure evolution"},
        ("technology", "military"): {"likelihood": 0.80, "timeframe": "medium", "effect": "Capability advantage"},
        ("technology", "startups"): {"likelihood": 0.85, "timeframe": "short", "effect": "Innovation velocity"},
        ("finance", "startups"): {"likelihood": 0.80, "timeframe": "short", "effect": "Funding environment"},
        ("energy", "military"): {"likelihood": 0.75, "timeframe": "medium", "effect": "Strategic resource shift"},
        ("social", "politics"): {"likelihood": 0.70, "timeframe": "medium", "effect": "Policy agenda change"},
    }

    for link in links:
        pair = (link["source_sector"], link["target_sector"])
        rev = (link["target_sector"], link["source_sector"])
        pattern = impact_patterns.get(pair) or impact_patterns.get(rev)
        if pattern:
            adjusted_likelihood = pattern["likelihood"] * min(link.get("confidence", 0.5) * 1.2, 1.0)
            link["impact"] = {
                "predicted_effect": pattern["effect"],
                "likelihood": round(adjusted_likelihood, 3),
                "timeframe": pattern["timeframe"],
                "confidence_weighted": round(adjusted_likelihood * link.get("confidence", 0.5), 3),
            }
        else:
            link["impact"] = {
                "predicted_effect": "Cross-domain propagation",
                "likelihood": round(0.5 * link.get("confidence", 0.5), 3),
                "timeframe": "medium",
                "confidence_weighted": round(0.5 * link.get("confidence", 0.5), 3),
            }
    return links


# ---------------------------------------------------------------------------
# Standard pipeline
# ---------------------------------------------------------------------------

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
            sims = [_cosine_sim(date_embeds[i], date_embeds[j])
                    for i in range(len(date_embeds))
                    for j in range(i + 1, len(date_embeds))]
            semantic_similarity = float(np.mean(sims)) if sims else 0.0

        strength = round(data["count"] * 0.35 + source_diversity * 0.25 + semantic_similarity * 0.40, 3)
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
            "verified": None,
            "causal_direction": None,
            "causal_mechanism": None,
            "impact_prediction": None,
            "impact": None,
        })

    links.sort(key=lambda x: -x["strength"])
    links = links[:200]
    logger.info("Found %d cross-domain links", len(links))
    return links


def apply_llm_verification(links: List[Dict], pair_texts: Dict[str, List[str]]) -> List[Dict]:
    """Apply LLM verification with causal reasoning to all high-signal relationships."""
    llm_enabled = get("intelligence.llm_verification", True)
    if not llm_enabled:
        for link in links:
            link = _calibrate_confidence(link, None)
        return links

    logger.info("Applying LLM verification with causal reasoning...")
    verified_count = 0
    for link in links:
        key = f"{link['source_entity']}__{link['target_entity']}"
        contexts = pair_texts.get(key, [])
        if link["strength"] >= 2.0:
            llm_result = _llm_verify_relationship(
                link["source_entity"], link["target_entity"],
                link["source_sector"], link["target_sector"],
                contexts,
            )
            if llm_result:
                verified_count += 1
        else:
            llm_result = None
        link = _calibrate_confidence(link, llm_result)

    logger.info("LLM verified %d/%d relationships", verified_count, len(links))
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
    for link in links:
        if link.get("explanation"):
            continue
        src, tgt = link["source_entity"], link["target_entity"]
        src_sec, tgt_sec = link["source_sector"], link["target_sector"]
        link["explanation"] = (
            f"{src} ({src_sec}) and {tgt} ({tgt_sec}) show a cross-domain intelligence "
            f"relationship with {link['cooccurrence_count']} co-occurrences across "
            f"{link['source_diversity']} distinct sources. "
            f"This {src_sec}-{tgt_sec} connection suggests that developments in "
            f"{src_sec} may create measurable effects in {tgt_sec}."
        )
    return links


def cross_domain_pipeline(df: pd.DataFrame) -> Dict:
    logger.info("=" * 60)
    logger.info("PHASE 3 — CROSS-DOMAIN RELATIONSHIP ENGINE")
    logger.info("(LLM verification · Causal reasoning · Impact prediction · Confidence calibration)")
    logger.info("=" * 60)

    sector_map = build_sector_map(df)
    cross_links = find_cross_domain_links(df, sector_map)

    # Phase 3: LLM verification with causal reasoning
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

    cross_links = apply_llm_verification(cross_links, dict(pair_texts))

    # Phase 3: Cross-domain impact prediction
    cross_links = predict_cross_domain_impact(cross_links, sector_map)

    impact_chains = build_impact_chains(df, sector_map)
    cross_links = generate_relationship_explanations(cross_links, sector_map)

    sector_counts = Counter(v["sector"] for v in sector_map.values())
    confidence_dist = Counter(l.get("confidence_label", "unknown") for l in cross_links)
    verified_count = sum(1 for l in cross_links if l.get("verified") is True)
    causal_count = sum(1 for l in cross_links if l.get("causal_mechanism"))

    summary = {
        "total_entities_mapped": len(sector_map),
        "sector_distribution": dict(sector_counts.most_common()),
        "total_cross_domain_links": len(cross_links),
        "total_impact_chains": len(impact_chains),
        "confidence_distribution": dict(confidence_dist.most_common()),
        "llm_verified": verified_count,
        "causal_explanations": causal_count,
        "avg_confidence": round(float(np.mean([l.get("confidence", 0) for l in cross_links])), 3) if cross_links else 0,
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
    atomic_write_json(os.path.join(base, "sector_map.json"), sector_map)
    atomic_write_json(os.path.join(base, "cross_domain_links.json"), cross_links)
    atomic_write_json(os.path.join(base, "impact_chains.json"), impact_chains)

    logger.info("Saved: sector_map cross_domain_links impact_chains")
    logger.info("Confidence distribution: %s", dict(confidence_dist.most_common()))
    logger.info("LLM verified: %d | Causal explanations: %d", verified_count, causal_count)
    logger.info("=" * 60)
    return result
