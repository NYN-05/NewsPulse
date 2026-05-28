#!/usr/bin/env python3
"""
News Analytics Pipeline - Production Grade

Orchestrates: scraping -> detail fetching -> NLP analysis -> clustering -> trends -> export
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
    else:
        df = data_mgr.load_raw()
    return df


def step_fetch_details(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 2: Fetching article details ===")
    if "full_text" not in df.columns:
        df["full_text"] = ""
        df["full_text_fetched_at"] = ""
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

    # Vectorized text cleaning
    to_analyze["title"] = to_analyze["title"].apply(clean_text)
    to_analyze["description"] = to_analyze["description"].apply(clean_text)

    # Category extraction
    cats = to_analyze["title"].apply(extract_category)
    to_analyze["category"] = cats.apply(lambda x: x[0])
    to_analyze["clean_title"] = cats.apply(lambda x: x[1])

    # Combined text field
    to_analyze["text"] = to_analyze["clean_title"].fillna("") + ". " + to_analyze["description"].fillna("")

    rows_before = len(to_analyze)
    to_analyze = to_analyze[to_analyze["text"].str.len() > 20]
    if rows_before - len(to_analyze) > 0:
        logger.info("Filtered out %d with insufficient text content", rows_before - len(to_analyze))

    # Sensationalism
    to_analyze["sensationalism_score"] = to_analyze["text"].apply(detect_sensationalism)

    # Sentiment (GPU batch if available, else CPU)
    sent_results = analyze_sentiment_batch(to_analyze["text"].tolist())
    sent_df = pd.DataFrame.from_records(sent_results)
    to_analyze = pd.concat([to_analyze, sent_df], axis=1)
    pos_thresh = get("nlp.sentiment_threshold_positive", 0.35)
    neg_thresh = get("nlp.sentiment_threshold_negative", -0.35)
    to_analyze["sentiment"] = to_analyze["compound"].apply(
        lambda c: label_sentiment(c, pos_thresh, neg_thresh)
    )
    to_analyze["subjectivity"] = to_analyze.apply(
        lambda r: compute_subjectivity(r["compound"], r["neu"]), axis=1
    )
    to_analyze["analyzed_at"] = datetime.now().isoformat()

    # Summaries (GPU batch if available)
    logger.info("Generating summaries...")
    summary_sources = to_analyze.apply(
        lambda r: str(r.get("full_text", "")) if len(str(r.get("full_text", ""))) > len(str(r.get("text", "")))
        else str(r.get("text", "")),
        axis=1,
    )
    to_analyze["summary"] = summarize_batch(summary_sources.tolist())

    # Named entities (GPU batch if available)
    logger.info("Extracting named entities...")
    to_analyze["entities"] = extract_entities_batch(to_analyze["text"].tolist())

    # Merge with old
    df_result = pd.concat([old_analyzed, to_analyze], ignore_index=True) if not old_analyzed.empty else to_analyze
    data_mgr.save_analyzed(df_result)

    logger.info("Analyzed %d new articles (%d total)", len(to_analyze), len(df_result))
    return df_result


def step_cluster(df: pd.DataFrame, data_mgr: DataManager) -> pd.DataFrame:
    logger.info("=== Step 4: Topic Clustering ===")
    df = cluster_articles(df)
    data_mgr.save_analyzed(df)
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

    if steps is None:
        steps = ["scrape", "rss", "fetch", "analyze", "cluster", "trends", "compare", "track"]

    df = pd.DataFrame()

    if "scrape" in steps:
        df = step_scrape(data_mgr)

    if "rss" in steps:
        df = step_scrape_rss(data_mgr)

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

    if "track" in steps and not df.empty:
        step_update_tracking(df)

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    setup_logging()
    init_gpu()
    ensure_nltk_data()
    run_pipeline()
