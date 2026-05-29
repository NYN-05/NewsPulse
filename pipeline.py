#!/usr/bin/env python3
"""
NewsPulse — AI-Powered Cross-Domain Intelligence Discovery Engine

Core pipeline: scrape → analyze → entity graph → cross-domain relationships →
causal reasoning → narrative evolution → signal detection → multi-agent analysis →
temporal patterns → briefings → alerts → export → semantic search indexing
"""

import os
import sys
import json
import logging
import numpy as np
from datetime import datetime
from collections import defaultdict
import pandas as pd

from config.settings import load_config, get, path_for, atomic_write_json
from compute.gpu_manager import GPUManager
from storage.manager import DataManager
from scraper.sources import scrape_all_sources, fetch_all_details
from scraper.rss_scraper import scrape_all_rss
from nlp.preprocess import clean_text, extract_category
from nlp.entities import extract_entities_batch
from quality.dedup import deduplicate_semantic_lsh, deduplicate_exact
from quality.boilerplate import remove_boilerplate, extract_clean_title
from intelligence.entity_graph import build_entity_graph
from intelligence.relationships import cross_domain_pipeline
from intelligence.narratives import narrative_pipeline
from intelligence.signals import signals_pipeline
from intelligence.causal import causal_pipeline
from intelligence.agents import multi_agent_pipeline
from intelligence.temporal import temporal_pipeline
from intelligence.briefings import generate_briefing
from intelligence.alerting import alerting_pipeline
from multilingual.detect import detect_language

logger = logging.getLogger("pipeline")


