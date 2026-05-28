import logging
import pandas as pd

logger = logging.getLogger(__name__)


def _resolve_time_col(df) -> str:
    for col in ["published", "scraped_at", "analyzed_at", "full_text_fetched_at"]:
        if col in df.columns and df[col].notna().sum() > len(df) * 0.5:
            return col
    for col in ["published", "scraped_at", "analyzed_at", "full_text_fetched_at"]:
        if col in df.columns:
            return col
    return None


def _parse_time_column(df, col: str):
    parsed = pd.to_datetime(df[col], utc=True, errors="coerce")
    invalid = parsed.isna().sum()
    if invalid > 0:
        logger.warning("%d rows have invalid timestamps in '%s'", invalid, col)
    return parsed


def historical_comparison(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 10:
        logger.warning("Too few articles for comparison (< 10)")
        return {}

    time_col = _resolve_time_col(df)
    if time_col is None:
        logger.warning("No timestamp column for comparison")
        return {}

    df["ts"] = _parse_time_column(df, time_col)
    n_before = len(df)
    df = df.dropna(subset=["ts"])
    n_dropped = n_before - len(df)
    if n_dropped > 0:
        logger.info("Dropped %d rows with invalid timestamps", n_dropped)

    if len(df) < 10:
        logger.warning("Too few valid timestamps for comparison (< 10)")
        return {}

    median_ts = df["ts"].median()
    early = df[df["ts"] <= median_ts]
    late = df[df["ts"] > median_ts]

    if early.empty or late.empty:
        logger.warning("All timestamps fall on one side of median (possible batch import)")
        n_unique = df["ts"].nunique()
        if n_unique <= 1:
            logger.info("Only %d unique timestamp(s) — no temporal spread for comparison", n_unique)
            return {
                "early_period": {"start": pd.NaT, "end": pd.NaT, "count": 0},
                "late_period": {"start": df["ts"].min(), "end": df["ts"].max(), "count": len(df)},
                "sentiment_shift": {},
                "metric_shifts": [],
                "category_shifts": [],
                "note": "single_batch_no_temporal_spread",
            }

    result = {
        "early_period": {"start": early["ts"].min(), "end": early["ts"].max(), "count": len(early)},
        "late_period": {"start": late["ts"].min(), "end": late["ts"].max(), "count": len(late)},
        "sentiment_shift": {},
        "metric_shifts": [],
        "category_shifts": [],
    }

    result["sentiment_shift"]["early"] = early["sentiment"].value_counts().to_dict() if "sentiment" in early.columns else {}
    result["sentiment_shift"]["late"] = late["sentiment"].value_counts().to_dict() if "sentiment" in late.columns else {}

    for metric in ["compound", "sensationalism_score", "subjectivity"]:
        if metric in df.columns:
            e_mean = early[metric].mean()
            l_mean = late[metric].mean()
            result["metric_shifts"].append({
                "metric": metric,
                "early_mean": round(e_mean, 4),
                "late_mean": round(l_mean, 4),
                "delta": round(l_mean - e_mean, 4),
            })

    if "category" in df.columns:
        early_cats = early["category"].value_counts(normalize=True)
        late_cats = late["category"].value_counts(normalize=True)
        all_cats = set(list(early_cats.index) + list(late_cats.index))
        for cat in sorted(all_cats):
            e_pct = early_cats.get(cat, 0) * 100
            l_pct = late_cats.get(cat, 0) * 100
            delta = l_pct - e_pct
            if abs(delta) > 1:
                result["category_shifts"].append({
                    "category": cat,
                    "early_pct": round(e_pct, 1),
                    "late_pct": round(l_pct, 1),
                    "delta": round(delta, 1),
                })

    return result
