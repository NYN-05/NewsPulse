import re
import logging
import pandas as pd
from collections import Counter, defaultdict
from config.settings import get

logger = logging.getLogger(__name__)


def compute_trends(df: pd.DataFrame) -> dict:
    if df.empty:
        logger.warning("No data for trend analysis")
        return {}

    time_col = _resolve_time_col(df)
    if time_col is None:
        logger.warning("No timestamp column found")
        return {}

    parsed_dates = pd.to_datetime(df[time_col], utc=True, errors="coerce")
    invalid = parsed_dates.isna().sum()
    if invalid > 0:
        logger.warning("%d rows have invalid timestamps in '%s'", invalid, time_col)
    df["date"] = parsed_dates.dt.date
    df = df.dropna(subset=["date"]).sort_values("date")

    stop_words = set(get("trending.stop_words", []))
    daily_keywords = defaultdict(Counter)

    for _, row in df.iterrows():
        text = str(row.get("text", "") or "")
        if not text:
            continue
        words = [
            w.lower() for w in re.findall(r"\w+", text)
            if len(w) > 3 and w.lower() not in stop_words
        ]
        daily_keywords[row["date"]].update(words)

    all_words = Counter()
    for c in daily_keywords.values():
        all_words += c
    top_overall = all_words.most_common(get("trending.top_keywords", 15))

    result = {
        "top_keywords": top_overall,
        "daily_keywords": {str(k): dict(v) for k, v in daily_keywords.items()},
        "rising_keywords": {},
    }

    dates = sorted(daily_keywords.keys())
    window = get("trending.rising_window_days", 7)
    if len(dates) > window:
        recent = dates[-window:]
        older = dates[:-window]
        recent_words = Counter()
        older_words = Counter()
        for d in recent:
            recent_words += daily_keywords[d]
        for d in older:
            older_words += daily_keywords[d]

        rising = {}
        min_mentions = get("trending.rising_min_mentions", 2)
        min_pct = get("trending.rising_min_pct", 50.0)
        for word, count in recent_words.items():
            old_count = older_words.get(word, 0)
            if old_count < min_mentions and count >= min_mentions:
                rising[word] = count
            elif old_count >= min_mentions:
                rise_pct = (count - old_count) / old_count * 100
                if rise_pct > min_pct:
                    rising[word] = round(rise_pct, 1)
        result["rising_keywords"] = rising

    return result


def _resolve_time_col(df) -> str:
    for col in ["published", "scraped_at", "analyzed_at", "full_text_fetched_at"]:
        if col in df.columns and df[col].notna().sum() > len(df) * 0.5:
            return col
    for col in ["published", "scraped_at", "analyzed_at", "full_text_fetched_at"]:
        if col in df.columns:
            return col
    return None
