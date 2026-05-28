import logging
import numpy as np
from collections import Counter
from functools import lru_cache
from typing import List

logger = logging.getLogger(__name__)

_gpu_pipeline = None


def _get_gpu_summarizer():
    global _gpu_pipeline
    if _gpu_pipeline is not None:
        return _gpu_pipeline
    from compute.gpu_manager import GPUManager, is_cuda
    if is_cuda():
        try:
            mgr = GPUManager()
            _gpu_pipeline = mgr.get_pipeline("summarization")
        except Exception as e:
            logger.warning("GPU summarizer init failed: %s", e)
    return _gpu_pipeline


@lru_cache(maxsize=512)
def _cached_summary_gpu(text: str, max_length: int = 100, min_length: int = 30) -> str:
    pipe = _get_gpu_summarizer()
    if pipe is None:
        return None
    if not isinstance(text, str) or len(text) < 50:
        return text
    try:
        result = pipe(text[:2048], max_length=max_length, min_length=min_length, do_sample=False, truncation=True, max_time=10)
        return result[0]["summary_text"]
    except Exception as e:
        logger.warning("GPU summarization failed: %s", e)
        return None


def _cached_summary_nltk(text: str, n_sentences: int = 3) -> str:
    from nltk import sent_tokenize, word_tokenize
    if not isinstance(text, str) or len(text) < 50:
        return text
    sentences = sent_tokenize(text)
    if len(sentences) <= n_sentences:
        return text
    words = word_tokenize(text.lower())
    word_freq = Counter(w for w in words if w.isalpha() and len(w) > 2)
    scores = []
    for sent in sentences:
        score = sum(word_freq.get(w.lower(), 0) for w in word_tokenize(sent))
        scores.append(score / max(len(sent.split()), 1))
    top_idx = np.argsort(scores)[-n_sentences:]
    top_idx.sort()
    return " ".join(sentences[i] for i in top_idx)


def extractive_summary(text: str, n_sentences: int = 3) -> str:
    gpu_result = _cached_summary_gpu(text)
    if gpu_result is not None:
        return gpu_result
    return _cached_summary_nltk(text, n_sentences)


def summarize_batch(texts: List[str]) -> List[str]:
    pipe = _get_gpu_summarizer()
    if pipe is None:
        return [extractive_summary(t) for t in texts]
    valid_indices = [i for i, t in enumerate(texts) if isinstance(t, str) and len(t) >= 50]
    if not valid_indices:
        return [extractive_summary(t) for t in texts]
    valid_texts = [texts[i][:2048] for i in valid_indices]
    try:
        all_results = pipe(valid_texts, max_length=100, min_length=20, do_sample=False, truncation=True, batch_size=8)
        results = [""] * len(texts)
        for batch_idx, idx in enumerate(valid_indices):
            results[idx] = all_results[batch_idx]["summary_text"]
        for i, t in enumerate(texts):
            if not results[i] or len(results[i]) < 10:
                results[i] = _cached_summary_nltk(t)
        return results
    except Exception as e:
        logger.warning("GPU batch summarization failed (%s), falling back to CPU", e)
        return [extractive_summary(t) for t in texts]
