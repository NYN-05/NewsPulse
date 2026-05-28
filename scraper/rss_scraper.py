import re
import logging
import feedparser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from scraper.rss_feeds import RSS_FEEDS
from scraper.client import get_session
from config.settings import get

logger = logging.getLogger(__name__)

MAX_ARTICLES_PER_FEED = 20


def _parse_entry(entry, feed_name: str, source_country: str) -> Optional[dict]:
    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    if not title or not link:
        return None

    description = ""
    raw_desc = entry.get("summary", "") or entry.get("description", "") or entry.get("subtitle", "")
    if raw_desc:
        description = re.sub(r"<[^>]+>", "", raw_desc).strip()
        description = re.sub(r"\s+", " ", description)[:500]

    published = entry.get("published_parsed") or entry.get("updated_parsed")
    published_str = ""
    scraped_at = datetime.now().isoformat()
    if published:
        try:
            published_dt = datetime(*published[:6])
            published_str = published_dt.isoformat()
            scraped_at = published_str
        except Exception:
            pass

    media_content = entry.get("media_content") or []
    image = ""
    if media_content:
        for mc in media_content:
            url = mc.get("url", "")
            if url:
                image = url
                break
    if not image:
        links = entry.get("links", [])
        for lnk in links:
            if lnk.get("type", "").startswith("image"):
                image = lnk.get("href", "")
                break

    return {
        "source": feed_name,
        "title": title,
        "description": description,
        "link": link,
        "image": image,
        "published": published_str,
        "scraped_at": scraped_at,
        "source_country": source_country,
        "full_text": description,
        "full_text_fetched_at": datetime.now().isoformat(),
    }


def scrape_rss_feed(feed_cfg: dict) -> list:
    name = feed_cfg["name"]
    url = feed_cfg["url"]
    country = feed_cfg.get("country", "XX")
    logger.debug("Fetching RSS: %s (%s)", name, url)
    try:
        session = get_session()
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except Exception as e:
        logger.warning("RSS feed failed (%s): %s", name, e)
        return []

    articles = []
    for entry in parsed.entries[:MAX_ARTICLES_PER_FEED]:
        article = _parse_entry(entry, name, country)
        if article:
            articles.append(article)
    return articles


def scrape_all_rss(max_workers: int = None) -> list:
    if max_workers is None:
        max_workers = get("scraper.max_workers", 8)
    seen_urls = {}
    unique_feeds = []
    for feed in RSS_FEEDS:
        url = feed["url"]
        if url not in seen_urls:
            seen_urls[url] = feed["name"]
            unique_feeds.append(feed)
        else:
            logger.debug("Skipping duplicate RSS URL: %s (%s merged into %s)", url, feed["name"], seen_urls[url])
    dup_count = len(RSS_FEEDS) - len(unique_feeds)
    if dup_count > 0:
        logger.info("Deduplicated %d duplicate RSS feed URLs (%d unique)", dup_count, len(unique_feeds))
    all_articles = []
    logger.info("Scraping %d RSS feeds with %d workers...", len(unique_feeds), max_workers)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_rss_feed, feed): feed for feed in unique_feeds}
        for future in as_completed(futures):
            try:
                result = future.result()
                all_articles.extend(result)
            except Exception as e:
                logger.error("RSS scraping error: %s", e)
    logger.info("RSS scraping complete: %d articles", len(all_articles))
    return all_articles