def setup_logging():
    load_config()
    level = getattr(logging, get("logging.level", "INFO").upper(), logging.INFO)
    fmt = get("logging.format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.basicConfig(level=level, format=fmt, stream=sys.stdout)


def init_gpu():
    from compute.gpu_manager import GPUManager, detect_cuda
    detect_cuda()
    _ = GPUManager()
    logger.info("GPU initialized: device=%s", GPUManager().device)


def step_scrape(data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Intelligence Step 1: Scrape Web Sources ===")
    new = scrape_all_sources()
    if new:
        df = data_mgr.merge_new_articles(new)
        logger.info("Web scrape: %d new articles", len(new))
    else:
        df = data_mgr.load_raw()
    logger.info("Total raw articles: %d", len(df))
    return df


def step_scrape_rss(data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Intelligence Step 2: Scrape RSS Feeds ===")
    new = scrape_all_rss()
    if new:
        df = data_mgr.merge_new_articles(new)
        logger.info("RSS scrape: %d new articles", len(new))
    else:
        df = data_mgr.load_raw()
    return df


def step_dedup(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Intelligence Step 3: Deduplication ===")
    n_before = len(df)
    df = deduplicate_exact(df)
    if get("quality.enable_semantic_dedup", True) and len(df) > 10:
        df = deduplicate_semantic_lsh(df, threshold=get("quality.dedup_threshold", 0.85))
    data_mgr.save_raw(df)
    logger.info("Dedup: %d -> %d (removed %d)", n_before, len(df), n_before - len(df))
    return df


def step_fetch_details(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Intelligence Step 4: Fetch Article Details ===")
    if "full_text" not in df.columns:
        df["full_text"] = ""
        df["full_text_fetched_at"] = ""

    if get("quality.enable_boilerplate_removal", True):
        if "description" in df.columns:
            df["description"] = df["description"].apply(remove_boilerplate)
        if "title" in df.columns:
            df["clean_title_extracted"] = df["title"].apply(extract_clean_title)

    df = fetch_all_details(df)
    full_raw = data_mgr.load_raw()
    if not full_raw.empty and len(full_raw) > len(df):
        logger.info("Merging detail updates into full raw dataset (%d rows)", len(full_raw))
        for col in ["full_text", "full_text_fetched_at"]:
            if col in df.columns:
                full_raw[col] = full_raw[col].fillna("")
        update_map = df.set_index("link")[["full_text", "full_text_fetched_at"]].to_dict("index")
        for idx, row in full_raw.iterrows():
            link = row.get("link", "")
            if link in update_map:
                full_raw.at[idx, "full_text"] = update_map[link]["full_text"]
                full_raw.at[idx, "full_text_fetched_at"] = update_map[link]["full_text_fetched_at"]
        data_mgr.save_raw(full_raw)
    else:
        data_mgr.save_raw(df)
    return df


def step_analyze(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Intelligence Step 5: NLP Analysis ===")
    old_analyzed = data_mgr.load_analyzed()
    existing_keys = data_mgr.get_existing_keys(old_analyzed) if not old_analyzed.empty else set()

    df_all = df.drop_duplicates(subset=["title"]).reset_index(drop=True).copy()
    titles = df_all["title"].fillna("").astype(str).str.strip().str.lower()
    links = df_all["link"].fillna("").astype(str).str.strip()
    srcs = df_all["source"].fillna("").astype(str).str.strip() if "source" in df_all.columns else ""
    if existing_keys:
        is_new = [k not in existing_keys for k in zip(titles, links, srcs)]
    else:
        is_new = [True] * len(df_all)
    to_analyze = df_all[is_new].copy()

    if to_analyze.empty:
        logger.info("No new articles to analyze")
        return old_analyzed if not old_analyzed.empty else df

    logger.info("Raw in: %d | New candidates: %d", len(df), len(to_analyze))
    to_analyze["title"] = to_analyze["title"].apply(clean_text)
    to_analyze["description"] = to_analyze["description"].apply(clean_text)
    cats = to_analyze["title"].apply(extract_category)
    to_analyze["category"] = cats.apply(lambda x: x[0])
    to_analyze["clean_title"] = cats.apply(lambda x: x[1])
    to_analyze["text"] = to_analyze["clean_title"].fillna("") + ". " + to_analyze["description"].fillna("")
    to_analyze = to_analyze[to_analyze["text"].str.len() > 20]

    logger.info("Extracting entities with GLiNER...")
    to_analyze["entities"] = extract_entities_batch(to_analyze["text"].tolist())
    to_analyze["_parsed_entities"] = to_analyze["entities"].apply(json.loads)

    logger.info("Detecting languages...")
    to_analyze["language"] = to_analyze["text"].apply(
        lambda t: detect_language(t) if isinstance(t, str) and t.strip() else "unknown"
    )
    non_english = (to_analyze["language"] != "en").sum()
    if non_english > 0:
        logger.info("Non-English articles: %d", non_english)

    to_analyze["analyzed_at"] = datetime.now().isoformat()

    df_result = pd.concat([old_analyzed, to_analyze], ignore_index=True) if not old_analyzed.empty else to_analyze
    data_mgr.save_analyzed(df_result)
    logger.info("Analyzed %d new articles (%d total)", len(to_analyze), len(df_result))
    return df_result


def step_entity_graph(df: pd.DataFrame):
    logger.info("=== Intelligence Step 6: Entity Relationship Graph ===")
    graph = build_entity_graph(df, max_age_days=90)
    if "stats" in graph:
        s = graph["stats"]
        logger.info("Entity graph: %d important nodes, %d edges", s.get("total_nodes", 0), s.get("total_edges", 0))
    atomic_write_json(os.path.join(path_for("output_dir"), "entity_graph.json"), graph)


def step_cross_domain(df: pd.DataFrame):
    logger.info("=== Intelligence Step 7: Cross-Domain Relationship Discovery ===")
    result = cross_domain_pipeline(df)
    s = result.get("summary", {})
    sector_map = result.get("sector_map", {})
    links = result.get("cross_domain_links", [])
    chains = result.get("impact_chains", [])
    base = path_for("output_dir")
    atomic_write_json(os.path.join(base, "sector_map.json"), sector_map)
    atomic_write_json(os.path.join(base, "cross_domain_links.json"), links)
    atomic_write_json(os.path.join(base, "impact_chains.json"), chains)
    logger.info("Cross-domain: %d links, %d chains across %d entities (LLM=%d, causal=%d)",
                s.get("total_cross_domain_links", 0), s.get("total_impact_chains", 0),
                s.get("total_entities_mapped", 0),
                s.get("llm_verified", 0), s.get("causal_explanations", 0))
    return result


def step_causal(df: pd.DataFrame, sector_map: dict, entity_pairs: list):
    if not get("causal.enabled", True):
        logger.info("Causal reasoning disabled in config")
        return {}
    logger.info("=== Phase 3 Step: Causal Reasoning ===")
    result = causal_pipeline(df, sector_map, entity_pairs)
    atomic_write_json(os.path.join(path_for("output_dir"), "causal_analysis.json"), result)
    logger.info("Causal: %d candidates, %d chains",
                result.get("summary", {}).get("total_candidates", 0),
                result.get("summary", {}).get("total_causal_chains", 0))
    return result


def step_narratives(df: pd.DataFrame):
    logger.info("=== Intelligence Step 8: Narrative Evolution Tracking ===")
    result = narrative_pipeline(df)
    s = result.get("summary", {})
    atomic_write_json(os.path.join(path_for("output_dir"), "narrative_evolution.json"), result)
    logger.info("Narratives: %d emerging, %d disappearing, %d mutations",
                s.get("emerging_count", 0), s.get("disappearing_count", 0), s.get("total_mutations", 0))
    return result


def step_signals(df: pd.DataFrame):
    logger.info("=== Intelligence Step 9: Signal Detection ===")
    result = signals_pipeline(df)
    s = result.get("summary", {})
    atomic_write_json(os.path.join(path_for("output_dir"), "breaking_events.json"), result)
    signals = result.get("signals", [])
    # WebSocket broadcast for signals
    if signals:
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            from dashboard.backend.ws import broadcast_signal
            for sig in signals[:5]:
                loop.run_until_complete(broadcast_signal(sig))
            loop.close()
        except Exception:
            pass
    logger.info("Signals: %d total (highest score: %.1f)", s.get("total_signals", 0), s.get("highest_score", 0))
    return result


def step_multi_agent(cross_domain_links: list, impact_chains: list):
    if not get("intelligence.multi_agent.enabled", True):
        logger.info("Multi-agent analysis disabled in config")
        return {}
    logger.info("=== Phase 4 Step: Multi-Agent Intelligence Analysis ===")
    result = multi_agent_pipeline(cross_domain_links, impact_chains)
    atomic_write_json(os.path.join(path_for("output_dir"), "multi_agent_analysis.json"), result)
    findings = result.get("analyst", {}).get("findings", [])
    logger.info("Multi-agent: %d findings, quality=%s",
                len(findings), result.get("critic", {}).get("overall_quality", "unknown"))
    return result


def step_temporal(df: pd.DataFrame, narrative_data: dict):
    if not get("intelligence.temporal.enabled", True):
        logger.info("Temporal analysis disabled in config")
        return {}
    logger.info("=== Phase 4 Step: Temporal Pattern Mining ===")
    phase_map = {}
    cluster_narratives = narrative_data.get("cluster_narratives", []) if isinstance(narrative_data, dict) else []
    for n in (narrative_data.get("entity_narratives", []) if isinstance(narrative_data, dict) else []):
        if n.get("entity"):
            phase_map[n["entity"]] = n.get("phase", "stable")
    result = temporal_pipeline(df, phase_map)
    atomic_write_json(os.path.join(path_for("output_dir"), "temporal_patterns.json"), result)
    logger.info("Temporal: %d velocities, %d anomalies, %d bursts, %d transitions",
                result.get("summary", {}).get("total_entities_tracked", 0),
                result.get("summary", {}).get("total_anomalies", 0),
                result.get("summary", {}).get("total_bursts", 0),
                result.get("summary", {}).get("total_phase_transitions", 0))
    return result


def step_briefings(cross_domain_links: list, sector_map: dict, impact_chains: list,
                   agent_result: dict, temporal_result: dict, narrative_data: dict):
    if not get("intelligence.briefings.enabled", True):
        logger.info("Briefings disabled in config")
        return {}
    logger.info("=== Phase 4 Step: Intelligence Briefing Generation ===")
    anomalies = temporal_result.get("anomalies", []) if isinstance(temporal_result, dict) else []
    transitions = temporal_result.get("phase_transitions", []) if isinstance(temporal_result, dict) else []
    narrative_summary = narrative_data.get("summary", {}) if isinstance(narrative_data, dict) else {}
    result = generate_briefing(
        cross_domain_links, sector_map, impact_chains,
        agent_result, anomalies, transitions, narrative_summary,
    )
    atomic_write_json(os.path.join(path_for("output_dir"), "intelligence_briefing.json"), result)
    logger.info("Briefing: %d sectors, %d watch items, %d predictions",
                len(result.get("sector_situations", [])),
                len(result.get("watch_items", [])),
                len(result.get("predictions", [])))
    return result


def step_alerts(cross_domain_links: list, temporal_result: dict):
    if not get("alerts.enabled", True):
        logger.info("Alerts disabled in config")
        return {}
    logger.info("=== Phase 5 Step: Intelligence Alerting ===")
    velocities = temporal_result.get("velocities", []) if isinstance(temporal_result, dict) else []
    bursts = temporal_result.get("bursts", []) if isinstance(temporal_result, dict) else []
    transitions = temporal_result.get("phase_transitions", []) if isinstance(temporal_result, dict) else []
    result = alerting_pipeline(cross_domain_links, velocities, bursts, transitions)
    atomic_write_json(os.path.join(path_for("output_dir"), "alerts.json"), result)
    alerts = result.get("alerts", [])
    # WebSocket broadcast for alerts
    if alerts:
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            from dashboard.backend.ws import broadcast_alert
            for alert in alerts[:5]:
                loop.run_until_complete(broadcast_alert(alert))
            loop.close()
        except Exception:
            pass
    logger.info("Alerts: %d total (%d high severity)",
                result.get("summary", {}).get("total_alerts", 0),
                result.get("summary", {}).get("high_severity", 0))
    return result


def step_export():
    logger.info("=== Phase 5 Step: Export ===")
    try:
        from dashboard.backend.exporter import export_json, export_csv, export_markdown
        export_dir = path_for("export.json_dir") or os.path.join(path_for("output_dir"), "exports")
        os.makedirs(export_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_json(os.path.join(export_dir, f"intelligence_export_{ts}.json"))
        export_csv(os.path.join(export_dir, f"relationships_{ts}.csv"))
        export_markdown(os.path.join(export_dir, f"briefing_{ts}.md"))
        logger.info("Exports written to %s", export_dir)
    except Exception as e:
        logger.warning("Export step failed: %s", e)


def step_neo4j(sector_map: dict, cross_domain_links: list, impact_chains: list):
    if not get("neo4j.enabled", False):
        logger.info("Neo4j disabled in config")
        return
    logger.info("=== Phase 5 Step: Neo4j Graph Sync ===")
    try:
        from vector_store.neo4j_store import Neo4jStore
        store = Neo4jStore(
            uri=get("neo4j.uri", "bolt://localhost:7687"),
            user=get("neo4j.user", "neo4j"),
            password=get("neo4j.password", "password"),
        )
        if store.enabled:
            store.store_sector_map(sector_map)
            store.store_cross_domain_links(cross_domain_links)
            store.store_impact_chains(impact_chains)
            stats = store.get_statistics()
            logger.info("Neo4j sync complete: %d entities, %d rels", stats["entities"], stats["relationships"])
        store.close()
    except Exception as e:
        logger.warning("Neo4j sync failed: %s", e)


def step_vector_index(df: pd.DataFrame):
    logger.info("=== Intelligence Step 10: Semantic Search Indexing ===")
    try:
        from vector_store.chroma_store import index_articles, get_collection_stats
        count = index_articles(df)
        stats = get_collection_stats()
        logger.info("Vector DB: %d articles indexed", stats.get("count", 0))
    except ImportError:
        logger.warning("chromadb not installed, skipping vector indexing")


def run_pipeline(steps: list = None):
    data_mgr = DataManager()
    if steps is None:
        steps = [
            "scrape", "rss", "dedup", "fetch", "analyze",
            "entity_graph", "cross_domain", "causal", "narratives", "signals",
            "multi_agent", "temporal", "briefings", "alerts", "export", "neo4j", "vector_index",
        ]

    df = pd.DataFrame()
    cross_domain_result = {}
    narrative_result = {}
    temporal_result = {}
    agent_result = {}
    briefing_result = {}
    causal_result = {}

    if "scrape" in steps:
        df = step_scrape(data_mgr)
    if "rss" in steps:
        df = step_scrape_rss(data_mgr)
    if "dedup" in steps and not df.empty:
        df = step_dedup(df, data_mgr)
    elif "dedup" in steps and df.empty:
        df = data_mgr.load_raw()
    if "fetch" in steps and not df.empty:
        df = step_fetch_details(df, data_mgr)
    elif "fetch" in steps and df.empty:
        df = data_mgr.load_raw()
    if "analyze" in steps and not df.empty:
        df = step_analyze(df, data_mgr)
    elif "analyze" in steps:
        df = data_mgr.load_analyzed()
    if "entity_graph" in steps and not df.empty:
        step_entity_graph(df)
    if "cross_domain" in steps and not df.empty:
        cross_domain_result = step_cross_domain(df) or {}
    if "causal" in steps and not df.empty:
        sector_map = cross_domain_result.get("sector_map", {})
        links = cross_domain_result.get("cross_domain_links", [])
        entity_pairs = [(l["source_entity"], l["target_entity"], l) for l in links[:50]]
        causal_result = step_causal(df, sector_map, entity_pairs)
    if "narratives" in steps and not df.empty:
        narrative_result = step_narratives(df) or {}
    if "signals" in steps and not df.empty:
        step_signals(df)
    if "multi_agent" in steps:
        links = cross_domain_result.get("cross_domain_links", [])
        chains = cross_domain_result.get("impact_chains", [])
        agent_result = step_multi_agent(links, chains)
    if "temporal" in steps and not df.empty:
        temporal_result = step_temporal(df, narrative_result)
    if "briefings" in steps:
        links = cross_domain_result.get("cross_domain_links", [])
        sector_map = cross_domain_result.get("sector_map", {})
        chains = cross_domain_result.get("impact_chains", [])
        briefing_result = step_briefings(links, sector_map, chains, agent_result, temporal_result, narrative_result)
    if "alerts" in steps:
        links = cross_domain_result.get("cross_domain_links", [])
        step_alerts(links, temporal_result)
    if "export" in steps:
        step_export()
    if "neo4j" in steps:
        sector_map = cross_domain_result.get("sector_map", {})
        links = cross_domain_result.get("cross_domain_links", [])
        chains = cross_domain_result.get("impact_chains", [])
        step_neo4j(sector_map, links, chains)
    if "vector_index" in steps and not df.empty:
        step_vector_index(df)

    logger.info("=== Pipeline complete ===")
    return cross_domain_result, narrative_result, temporal_result, agent_result, briefing_result, causal_result


if __name__ == "__main__":
    setup_logging()
    init_gpu()
    run_pipeline()
