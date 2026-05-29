"""
Vector Store for Semantic Intelligence Search.

Upgraded with:
- BGE-M3 embeddings (upgraded from all-MiniLM-L6-v2)
- Hybrid search: BM25 + vector search
- Optional BGE reranker for precision improvement
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

try:
    import rank_bm25
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

_collection = None
_bm25_index = None
_bm25_docs = None
_reranker = None


def _get_collection():
    global _collection
    if _collection is None and HAS_CHROMA:
        try:
            from config.settings import path_for
            client = chromadb.PersistentClient(
                path=os.path.join(path_for("output_dir"), "chroma_db"),
                settings=Settings(anonymized_telemetry=False),
            )
            _collection = client.get_or_create_collection(
                name="newspulse",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB collection ready: %s", _collection.count())
        except Exception as e:
            logger.warning("ChromaDB init failed: %s", e)
    return _collection


def _get_embeddings(texts: List[str]):
    try:
        from compute.embeddings import encode_texts
        return encode_texts(texts, normalize=True)
    except Exception as e:
        logger.error("Embedding error: %s", e)
        return None


def _get_reranker():
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info("Loading reranker: BAAI/bge-reranker-v2-m3")
            _reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
        except Exception as e:
            logger.debug("Reranker unavailable: %s", e)
    return _reranker


def index_articles(df: pd.DataFrame) -> int:
    collection = _get_collection()
    if collection is None:
        return 0

    texts = []
    metadatas = []
    ids = []

    for row in df.itertuples():
        title = str(getattr(row, "title", "") or "")
        desc = str(getattr(row, "description", "") or "")
        text = f"{title}. {desc}".strip()
        if len(text) < 30:
            continue
        link = str(getattr(row, "link", "") or "")
        doc_id = f"article_{hash(link) % 10**12}" if link else f"article_{_id_generator()}"

        texts.append(text)
        metadatas.append({
            "title": title,
            "source": str(row.get("source", "") or ""),
            "published": str(row.get("published", "") or ""),
            "category": str(row.get("category", "") or ""),
            "sentiment": str(row.get("sentiment", "") or ""),
        })
        ids.append(doc_id)

    if not texts:
        return 0

    embeddings = _get_embeddings(texts)
    if embeddings is None:
        logger.warning("Skipping vector indexing — embeddings unavailable")
        return 0

    try:
        batch_size = 128
        for i in range(0, len(texts), batch_size):
            end = min(i + batch_size, len(texts))
            collection.add(
                embeddings=embeddings[i:end].tolist(),
                documents=texts[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end],
            )
        logger.info("Indexed %d articles into vector store", len(texts))
        return len(texts)
    except Exception as e:
        logger.error("Indexing error: %s", e)
        return 0


_id_counter = 0


def _id_generator() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter


def _build_bm25_index(texts: List[str]):
    global _bm25_index, _bm25_docs
    if not HAS_BM25 or not texts:
        return
    try:
        tokenized = [t.lower().split() for t in texts]
        _bm25_index = rank_bm25.BM25Okapi(tokenized)
        _bm25_docs = texts
    except Exception as e:
        logger.debug("BM25 init error: %s", e)


def semantic_search(query: str, n_results: int = 10, use_hybrid: bool = True, use_reranker: bool = False) -> List[Dict]:
    collection = _get_collection()
    if collection is None:
        return [{"error": "vector store not available"}]

    query_embedding = _get_embeddings([query])
    if query_embedding is None:
        return [{"error": "query embedding failed"}]

    try:
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results * 2 if use_hybrid else n_results,
        )
    except Exception as e:
        return [{"error": str(e)}]

    candidates = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 0
            score = 1.0 - dist if dist <= 1.0 else 0.0
            candidates.append({
                "title": meta.get("title", ""),
                "source": meta.get("source", ""),
                "published": meta.get("published", ""),
                "category": meta.get("category", ""),
                "sentiment": meta.get("sentiment", ""),
                "score": round(score * 10, 3),
                "snippet": doc[:300] if doc else "",
            })

    if use_hybrid and HAS_BM25:
        try:
            bm25_scores = _bm25_index.get_scores(query.lower().split()) if _bm25_index else []
            if bm25_scores and _bm25_docs:
                bm25_results = sorted(
                    [(i, s) for i, s in enumerate(bm25_scores) if s > 0],
                    key=lambda x: -x[1],
                )[:n_results]
                bm25_candidates = []
                for idx, bm25_score in bm25_results:
                    bm25_candidates.append({
                        "title": _bm25_docs[idx][:100],
                        "score": round(float(bm25_score), 3),
                        "snippet": _bm25_docs[idx][:300],
                    })
                merged = _reciprocal_rank_fusion(candidates, bm25_candidates, k=60)
                candidates = sorted(merged, key=lambda x: -x["rrf_score"])[:n_results]
                for c in candidates:
                    c.pop("rrf_score", None)
        except Exception as e:
            logger.debug("Hybrid search error: %s", e)

    if use_reranker and len(candidates) > 1:
        reranker = _get_reranker()
        if reranker:
            try:
                pairs = [(query, c.get("snippet", "")[:512]) for c in candidates]
                scores = reranker.predict(pairs)
                for c, s in zip(candidates, scores):
                    c["rerank_score"] = round(float(s), 3)
                candidates.sort(key=lambda x: -x.get("rerank_score", x.get("score", 0)))
            except Exception as e:
                logger.debug("Reranker error: %s", e)

    return candidates[:n_results]


def _reciprocal_rank_fusion(vector_results: List[Dict], bm25_results: List[Dict], k: int = 60) -> List[Dict]:
    merged = {}
    for rank, doc in enumerate(vector_results):
        key = doc.get("title", doc.get("snippet", ""))[:100]
        merged[key] = {
            "title": doc.get("title", ""),
            "source": doc.get("source", ""),
            "published": doc.get("published", ""),
            "snippet": doc.get("snippet", ""),
            "score": doc.get("score", 0),
            "rrf_score": 1.0 / (k + rank + 1),
        }
    for rank, doc in enumerate(bm25_results):
        key = doc.get("title", doc.get("snippet", ""))[:100]
        if key in merged:
            merged[key]["rrf_score"] += 1.0 / (k + rank + 1)
            merged[key]["score"] = max(merged[key]["score"], doc.get("score", 0))
        else:
            merged[key] = {
                "title": doc.get("title", ""),
                "snippet": doc.get("snippet", ""),
                "score": doc.get("score", 0),
                "rrf_score": 1.0 / (k + rank + 1),
            }
    return list(merged.values())


def get_collection_stats() -> Dict:
    collection = _get_collection()
    if collection is None:
        return {"count": 0}
    try:
        return {"count": collection.count()}
    except Exception:
        return {"count": 0}
