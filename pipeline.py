#!/usr/bin/env python3
"""
NewsPulse — AI-Powered Cross-Domain Intelligence Discovery Engine

Core pipeline: scrape → analyze → entity graph → cross-domain relationships →
narrative evolution → signal detection → semantic intelligence search indexing

Every step is focused on intelligence quality over feature quantity.
"""

import os
import sys
import json
import logging
from datetime import datetime
import pandas as pd

from config.settings import load_config, get, path_for
from compute.gpu_manager import GPUManager
from storage.manager import DataManager
from scraper.sources import scrape_all_sources, fetch_all_details
from scraper.rss_scraper import scrape_all_rss
from nlp.preprocess import clean_text, extract_category
from nlp.entities import extract_entities_batch
from quality.dedup import deduplicate_semantic, deduplicate_exact
from quality.boilerplate import remove_boilerplate, extract_clean_title
from intelligence.entity_graph import build_entity_graph
from intelligence.relationships import cross_domain_pipeline
from intelligence.narratives import narrative_pipeline
from intelligence.signals import signals_pipeline
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
        df = deduplicate_semantic(df, threshold=get("quality.dedup_threshold", 0.85))
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
    graph_path = path_for("output_dir") + "/entity_graph.json"
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    with open(graph_path, "w") as f:
        json.dump(graph, f, indent=2)


def step_cross_domain(df: pd.DataFrame):
    logger.info("=== Intelligence Step 7: Cross-Domain Relationship Discovery ===")
    result = cross_domain_pipeline(df, verify_llm=False)
    s = result.get("summary", {})
    logger.info("Cross-domain: %d links, %d chains across %d entities",
                s.get("total_cross_domain_links", 0), s.get("total_impact_chains", 0),
                s.get("total_entities_mapped", 0))


def step_narratives(df: pd.DataFrame):
    logger.info("=== Intelligence Step 8: Narrative Evolution Tracking ===")
    result = narrative_pipeline(df)
    s = result.get("summary", {})
    logger.info("Narratives: %d emerging, %d disappearing, %d mutations",
                s.get("emerging_count", 0), s.get("disappearing_count", 0), s.get("total_mutations", 0))


def step_signals(df: pd.DataFrame):
    logger.info("=== Intelligence Step 9: Signal Detection ===")
    result = signals_pipeline(df)
    s = result.get("summary", {})
    logger.info("Signals: %d total (highest score: %.1f)", s.get("total_signals", 0), s.get("highest_score", 0))


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
        steps = ["scrape", "rss", "dedup", "fetch", "analyze",
                 "entity_graph", "cross_domain", "narratives", "signals", "vector_index"]

    df = pd.DataFrame()

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
        step_cross_domain(df)
    if "narratives" in steps and not df.empty:
        step_narratives(df)
    if "signals" in steps and not df.empty:
        step_signals(df)
    if "vector_index" in steps and not df.empty:
        step_vector_index(df)

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    setup_logging()
    init_gpu()
    run_pipeline()
