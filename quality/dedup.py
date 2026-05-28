import re
import logging
import hashlib
import numpy as np
import pandas as pd
from typing import List, Tuple
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def canonicalize_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    url = url.strip().rstrip("/")
    url = re.sub(r"\?utm_[^&]+(&|$)", "", url)
    url = re.sub(r"\?fbclid=[^&]+(&|$)", "", url)
    url = re.sub(r"\?ref=[^&]+(&|$)", "", url)
    url = re.sub(r"\?source=[^&]+(&|$)", "", url)
    url = re.sub(r"\?amp;?", "", url)
    url = re.sub(r"\?amp$", "", url)
    url = re.sub(r"(\?|&)_[^=&]+=[^&]+", "", url)
    url = url.rstrip("?&")
    return url


def normalize_title(title: str) -> str:
    if not isinstance(title, str):
        return ""
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\b(the|a|an|in|of|to|for|on|at|by|with|from|is|are|was|were)\b", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def fuzzy_hash(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    tokens = sorted(set(cleaned.split()))
    return hashlib.md5(" ".join(tokens).encode()).hexdigest()


@lru_cache(maxsize=1)
def _get_vectorizer():
    return TfidfVectorizer(
        max_features=5000,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )


def _compute_similarity_matrix(texts: List[str]) -> np.ndarray:
    vec = _get_vectorizer()
    tfidf = vec.fit_transform(texts)
    return cosine_similarity(tfidf)


def deduplicate_semantic(
    df: pd.DataFrame,
    title_col: str = "title",
    text_col: str = "text",
    threshold: float = 0.85,
) -> pd.DataFrame:
    if df.empty:
        return df

    texts = df[text_col].fillna("").tolist() if text_col in df.columns else df[title_col].fillna("").tolist()
    titles = df[title_col].fillna("").tolist()

    n = len(texts)
    if n < 2:
        return df

    logger.info("Semantic dedup: %d articles, threshold=%.2f", n, threshold)
    sim_matrix = _compute_similarity_matrix(texts)

    keep = [True] * n
    dup_groups = []

    for i in range(n):
        if not keep[i]:
            continue
        group = [i]
        for j in range(i + 1, n):
            if not keep[j]:
                continue
            if sim_matrix[i][j] >= threshold:
                keep[j] = False
                group.append(j)
        if len(group) > 1:
            dup_groups.append(group)

    if dup_groups:
        logger.info("Found %d duplicate groups (%d articles total)", len(dup_groups), sum(len(g) for g in dup_groups))
        for g in dup_groups:
            kept_title = titles[g[0]]
            for dup_idx in g[1:]:
                logger.debug("  Duplicate: '%s' ~ '%s'", titles[dup_idx][:60], kept_title[:60])

    result = df[keep].reset_index(drop=True).copy()
    logger.info("Dedup: %d -> %d (removed %d)", n, len(result), n - len(result))
    return result


def deduplicate_exact(df: pd.DataFrame) -> pd.DataFrame:
    n_before = len(df)
    df = df.drop_duplicates(subset=["title"], keep="first").reset_index(drop=True)
    n_removed = n_before - len(df)
    if n_removed > 0:
        logger.info("Exact dedup removed %d duplicate titles", n_removed)
    return df


def deduplicate_by_fuzzy_hash(df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
    if df.empty or text_col not in df.columns:
        return df
    df = df.copy()
    df["_fuzzy_hash"] = df[text_col].fillna("").apply(fuzzy_hash)
    n_before = len(df)
    df = df.drop_duplicates(subset=["_fuzzy_hash"], keep="first").reset_index(drop=True)
    df = df.drop(columns=["_fuzzy_hash"])
    n_removed = n_before - len(df)
    if n_removed > 0:
        logger.info("Fuzzy hash dedup removed %d", n_removed)
    return df
