import logging
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from scraper.client import fetch
from config.settings import get

logger = logging.getLogger(__name__)

SOURCES = [
    {
        "name": "Times of India",
        "url": "https://timesofindia.indiatimes.com",
        "selectors": {
            "card": ["a.VXZ9M"],
            "title": [".Kt6Pm"],
            "desc": [".hEoJ3"],
            "img": [".Ik2M6 img"],
        },
        "detail_sel": ["._s30J", ".article-text", '[itemprop="articleBody"]', ".Normal"],
    },
    {
        "name": "Hindustan Times",
        "url": "https://www.hindustantimes.com",
        "selectors": {
            "card": ["figure.htStoryCard a", "a.story-link", "h3 a", "div.story-link a"],
            "title": ["h3", "h2", ".headline"],
            "desc": ["p", ".sortDec", ".description"],
            "img": ["img"],
        },
        "detail_sel": [".storyDetail", ".articleBody", '[itemprop="articleBody"]', "article p"],
    },
    {
        "name": "Indian Express",
        "url": "https://indianexpress.com",
        "selectors": {
            "card": ["div.articles a", "h2 a", "div.title a", "a.Item_link"],
            "title": ["h2", "div.title", "h3"],
            "desc": ["p", ".description"],
            "img": ["img"],
        },
        "detail_sel": [".story-details", "article", ".full-details", '[itemprop="articleBody"]'],
    },
    {
        "name": "NDTV",
        "url": "https://www.ndtv.com",
        "selectors": {
            "card": ["div.news_item a", "div.lisingNews a", "h2 a", "a.item-title"],
            "title": ["h2", "div.news_Itm h2", "div.lisingNews h2"],
            "desc": ["div.news_Itm p", "div.lisingNews p", "p"],
            "img": ["div.news_Itm img", "div.lisingNews img", "img"],
        },
        "detail_sel": [".story-content", "article", ".content-area", '[itemprop="articleBody"]'],
    },
]


def scrape_source(source_cfg: dict) -> list:
    name = source_cfg["name"]
    url = source_cfg["url"]
    sels = source_cfg["selectors"]
    logger.info("Scraping %s...", name)

    try:
        resp = fetch(url)
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", name, e)
        return []

    cards = []
    for sel in sels["card"]:
        cards = soup.select(sel)
        if cards:
            break

    articles = []
    seen_titles = set()

    for card in cards[:get("scraper.max_articles_per_source", 50)]:
        link = ""
        if card.name == "a" and card.get("href"):
            link = card["href"].strip()
            if link.startswith("/"):
                link = url.rstrip("/") + link
            parent = card.parent
        else:
            link_el = card if card.name == "a" else card.find("a")
            if link_el and link_el.get("href"):
                link = link_el["href"].strip()
                if link.startswith("/"):
                    link = url.rstrip("/") + link
            parent = card

        title = None
        for sel in sels["title"]:
            el = card.select_one(sel) or (parent.select_one(sel) if parent != card else None)
            if el:
                t = el.get_text(strip=True)
                if len(t) > 15:
                    title = t
                    break
        if not title:
            t = card.get_text(strip=True)
            if len(t) > 20:
                title = t
        if not title or title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())

        desc = None
        for sel in sels["desc"]:
            el = card.select_one(sel) or (parent.select_one(sel) if parent != card else None)
            if el:
                d = el.get_text(strip=True)
                if len(d) > 10 and d != title:
                    desc = d
                    break

        img = None
        for sel in sels["img"]:
            el = card.select_one(sel) or (parent.select_one(sel) if parent != card else None)
            if el:
                img = el.get("data-src") or el.get("src") or None
                if img and img.startswith("/"):
                    img = url.rstrip("/") + img
                if img:
                    break

        articles.append({
            "source": name,
            "title": title,
            "description": desc or "",
            "link": link,
            "image": img or "",
            "published": "",
            "scraped_at": datetime.now().isoformat(),
        })

    logger.info("  %s: %d articles", name, len(articles))
    return articles


def scrape_all_sources() -> list:
    all_articles = []
    with ThreadPoolExecutor(max_workers=get("scraper.max_workers", 8)) as executor:
        futures = {executor.submit(scrape_source, src): src for src in SOURCES}
        for future in as_completed(futures):
            try:
                result = future.result()
                all_articles.extend(result)
            except Exception as e:
                logger.error("Scraping failed: %s", e)
    return all_articles


def fetch_article_body(url: str, detail_selectors: list) -> str:
    try:
        resp = fetch(url)
        soup = BeautifulSoup(resp.text, "lxml")
        text = ""
        for sel in detail_selectors:
            els = soup.select(sel)
            if els:
                paragraphs = [el.get_text(strip=True) for el in els if len(el.get_text(strip=True)) > 20]
                if paragraphs:
                    text = " ".join(paragraphs)
                    break
        if not text:
            paragraphs = [p.get_text(strip=True) for p in soup.select("p") if len(p.get_text(strip=True)) > 30]
            text = " ".join(paragraphs[:30])
        return text
    except Exception as e:
        logger.warning("Detail fetch failed for %s: %s", url[:60], e)
        return ""


def fetch_all_details(df) -> list:
    mask = df["full_text"].fillna("").str.len() < 100 if "full_text" in df.columns else pd.Series([True] * len(df))
    indices = df[mask].index.tolist()
    logger.info("Fetching full text for %d articles...", len(indices))

    def _fetch(idx):
        row = df.loc[idx]
        source = row.get("source", "")
        cfg = next((s for s in SOURCES if s["name"] == source), SOURCES[0])
        link = row.get("link", "")
        if not link:
            return idx, row.get("full_text", "")
        body = fetch_article_body(link, cfg.get("detail_sel", []))
        return idx, body

    updated = {}
    with ThreadPoolExecutor(max_workers=get("scraper.max_workers", 8)) as executor:
        futures = {executor.submit(_fetch, idx): idx for idx in indices}
        for future in as_completed(futures):
            try:
                idx, body = future.result()
                updated[idx] = body
            except Exception as e:
                logger.error("Detail fetch error: %s", e)

    for idx, body in updated.items():
        df.at[idx, "full_text"] = body
        df.at[idx, "full_text_fetched_at"] = datetime.now().isoformat()

    logger.info("Full text fetched for %d articles", len(updated))
    return df
