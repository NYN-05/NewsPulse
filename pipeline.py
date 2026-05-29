#!/usr/bin/env python3
"""
NewsPulse - AI-Powered Cross-Domain Intelligence Discovery Engine

Core pipeline: scrape → analyze → entity graph → cross-domain relationships →
narrative tracking → influence mapping → signal detection → semantic indexing
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime
import pandas as pd

from config.settings import load_config, get, path_for
from compute.gpu_manager import GPUManager
from storage.manager import DataManager
from scraper.sources import scrape_all_sources, fetch_all_details
from scraper.rss_scraper import scrape_all_rss
from nlp.preprocess import clean_text, extract_category, detect_sensationalism
from nlp.sentiment import analyze_sentiment_batch, label_sentiment, compute_subjectivity
from nlp.entities import extract_entities_batch
from nlp.summarization import summarize_batch
from quality.dedup import deduplicate_semantic, deduplicate_exact
from quality.boilerplate import remove_boilerplate, extract_clean_title
from intelligence.entity_graph import build_entity_graph, compute_entity_trends
from intelligence.event_detection import detect_breaking_events
from intelligence.cross_domain import cross_domain_pipeline
from intelligence.narrative_tracker import narrative_pipeline
from intelligence.influence import influence_pipeline
from multilingual.detect import detect_language
from alerts.engine import AlertEngine
from observability.metrics import metrics

logger = logging.getLogger("pipeline")


def setup_logging():
    config = load_config()
    level = getattr(logging, get("logging.level", "INFO").upper(), logging.INFO)
    fmt = get("logging.format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.basicConfig(level=level, format=fmt, stream=sys.stdout)


def init_gpu():
    from compute.gpu_manager import GPUManager, detect_cuda
    detect_cuda()
    _ = GPUManager()
    logger.info("GPU initialized: device=%s", GPUManager().device)


def ensure_nltk_data():
    import nltk
    for res in ("punkt", "vader_lexicon", "averaged_perceptron_tagger", "maxent_ne_chunker", "words"):
        nltk.download(res, quiet=True)


def step_scrape(data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 1: Scraping web sources ===")
    new_articles = scrape_all_sources()
    if new_articles:
        df = data_mgr.merge_new_articles(new_articles)
        logger.info("Web scrape: %d new articles", len(new_articles))
        metrics.record_scrape("web", len(new_articles))
    else:
        df = data_mgr.load_raw()
    logger.info("Total raw articles: %d", len(df))
    return df


def step_scrape_rss(data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 2: Scraping RSS feeds ===")
    new_articles = scrape_all_rss()
    if new_articles:
        df = data_mgr.merge_new_articles(new_articles)
        logger.info("RSS scrape: %d new articles", len(new_articles))
        metrics.record_rss(len(new_articles))
    else:
        df = data_mgr.load_raw()
    return df


def step_dedup(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 3: Deduplication ===")
    n_before = len(df)
    df = deduplicate_exact(df)
    if get("quality.enable_semantic_dedup", True) and len(df) > 10:
        df = deduplicate_semantic(df, threshold=get("quality.dedup_threshold", 0.85))
    data_mgr.save_raw(df)
    logger.info("Dedup: %d -> %d (removed %d)", n_before, len(df), n_before - len(df))
    return df


def step_fetch_details(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 4: Fetching article details ===")
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
    logger.info("=== Step 5: NLP Analysis ===")
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

    logger.info("Raw in: %d | Old analyzed: %d | New candidates: %d", len(df), len(old_analyzed), len(to_analyze))

    to_analyze["title"] = to_analyze["title"].apply(clean_text)
    to_analyze["description"] = to_analyze["description"].apply(clean_text)

    cats = to_analyze["title"].apply(extract_category)
    to_analyze["category"] = cats.apply(lambda x: x[0])
    to_analyze["clean_title"] = cats.apply(lambda x: x[1])
    to_analyze["text"] = to_analyze["clean_title"].fillna("") + ". " + to_analyze["description"].fillna("")

    rows_before = len(to_analyze)
    to_analyze = to_analyze[to_analyze["text"].str.len() > 20]
    if rows_before - len(to_analyze) > 0:
        logger.info("Filtered out %d with insufficient text content", rows_before - len(to_analyze))

    to_analyze["sensationalism_score"] = to_analyze["text"].apply(detect_sensationalism)

    sent_results = analyze_sentiment_batch(to_analyze["text"].tolist())
    sent_df = pd.DataFrame.from_records(sent_results)
    to_analyze = pd.concat([to_analyze, sent_df], axis=1)
    pos_thresh = get("nlp.sentiment_threshold_positive", 0.35)
    neg_thresh = get("nlp.sentiment_threshold_negative", -0.35)
    to_analyze["sentiment"] = to_analyze["compound"].apply(lambda c: label_sentiment(c, pos_thresh, neg_thresh))
    to_analyze["subjectivity"] = to_analyze.apply(lambda r: compute_subjectivity(r["compound"], r["neu"]), axis=1)
    to_analyze["analyzed_at"] = datetime.now().isoformat()

    logger.info("Generating summaries...")
    has_full_text = to_analyze["full_text"].fillna("").str.len() > 300
    to_analyze["summary"] = to_analyze.apply(
        lambda r: str(r.get("full_text", "")) if len(str(r.get("full_text", ""))) > 300
        else str(r.get("text", "")), axis=1)
    if has_full_text.sum() > 0:
        logger.info("GPU summarization for %d articles with full text", has_full_text.sum())
        gpu_texts = to_analyze.loc[has_full_text, "summary"].tolist()
        gpu_summaries = summarize_batch(gpu_texts)
        to_analyze.loc[has_full_text, "summary"] = gpu_summaries
    else:
        logger.info("No articles have full_text > 300 chars, using NLTK extractive")
    logger.info("Summaries complete for %d articles", len(to_analyze))

    logger.info("Extracting named entities...")
    to_analyze["entities"] = extract_entities_batch(to_analyze["text"].tolist())

    logger.info("Detecting languages...")
    to_analyze["language"] = to_analyze["text"].apply(
        lambda t: detect_language(t) if isinstance(t, str) and t.strip() else "unknown"
    )
    non_english = (to_analyze["language"] != "en").sum()
    if non_english > 0:
        logger.info("Non-English articles detected: %d", non_english)

    df_result = pd.concat([old_analyzed, to_analyze], ignore_index=True) if not old_analyzed.empty else to_analyze
    data_mgr.save_analyzed(df_result)

    metrics.record_analyzed(len(to_analyze))
    logger.info("Analyzed %d new articles (%d total)", len(to_analyze), len(df_result))
    return df_result


def step_entity_graph(df: pd.DataFrame):
    logger.info("=== Step 6: Entity Relationship Graph ===")
    graph = build_entity_graph(df, max_age_days=365)
    if "stats" in graph:
        stats = graph["stats"]
        logger.info("Entity graph: %d nodes, %d edges", stats.get("total_nodes", 0), stats.get("total_edges", 0))
    graph_path = path_for("output_dir") + "/entity_graph.json"
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    with open(graph_path, "w") as f:
        json.dump(graph, f, indent=2)
    logger.info("Entity graph saved to %s", graph_path)


def step_entity_trends(df: pd.DataFrame):
    logger.info("=== Step 6a: Entity Trend Analysis ===")
    trends = compute_entity_trends(df)
    if trends:
        logger.info("Entity trends: %d trending entities", len(trends))
    trends_path = path_for("output_dir") + "/entity_trends.json"
    with open(trends_path, "w") as f:
        json.dump(trends, f, indent=2)


def step_breaking_news(df: pd.DataFrame):
    logger.info("=== Step 6b: Signal Detection ===")
    events = detect_breaking_events(df)
    if events:
        logger.info("Breaking events detected: %d", len(events))
    events_path = path_for("output_dir") + "/breaking_events.json"
    with open(events_path, "w") as f:
        json.dump(events, f, indent=2)


def step_cross_domain(df: pd.DataFrame):
    logger.info("=== Step 7: Cross-Domain Relationship Discovery ===")
    result = cross_domain_pipeline(df)
    summary = result.get("summary", {})
    logger.info("Cross-domain: %d links, %d chains across %d entities",
                summary.get("total_cross_domain_links", 0),
                summary.get("total_impact_chains", 0),
                summary.get("total_entities_mapped", 0))


def step_narrative_tracker(df: pd.DataFrame):
    logger.info("=== Step 8: Narrative Evolution Tracking ===")
    result = narrative_pipeline(df)
    summary = result.get("summary", {})
    logger.info("Narratives: %d emerging, %d disappearing, %d mutations across %d entities",
                summary.get("emerging_count", 0),
                summary.get("disappearing_count", 0),
                summary.get("total_mutations", 0),
                summary.get("total_entity_narratives", 0))


def step_influence(df: pd.DataFrame):
    logger.info("=== Step 9: Influence Mapping ===")
    result = influence_pipeline(df)
    summary = result.get("summary", {})
    logger.info("Influence: %d entities scored, %d sources, %d propagation tracks",
                summary.get("total_entities_scored", 0),
                summary.get("total_sources_scored", 0),
                summary.get("total_propagation_tracked", 0))


def step_vector_index(df: pd.DataFrame):
    logger.info("=== Step 10: Vector Database Indexing ===")
    try:
        from vector_store.chroma_store import index_articles, get_collection_stats
        count = index_articles(df)
        stats = get_collection_stats()
        logger.info("Vector DB: %d articles indexed", stats.get("count", 0))
    except ImportError:
        logger.warning("chromadb not installed, skipping vector indexing")


def step_update_tracking(df: pd.DataFrame):
    logger.info("=== Step 11: Article Update Tracking ===")
    log_path = path_for("update_log")
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            log = json.load(f)
    else:
        log = {}

    changes = []
    for _, row in df.iterrows():
        link = row.get("link", "")
        if not link:
            continue
        current_text = str(row.get("title", "")) + str(row.get("description", ""))
        full = row.get("full_text", "")
        if isinstance(full, str) and len(full) > 50:
            current_text += full
        current_hash = hashlib.md5(current_text.encode()).hexdigest()
        prev_hash = log.get(link, {}).get("hash", "")
        if prev_hash and prev_hash != current_hash:
            changes.append(link)
        if link not in log:
            log[link] = {}
        log[link]["hash"] = current_hash
        log[link]["title"] = str(row.get("title", ""))
        log[link]["last_checked"] = datetime.now().isoformat()

    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    if changes:
        logger.info("%d article(s) changed since last check", len(changes))


def step_alerts(df: pd.DataFrame):
    logger.info("=== Step 12: Alerts ===")
    try:
        engine = AlertEngine()
        events_path = path_for("output_dir") + "/breaking_events.json"
        if os.path.exists(events_path):
            with open(events_path) as f:
                events = json.load(f)
            engine.check_breaking_events(events)
        logger.info("Alerts processed")
    except Exception as e:
        logger.warning("Alert step failed: %s", e)


def run_pipeline(steps: list = None):
    data_mgr = DataManager()
    metrics.start_run()

    if steps is None:
        steps = ["scrape", "rss", "dedup", "fetch", "analyze",
                 "entity_graph", "entity_trends", "breaking",
                 "cross_domain", "narratives", "influence",
                 "vector_index", "track", "alerts"]

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
    if "entity_trends" in steps and not df.empty:
        step_entity_trends(df)
    if "breaking" in steps and not df.empty:
        step_breaking_news(df)
    if "cross_domain" in steps and not df.empty:
        step_cross_domain(df)
    if "narratives" in steps and not df.empty:
        step_narrative_tracker(df)
    if "influence" in steps and not df.empty:
        step_influence(df)
    if "vector_index" in steps and not df.empty:
        step_vector_index(df)
    if "track" in steps and not df.empty:
        step_update_tracking(df)
    if "alerts" in steps and not df.empty:
        step_alerts(df)

    metrics.end_run()
    report = metrics.get_report()
    logger.info("=== Pipeline complete (run #%d, total: %d articles, avg duration: %.1fs) ===",
                report["pipeline_runs"], report["total_scraped"], report["avg_duration"])


if __name__ == "__main__":
    setup_logging()
    init_gpu()
    ensure_nltk_data()
    run_pipeline()
