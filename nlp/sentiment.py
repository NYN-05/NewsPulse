import logging
import numpy as np
from functools import lru_cache
from typing import List, Dict

logger = logging.getLogger(__name__)

_sia = None
_gpu_pipeline = None


def _get_sia():
    global _sia
    if _sia is None:
        from nltk.sentiment import SentimentIntensityAnalyzer
        _sia = SentimentIntensityAnalyzer()
    return _sia


def _get_gpu_sentiment():
    global _gpu_pipeline
    if _gpu_pipeline is not None:
        return _gpu_pipeline
    from compute.gpu_manager import GPUManager, is_cuda
    if is_cuda():
        mgr = GPUManager()
        _gpu_pipeline = mgr.get_pipeline("sentiment")
    return _gpu_pipeline


@lru_cache(maxsize=4096)
def _cached_sentiment(text: str):
    sia = _get_sia()
    return sia.polarity_scores(text)


def analyze_sentiment(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    return _cached_sentiment(text)


def analyze_sentiment_batch(texts: List[str]) -> List[Dict]:
    pipe = _get_gpu_sentiment()
    if pipe is None:
        return [analyze_sentiment(t) for t in texts]
    results = []
    valid_texts = [t for t in texts if isinstance(t, str) and t.strip()]
    if not valid_texts:
        return [{"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}] * len(texts)
    try:
        gpu_results = pipe(valid_texts, batch_size=64, truncation=True)
        idx = 0
        for t in texts:
            if isinstance(t, str) and t.strip():
                r = gpu_results[idx]
                label = r["label"].lower()
                compound = r["score"] if label == "positive" else -r["score"] if label == "negative" else 0.0
                results.append({
                    "neg": max(0, -min(compound, 0)),
                    "neu": max(0, 1 - abs(compound)),
                    "pos": max(0, compound),
                    "compound": compound,
                })
                idx += 1
            else:
                results.append({"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0})
    except Exception as e:
        logger.warning("GPU sentiment failed (%s), falling back to CPU", e)
        return [analyze_sentiment(t) for t in texts]
    return results


def label_sentiment(compound: float, pos_threshold: float = 0.35, neg_threshold: float = -0.35) -> str:
    if compound >= pos_threshold:
        return "positive"
    elif compound <= neg_threshold:
        return "negative"
    return "neutral"


def compute_subjectivity(compound: float, neu: float) -> float:
    return abs(compound) * (1 - neu) if neu < 1 else 0.0
