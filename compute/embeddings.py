import hashlib
import logging
import numpy as np
from collections import OrderedDict
from typing import List, Optional

logger = logging.getLogger(__name__)

_encoder = None
_MODEL_NAME = "BAAI/bge-m3"

_EMBED_CACHE: OrderedDict = OrderedDict()
_MAX_CACHE_ENTRIES = 32


def _cache_key(texts: List[str], normalize: bool) -> bytes:
    h = hashlib.md5()
    for t in texts:
        h.update(t.encode("utf-8"))
    h.update(b"n" if normalize else b"r")
    return h.digest()


def _get_encoder():
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
            from compute.gpu_manager import device
            logger.info("Loading embedding model: %s (device=%s)", _MODEL_NAME, device)
            _encoder = SentenceTransformer(_MODEL_NAME, device=device)
        except Exception as e:
            logger.error("Failed to load BGE embedding model: %s", e)
    return _encoder


def encode_texts(texts: List[str], normalize: bool = True) -> Optional[np.ndarray]:
    if not texts:
        return None
    key = _cache_key(texts, normalize)
    if key in _EMBED_CACHE:
        _EMBED_CACHE.move_to_end(key)
        return _EMBED_CACHE[key]

    encoder = _get_encoder()
    if encoder is None:
        return None
    try:
        emb = encoder.encode(texts, show_progress_bar=False, normalize_embeddings=normalize)
        result = np.array(emb, dtype=np.float32)
        _EMBED_CACHE[key] = result
        while len(_EMBED_CACHE) > _MAX_CACHE_ENTRIES:
            _EMBED_CACHE.popitem(last=False)
        return result
    except Exception as e:
        logger.error("Embedding error: %s", e)
        return None


def clear_cache():
    _EMBED_CACHE.clear()


def encode_query(query: str) -> Optional[np.ndarray]:
    encoder = _get_encoder()
    if encoder is None:
        return None
    try:
        emb = encoder.encode([query], show_progress_bar=False, normalize_embeddings=True)
        return np.array(emb[0], dtype=np.float32)
    except Exception as e:
        logger.error("Query embedding error: %s", e)
        return None
