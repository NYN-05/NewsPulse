import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)


_STOP_TERMS = {"and", "or", "the", "a", "an", "in", "on", "at", "for", "to", "of", "by", "with",
               "from", "about", "last", "this", "that", "these", "those", "week", "month", "day",
               "year", "today", "yesterday", "tomorrow"}


def _parse_nl_query(query: str) -> Dict:
    q = query.lower().strip()
    filters = {"sentiment": None, "source": None, "category": None, "entity": None, "days": 7}

    if "positive" in q or "good" in q:
        filters["sentiment"] = "positive"
    elif "negative" in q or "bad" in q:
        filters["sentiment"] = "negative"
    elif "neutral" in q:
        filters["sentiment"] = "neutral"

    for prefix in ["about ", "regarding ", "related to ", "on "]:
        if prefix in q:
            after_text = q.split(prefix, 1)[1].strip()
            words = after_text.split()
            entity_parts = []
            for w in words:
                wc = w.strip(".,!?\"'():;[]{}")
                if wc in _STOP_TERMS:
                    break
                entity_parts.append(wc)
            if entity_parts:
                filters["entity"] = " ".join(entity_parts)

    import re
    numbers = re.findall(r"\d+", q)
    if numbers:
        filters["days"] = int(numbers[0])

    source_keywords = {"times of india": "times of india", "bbc": "bbc", "cnn": "cnn",
                       "the hindu": "the hindu", "ndtv": "ndtv", "reuters": "reuters",
                       "guardian": "guardian", "ny times": "ny times"}
    for key, val in source_keywords.items():
        if key in q:
            filters["source"] = val
            break

    return filters


def query_articles(df: pd.DataFrame, query: str) -> List[Dict]:
    filters = _parse_nl_query(query)
    if df.empty:
        return [{"answer": "No data available. Run the pipeline first.", "articles": []}]

    result = df.copy()
    cutoff = datetime.now() - timedelta(days=filters["days"])
    time_col = "published" if "published" in result.columns and result["published"].notna().sum() > 0 else "scraped_at"
    if time_col in result.columns:
        result["_ts"] = pd.to_datetime(result[time_col], errors="coerce")
        result = result[result["_ts"] >= cutoff]

    if filters["sentiment"]:
        if "sentiment" in result.columns:
            result = result[result["sentiment"] == filters["sentiment"]]

    if filters["source"]:
        if "source" in result.columns:
            result = result[result["source"].str.lower().str.contains(filters["source"], na=False)]

    if filters["entity"]:
        if "entities" in result.columns:
            result = result[result["entities"].apply(
                lambda e: isinstance(e, str) and filters["entity"].lower() in e.lower()
            )]

    if filters["category"]:
        if "category" in result.columns:
            result = result[result["category"].str.lower() == filters["category"].lower()]

    result = result.sort_values("_ts", ascending=False) if "_ts" in result.columns else result
    articles = result.head(10).to_dict("records")

    summary = _summarize_results(articles, filters)
    formatted = []
    for a in articles:
        formatted.append({
            "title": a.get("title", ""),
            "source": a.get("source", ""),
            "sentiment": a.get("sentiment", ""),
            "published": str(a.get("published", "") or a.get("scraped_at", "")),
            "link": a.get("link", ""),
            "summary": a.get("summary", "")[:200],
            "entities": a.get("entities", "{}"),
            "virality": a.get("virality_score", "N/A"),
        })

    return [{"answer": summary, "articles": formatted, "query_filters": filters, "total": len(articles)}]


def _summarize_results(articles: List[Dict], filters: Dict) -> str:
    if not articles:
        return f"No articles found matching your query."

    n = len(articles)
    sentiment = filters["sentiment"] or "any"
    source = filters["source"] or "all sources"
    entity = filters["entity"] or ""
    days = filters["days"]

    sources = set()
    for a in articles:
        if a.get("source"):
            sources.add(a["source"])

    parts = [f"Found {n} articles from the last {days} days with {sentiment} sentiment"]
    if entity:
        parts.append(f"related to '{entity}'")
    parts.append(f"from {', '.join(list(sources)[:3])}")
    parts.append(".")

    return " ".join(parts)


def ask(query: str, df: pd.DataFrame) -> str:
    results = query_articles(df, query)
    if not results:
        return "No results."
    r = results[0]
    ans = r.get("answer", "")
    articles = r.get("articles", [])[:5]
    if articles:
        ans += "\n\nTop articles:\n"
        for a in articles:
            ans += f"- {a['title']} ({a['source']}, {a['sentiment']})\n"
    return ans
