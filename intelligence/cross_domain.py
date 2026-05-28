import json
import logging
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

SECTORS = {
    "politics": {
        "keywords": ["government", "parliament", "election", "senate", "congress", "minister", "president",
                     "governor", "mayor", "policy", "legislation", "democrat", "republican", "party",
                     "vote", "campaign", "diplomat", "ambassador", "treaty", "sanction"],
        "org_keywords": ["senate", "congress", "parliament", "ministry", "commission", "committee",
                        "bureau", "department", "council", "authority", "fbi", "cia", "nsa", "pentagon"],
        "location_map": {"washington": "politics", "delhi": "politics", "moscow": "politics",
                        "beijing": "politics", "london": "politics", "geneva": "politics",
                        "brussels": "politics"},
    },
    "finance": {
        "keywords": ["market", "stock", "bond", "inflation", "GDP", "trade", "tariff", "export", "import",
                     "recession", "deficit", "revenue", "profit", "bank", "lending", "interest rate",
                     "fiscal", "monetary", "rupee", "dollar", "euro", "yen", "treasury", "sebi",
                     "reserve bank", "central bank", "ipo", "mutual fund", "hedge fund", "investment"],
        "org_keywords": ["bank", "finance", "capital", "venture", "invest", "market", "exchange",
                        "treasury", "fed", "imf", "world bank", "sebi", "nasdaq", "nyse",
                        "jpmorgan", "goldman", "morgan stanley", "blackrock"],
        "location_map": {"wall street": "finance", "zurich": "finance", "frankfurt": "finance",
                        "hong kong": "finance", "singapore": "finance"},
    },
    "technology": {
        "keywords": ["AI", "artificial intelligence", "machine learning", "semiconductor", "chip",
                     "software", "hardware", "cloud", "data", "algorithm", "quantum", "cyber",
                     "blockchain", "crypto", "bitcoin", "startup", "innovation", "tech", "digital",
                     "platform", "5G", "6G", "IoT", "robotics", "automation", "neural", "compute",
                     "GPU", "CPU", "open source", "API", "SaaS", "app", "mobile", "internet"],
        "org_keywords": ["google", "microsoft", "apple", "meta", "amazon", "nvidia", "intel",
                        "tsmc", "samsung", "qualcomm", "amd", "ibm", "oracle", "salesforce",
                        "twitter", "x corp", "openai", "deepmind", "anthropic", "tesla",
                        "broadcom", "micron", "applied materials", "asml", "infosys", "tcs",
                        "wipro", "hcl", "tech mahindra"],
        "location_map": {"silicon valley": "technology", "shenzhen": "technology",
                        "bengaluru": "technology", "hyderabad": "technology",
                        "pune": "technology", "san francisco": "technology",
                        "seattle": "technology"},
    },
    "energy": {
        "keywords": ["oil", "gas", "petroleum", "renewable", "solar", "wind", "nuclear", "coal",
                     "electricity", "power grid", "energy", "fuel", "refinery", "pipeline",
                     "emission", "carbon", "climate", "green energy", "hydrogen", "battery",
                     "lithium", "rare earth", "mining", "commodity", "crude", "natural gas",
                     "OPEC", "electric vehicle", "EV", "charging"],
        "org_keywords": ["opec", "shell", "bp", "exxon", "chevron", "totalenergies", "reliance",
                        "adani", "ongc", "nuclear", "power grid", "energy", "solar", "wind"],
        "location_map": {"strait of hormuz": "energy", "persian gulf": "energy",
                        "saudi": "energy", "uae": "energy", "qatar": "energy",
                        "texas": "energy", "alaska": "energy"},
    },
    "military": {
        "keywords": ["defense", "military", "army", "navy", "air force", "missile", "drone",
                     "weapon", "arms", "war", "conflict", "invasion", "battle", "troop",
                     "soldier", "general", "admiral", "nuclear weapon", "cyber attack",
                     "terrorist", "insurgency", "border", "security", "surveillance",
                     "intelligence", "spy", "counter", "reconnaissance", "submarine"],
        "org_keywords": ["army", "navy", "air force", "pentagon", "nato", "united nations",
                        "interpol", "homeland security", "defense", "military", "marine",
                        "coast guard", "cia", "fbi", "mossad", "raw", "isro", "drdo",
                        "space force", "central command"],
        "location_map": {"pentagon": "military", "kabul": "military", "kiev": "military",
                        "gaza": "military", "west bank": "military", "crimea": "military",
                        "donbas": "military", "taiwan strait": "military"},
    },
    "startups": {
        "keywords": ["startup", "founder", "funding", "seed round", "series a", "series b",
                     "venture capital", "VC", "angel", "incubator", "accelerator", "unicorn",
                     "IPO", "valuation", "pivot", "scale-up", "entrepreneur", "bootstrapped",
                     "Y Combinator", "sequoia", "a16z", "acquisition", "exit"],
        "org_keywords": ["sequoia", "a16z", "y combinator", "accel", "tiger global",
                        "softbank", "index ventures", "benchmark", "greylock",
                        "kleiner perkins", "lightspeed", "nexus venture"],
        "location_map": {},
    },
    "social": {
        "keywords": ["protest", "movement", "activist", "human rights", "inequality", "poverty",
                     "education", "healthcare", "welfare", "discrimination", "justice",
                     "equality", "freedom", "speech", "privacy", "misinformation",
                     "social media", "viral", "trending", "hashtag", "boycott", "solidarity",
                     "strike", "rally", "petition", "awareness", "campaign"],
        "org_keywords": ["united nations", "who", "unesco", "unicef", "red cross", "amnesty",
                        "human rights watch", "greenpeace", "wikipedia", "aclu", "naacp"],
        "location_map": {},
    },
    "global_events": {
        "keywords": ["earthquake", "flood", "hurricane", "pandemic", "epidemic", "disaster",
                     "tsunami", "wildfire", "drought", "famine", "crisis", "emergency",
                     "summit", "conference", "olympics", "world cup", "treaty", "accord",
                     "ceasefire", "resolution", "referendum", "independence", "sanction",
                     "embargo", "trade war", "cold war", "summit"],
        "org_keywords": ["united nations", "wto", "who", "imf", "world bank", "g7", "g20",
                        "g77", "nato", "eu", "european union", "african union", "saarc",
                        "asean", "brics", "oecd", "red cross"],
        "location_map": {},
    },
}

