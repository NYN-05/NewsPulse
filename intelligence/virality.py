import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict

logger = logging.getLogger(__name__)


def compute_virality_score(row: pd.Series) -> float:
    score = 0.0
    weights = {
        "sentiment_intensity": 0.20,
        "sensationalism": 0.25,
        "entity_density": 0.10,
        "source_authority": 0.20,
        "subjectivity": 0.25,
    }

    compound = row.get("compound", 0)
    if isinstance(compound, (int, float)):
        score += weights["sentiment_intensity"] * min(abs(compound) * 2, 1.0)

    sens = row.get("sensationalism_score", 0)
    if isinstance(sens, (int, float)):
        score += weights["sensationalism"] * min(sens * 5, 1.0)

    subj = row.get("subjectivity", 0)
    if isinstance(subj, (int, float)):
        score += weights["subjectivity"] * subj

    entities_str = row.get("entities", "{}")
    if isinstance(entities_str, str):
        try:
            entities = json.loads(entities_str)
            total = sum(len(v) for v in entities.values())
            score += weights["entity_density"] * min(total / 10, 1.0)
        except (json.JSONDecodeError, TypeError):
            pass

    source = str(row.get("source", ""))
    authority = _source_authority_score(source)
    score += weights["source_authority"] * authority

    clickbait = row.get("clickbait_score", 0)
    if isinstance(clickbait, (int, float)):
        score += 0.10 * min(clickbait, 1.0)

    score = min(max(score, 0), 1)
    return round(score, 4)


def _source_authority_score(source: str) -> float:
    high_authority = {"reuters", "bbc", "associated press", "ap", "cnn", "the guardian",
                      "ny times", "new york times", "washington post", "wall street journal",
                      "bloomberg", "financial times", "npr", "forbes"}
    medium_authority = {"times of india", "the hindu", "hindustan times", "indian express",
                        "ndtv", "india today", "bbc india", "al jazeera", "abc news",
                        "nbc news", "cbs news", "sky news", "cnbc", "economist"}

    source_lower = source.lower().strip()
    for name in high_authority:
        if name in source_lower:
            return 1.0
    for name in medium_authority:
        if name in source_lower:
            return 0.6
    return 0.3


def predict_virality(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["virality_score"] = df.apply(compute_virality_score, axis=1)
    viral_count = (df["virality_score"] >= 0.6).sum()
    logger.info("Virality: %d/%d articles above threshold (>=0.6)", viral_count, len(df))
    return df
