#!/usr/bin/env python3
"""
NewsPulse - AI-Powered Media Intelligence Pipeline

Orchestrates: scraping -> dedup -> detail fetching -> NLP analysis ->
clustering -> intelligence -> vector indexing -> trends -> alerts
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
from scraper.sources import scrape_all_sources, fetch_all_details, SOURCES
from scraper.rss_scraper import scrape_all_rss
from nlp.preprocess import clean_text, extract_category, detect_sensationalism
from nlp.sentiment import analyze_sentiment, analyze_sentiment_batch, label_sentiment, compute_subjectivity
from nlp.entities import extract_entities, extract_entities_batch
from nlp.summarization import extractive_summary, summarize_batch
from analytics.clustering import cluster_articles
from analytics.trending import compute_trends
from analytics.comparison import historical_comparison
from quality.dedup import deduplicate_semantic, deduplicate_exact, canonicalize_url, normalize_title
from quality.boilerplate import remove_boilerplate, extract_clean_title
from intelligence.entity_graph import build_entity_graph, compute_entity_trends
from intelligence.event_detection import detect_breaking_events
from intelligence.virality import predict_virality
from intelligence.bias import analyze_bias, compute_source_reliability
from intelligence.topics import track_topic_evolution
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
    logger.info("=== Step 1b: Scraping RSS feeds ===")
    new_articles = scrape_all_rss()
    if new_articles:
        df = data_mgr.merge_new_articles(new_articles)
        logger.info("RSS scrape: %d new articles", len(new_articles))
        metrics.record_rss(len(new_articles))
    else:
        df = data_mgr.load_raw()
    return df


def step_dedup(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 1c: Semantic Deduplication ===")
    n_before = len(df)
    df = deduplicate_exact(df)
    if get("quality.enable_semantic_dedup", True) and len(df) > 10:
        df = deduplicate_semantic(df, threshold=get("quality.dedup_threshold", 0.85))
    data_mgr.save_raw(df)
    logger.info("Dedup: %d -> %d (removed %d)", n_before, len(df), n_before - len(df))
    return df


def step_fetch_details(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 2: Fetching article details ===")
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
    logger.info("=== Step 3: NLP Analysis ===")
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
    description_na = to_analyze["description"].isna().sum()
    description_empty = (to_analyze["description"].fillna("").str.strip() == "").sum()
    logger.info("Descriptions: %d missing, %d empty", description_na, description_empty)

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

    logger.info("Analyzing bias and clickbait...")
    bias_results = to_analyze["text"].apply(analyze_bias)
    bias_df = pd.DataFrame.from_records(bias_results)
    to_analyze = pd.concat([to_analyze, bias_df], axis=1)

    to_analyze = predict_virality(to_analyze)

    df_result = pd.concat([old_analyzed, to_analyze], ignore_index=True) if not old_analyzed.empty else to_analyze
    data_mgr.save_analyzed(df_result)

    metrics.record_analyzed(len(to_analyze))
    logger.info("Analyzed %d new articles (%d total)", len(to_analyze), len(df_result))
    return df_result


def step_cluster(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 4: Topic Clustering ===")
    df = cluster_articles(df)
    data_mgr.save_analyzed(df)
    metrics.record_clustered(len(df))
    return df


def step_trends(df: pd.DataFrame):
    logger.info("=== Step 5: Trend Detection ===")
    trends = compute_trends(df)
    if trends:
        logger.info("Top keywords: %s", trends.get("top_keywords", [])[:10])
        rising = trends.get("rising_keywords", {})
        if rising:
            logger.info("Rising keywords: %s", dict(list(rising.items())[:10]))


def step_comparison(df: pd.DataFrame):
    logger.info("=== Step 6: Historical Comparison ===")
    comparison = historical_comparison(df)
    if comparison:
        early = comparison["early_period"]
        late = comparison["late_period"]
        logger.info("Early: %s (%d articles)", early["start"].date(), early["count"])
        logger.info("Late: %s (%d articles)", late["start"].date(), late["count"])


def step_entity_graph(df: pd.DataFrame):
    logger.info("=== Step 6b: Entity Relationship Graph ===")
    graph = build_entity_graph(df, max_age_days=365)
    if "stats" in graph:
        stats = graph["stats"]
        logger.info("Entity graph: %d nodes, %d edges", stats.get("total_nodes", 0), stats.get("total_edges", 0))
        top = stats.get("top_entities", [])[:5]
        for e in top:
            logger.info("  Influential: %s (centrality=%.3f)", e["entity"], e["centrality"])
    graph_path = path_for("output_dir") + "/entity_graph.json"
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    with open(graph_path, "w") as f:
        json.dump(graph, f, indent=2)
    logger.info("Entity graph saved to %s", graph_path)


def step_breaking_news(df: pd.DataFrame):
    logger.info("=== Step 6c: Breaking News Detection ===")
    events = detect_breaking_events(df)
    if events:
        logger.info("Breaking events detected: %d", len(events))
        for e in events[:5]:
            kw = e.get("keyword") or e.get("entity", "?")
            logger.info("  %s (score=%.1f, count=%d)", kw, e.get("score", 0), e.get("recent_count", 0))
    events_path = path_for("output_dir") + "/breaking_events.json"
    with open(events_path, "w") as f:
        json.dump(events, f, indent=2)


def step_entity_trends(df: pd.DataFrame):
    logger.info("=== Step 6ba: Entity Trend Analysis ===")
    trends = compute_entity_trends(df)
    if trends:
        logger.info("Entity trends: %d trending entities", len(trends))
        for t in trends[:5]:
            logger.info("  %s (momentum=%d, recent=%d)", t["entity"], t["momentum"], t["recent_mentions"])
    trends_path = path_for("output_dir") + "/entity_trends.json"
    with open(trends_path, "w") as f:
        json.dump(trends, f, indent=2)


def step_topic_evolution(df: pd.DataFrame):
    logger.info("=== Step 6d: Topic Evolution Tracking ===")
    evolution = track_topic_evolution(df)
    if "clusters" in evolution:
        logger.info("Tracking %d clusters over time", len(evolution["clusters"]))
        for c in evolution["clusters"][:3]:
            logger.info("  Cluster %d: %d articles, momentum=%d", c["cluster"], c["total_articles"], c["momentum"])
    evo_path = path_for("output_dir") + "/topic_evolution.json"
    with open(evo_path, "w") as f:
        json.dump(evolution, f, indent=2)


def step_source_reliability(df: pd.DataFrame):
    logger.info("=== Step 6e: Source Reliability Scoring ===")
    reliability = compute_source_reliability(df)
    if reliability:
        logger.info("Source reliability scores:")
        for source, stats in list(reliability.items())[:5]:
            logger.info("  %s: %.1f/100 (%d articles)", source, stats["reliability_score"], stats["total_articles"])
    rel_path = path_for("output_dir") + "/source_reliability.json"
    with open(rel_path, "w") as f:
        json.dump(reliability, f, indent=2)


def step_vector_index(df: pd.DataFrame):
    logger.info("=== Step 6f: Vector Database Indexing ===")
    try:
        from vector_store.chroma_store import index_articles, get_collection_stats
        count = index_articles(df)
        stats = get_collection_stats()
        logger.info("Vector DB: %d articles indexed", stats.get("count", 0))
    except ImportError:
        logger.warning("chromadb not installed, skipping vector indexing")


def step_alerts(df: pd.DataFrame):
    logger.info("=== Step 8: Alerts ===")
    try:
        engine = AlertEngine()
        events_path = path_for("output_dir") + "/breaking_events.json"
        if os.path.exists(events_path):
            with open(events_path) as f:
                events = json.load(f)
            engine.check_breaking_events(events)
        engine.check_virality_alerts(df)
        logger.info("Alerts processed")
    except Exception as e:
        logger.warning("Alert step failed: %s", e)


def step_update_tracking(df: pd.DataFrame):
    logger.info("=== Step 7: Article Update Tracking ===")
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
    else:
        logger.info("No changes detected")


def run_pipeline(steps: list = None):
    data_mgr = DataManager()
    metrics.start_run()

    if steps is None:
        steps = ["scrape", "rss", "dedup", "fetch", "analyze", "cluster",
                 "trends", "compare", "entity_graph", "entity_trends", "breaking",
                 "topics", "reliability", "vector_index", "track", "alerts"]

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

    if "cluster" in steps and not df.empty:
        df = step_cluster(df, data_mgr)
    elif "cluster" in steps:
        df = data_mgr.load_analyzed()

    if "trends" in steps and not df.empty:
        step_trends(df)
    if "compare" in steps and not df.empty:
        step_comparison(df)
    if "entity_graph" in steps and not df.empty:
        step_entity_graph(df)
    if "entity_trends" in steps and not df.empty:
        step_entity_trends(df)
    if "breaking" in steps and not df.empty:
        step_breaking_news(df)
    if "topics" in steps and not df.empty:
        step_topic_evolution(df)
    if "reliability" in steps and not df.empty:
        step_source_reliability(df)
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