SECTOR_COLORS = {
    "politics": "#ef4444",
    "finance": "#22c55e",
    "technology": "#3b82f6",
    "energy": "#f59e0b",
    "military": "#dc2626",
    "startups": "#a855f7",
    "social": "#ec4899",
    "global_events": "#06b6d4",
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
    words = set(name_lower.split())

    sector_scores = defaultdict(float)

    for sector, config in SECTORS.items():
        score = 0.0
        matches = 0

        for kw in config["keywords"]:
            if kw in name_lower:
                score += 1.0
                matches += 1

        if entity_type == "orgs":
            for kw in config["org_keywords"]:
                if kw in name_lower:
                    score += 1.5
                    matches += 1

        if entity_type == "locations":
            for loc, mapped_sector in config.get("location_map", {}).items():
                if loc in name_lower and mapped_sector == sector:
                    score += 2.0
                    matches += 1

        if entity_type == "persons" and context_texts:
            context_lower = " ".join(context_texts).lower()
            for kw in config["keywords"]:
                if kw in context_lower:
                    score += 0.5

        if score > 0:
            sector_scores[sector] = score

    if not sector_scores:
        context_check = " ".join(context_texts).lower() if context_texts else ""

        if entity_type == "locations":
            geo_sector_indicators = {
                "politics": ["government", "election", "minister", "president", "vote"],
                "finance": ["market", "trade", "economy", "inflation", "gdp"],
                "military": ["war", "conflict", "attack", "defense", "troop"],
                "energy": ["oil", "gas", "energy", "pipeline", "refinery"],
            }
            for sector, indicators in geo_sector_indicators.items():
                for ind in indicators:
                    if ind in context_check:
                        sector_scores[sector] += 0.3

        if not sector_scores:
            return ("global_events", 0.1)

    best_sector = max(sector_scores, key=sector_scores.get)
    best_score = sector_scores[best_sector]
    confidence = min(best_score / 5.0, 1.0)

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
                ent_key = ent.strip().lower()
                if ent_key and len(ent_key) > 1 and "##" not in ent_key:
                    entity_contexts[ent_key].append(text[:500])
                    entity_types[ent_key] = key

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
    for s, c in sector_counts.most_common():
        logger.info("  %s: %d entities", s, c)

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
                if ek and len(ek) > 1 and "##" not in ek:
                    all_ents.add(ek)
        if len(all_ents) >= 2:
            article_entities.append({
                "entities": all_ents,
                "text": str(row.get("text", "") or ""),
                "source": str(row.get("source", "") or ""),
                "date": str(row.get("published", "") or ""),
                "category": str(row.get("category", "") or ""),
                "sentiment": row.get("compound", 0),
            })

    pair_cooccurrence = defaultdict(lambda: {"count": 0, "sources": set(), "articles": [], "sentiments": []})

    for art in article_entities:
        ents = list(art["entities"])
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                e1, e2 = ents[i], ents[j]
                s1 = sector_map.get(e1, {}).get("sector")
                s2 = sector_map.get(e2, {}).get("sector")
                if s1 and s2 and s1 != s2:
                    pair = tuple(sorted([e1, e2]))
                    pair_cooccurrence[pair]["count"] += 1
                    pair_cooccurrence[pair]["sources"].add(art["source"])
                    pair_cooccurrence[pair]["articles"].append(art["text"][:200])
                    pair_cooccurrence[pair]["sentiments"].append(art["sentiment"])

    links = []
    for (e1, e2), data in pair_cooccurrence.items():
        if data["count"] < 2:
            continue
        s1_info = sector_map.get(e1, {})
        s2_info = sector_map.get(e2, {})

        source_diversity = len(data["sources"])
        sentiment_std = float(np.std(data["sentiments"])) if len(data["sentiments"]) > 1 else 0
        if np.isnan(sentiment_std):
            sentiment_std = 0
        sentiment_variance = min(sentiment_std * 10, 1.0)
        strength = round(data["count"] * 0.4 + source_diversity * 0.3 + sentiment_variance * 0.3, 3)
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
            "example_articles": data["articles"][:3],
            "sentiment_variance": round(sentiment_variance, 3),
        })

    links.sort(key=lambda x: -x["strength"])
    logger.info("Found %d cross-domain links (showing top %d)", len(links), min(50, len(links)))
    for l in links[:10]:
        logger.info("  %s (%s) <-> %s (%s): strength=%.3f, count=%d",
                     l["source_entity"], l["source_sector"],
                     l["target_entity"], l["target_sector"],
                     l["strength"], l["cooccurrence_count"])

    return links[:200]


