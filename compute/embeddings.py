import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

_encoder = None


def _get_encoder():
    global _encoder
    if _encoder is not None:
        return _encoder
    from compute.gpu_manager import is_cuda, has_sentence_transformers
    if not has_sentence_transformers():
        logger.info("sentence-transformers not available, using TF-IDF fallback")
        return None
    from sentence_transformers import SentenceTransformer
    device = "cuda" if is_cuda() else "cpu"
    logger.info("Loading sentence-transformer model on %s...", device)
    _encoder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    return _encoder


def encode_texts(texts: List[str]) -> Optional[np.ndarray]:
    encoder = _get_encoder()
    if encoder is None:
        return None
    try:
        embeddings = encoder.encode(texts, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
        logger.info("Generated %d embeddings with shape %s", len(texts), embeddings.shape)
        return embeddings
    except Exception as e:
        logger.warning("GPU embedding failed: %s", e)
        return None