def build_impact_chains(df: pd.DataFrame, sector_map: Dict[str, Dict], max_depth: int = 4) -> List[Dict]:
    logger.info("Building cross-domain impact chains (max depth=%d)...", max_depth)

    try:
        import networkx as nx
    except ImportError:
        logger.warning("networkx not available for impact chains")
        return []

    G = nx.Graph()
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
                if ek and len(ek) > 1 and "##" not in ek:
                    all_ents.add(ek)
        if len(all_ents) >= 2:
            article_entities.append(all_ents)

    for ents in article_entities:
        ent_list = list(ents)
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

    try:
        from networkx.algorithms.approximation import traveling_salesman_problem
    except ImportError:
        pass

    chains = []
    sectors_ordered = ["politics", "finance", "technology", "energy", "military", "startups", "social", "global_events"]

    entities_by_sector = defaultdict(list)
    for entity, info in sector_map.items():
        entities_by_sector[info["sector"]].append(entity)

    for i in range(len(sectors_ordered)):
        s1 = sectors_ordered[i]
        for j in range(i + 1, len(sectors_ordered)):
            s2 = sectors_ordered[j]
            if s1 not in entities_by_sector or s2 not in entities_by_sector:
                continue
            source_ents = entities_by_sector[s1][:5]
            target_ents = entities_by_sector[s2][:5]
            for se in source_ents:
                for te in target_ents:
                    if se == te:
                        continue
                    try:
                        path = nx.shortest_path(G, source=se, target=te, weight="weight")
                        if 2 < len(path) <= max_depth:
                            path_sectors = []
                            for p in path:
                                ps = sector_map.get(p, {}).get("sector", "unknown")
                                path_sectors.append(ps)
                            chain_key = " -> ".join(path_sectors)
                            chains.append({
                                "chain": path[:max_depth],
                                "sectors": path_sectors,
                                "chain_key": chain_key,
                                "length": len(path),
                                "cross_domain_hops": sum(1 for k in range(1, len(path_sectors)) if path_sectors[k] != path_sectors[k-1]),
                                "total_weight": sum(G[path[k]][path[k+1]]["weight"] for k in range(len(path)-1) if G.has_edge(path[k], path[k+1])),
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
    for c in unique_chains[:5]:
        logger.info("  %s (hops=%d, weight=%.0f)", " -> ".join(c["chain"]), c["cross_domain_hops"], c["total_weight"])

    return unique_chains[:50]


def classify_sector_from_text(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for sector, config in SECTORS.items():
        score = sum(1 for kw in config["keywords"] if kw in text_lower)
        if score > 0:
            scores[sector] = score
    if not scores:
        return "global_events"
    return max(scores, key=scores.get)


def cross_domain_pipeline(df: pd.DataFrame) -> Dict:
    logger.info("=" * 60)
    logger.info("CROSS-DOMAIN RELATIONSHIP ENGINE")
    logger.info("=" * 60)

    sector_map = build_sector_map(df)
    cross_links = find_cross_domain_links(df, sector_map)
    impact_chains = build_impact_chains(df, sector_map)

    sector_counts = Counter(v["sector"] for v in sector_map.values())
    cross_sector_summary = {
        "total_entities_mapped": len(sector_map),
        "sector_distribution": dict(sector_counts.most_common()),
        "total_cross_domain_links": len(cross_links),
        "total_impact_chains": len(impact_chains),
    }

    result = {
        "sector_map": sector_map,
        "cross_domain_links": cross_links,
        "impact_chains": impact_chains,
        "summary": cross_sector_summary,
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

    logger.info("Saved: sector_map.json (%d entities), cross_domain_links.json (%d links), impact_chains.json (%d chains)",
                len(sector_map), len(cross_links), len(impact_chains))
    logger.info("=" * 60)

    return result
