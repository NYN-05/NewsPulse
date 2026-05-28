import os
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Optional, Dict
from config.settings import get, path_for

logger = logging.getLogger(__name__)

_chroma_client = None
_collection = None


def _get_chroma():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        persist_dir = os.path.join(path_for("output_dir"), "chroma_db")
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        _collection = _chroma_client.get_or_create_collection(
            name=get("vector_store.collection_name", "newspulse"),
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB initialized at %s", persist_dir)
        return _collection
    except ImportError:
        logger.warning("chromadb not installed, vector search disabled")
        return None
    except Exception as e:
        logger.warning("ChromaDB init failed: %s", e)
        return None


def _get_embeddings(texts: List[str]) -> Optional[np.ndarray]:
    from compute.embeddings import encode_texts
    return encode_texts(texts)


def index_articles(df: pd.DataFrame) -> int:
    col = _get_chroma()
    if col is None:
        return 0

    if df.empty:
        return 0

    texts = (df["text"].fillna("") + " " + df["summary"].fillna("")).tolist() if "summary" in df.columns else df["text"].fillna("").tolist()
    existing_ids = set(col.get()["ids"]) if col.count() > 0 else set()

    new_indices = []
    new_texts = []
    new_metadatas = []

    for idx, row in df.iterrows():
        doc_id = str(row.get("link", f"article_{idx}"))
        if doc_id in existing_ids:
            continue
        text = texts[idx] if idx < len(texts) else ""
        if not isinstance(text, str) or len(text) < 20:
            continue
        new_indices.append(doc_id)
        new_texts.append(text[:2000])
        new_metadatas.append({
            "title": str(row.get("title", ""))[:200],
            "source": str(row.get("source", ""))[:100],
            "category": str(row.get("category", ""))[:50],
            "sentiment": str(row.get("sentiment", "")),
            "published": str(row.get("published", "")),
            "link": str(row.get("link", "")),
        })

    if not new_indices:
        logger.info("No new articles to index (total: %d)", col.count())
        return col.count()

    batch_size = 64
    total_indexed = 0
    for i in range(0, len(new_indices), batch_size):
        batch_ids = new_indices[i:i + batch_size]
        batch_texts = new_texts[i:i + batch_size]
        batch_meta = new_metadatas[i:i + batch_size]
        embeddings = _get_embeddings(batch_texts)
        if embeddings is None:
            logger.warning("Embeddings failed, skipping batch")
            continue
        col.add(
            embeddings=embeddings.tolist(),
            ids=batch_ids,
            documents=batch_texts,
            metadatas=batch_meta,
        )
        total_indexed += len(batch_ids)

    logger.info("Indexed %d new articles into vector DB (total: %d)", total_indexed, col.count())
    return col.count()


def semantic_search(query: str, n_results: int = 10) -> List[Dict]:
    col = _get_chroma()
    if col is None:
        return []

    from compute.embeddings import encode_texts
    q_emb = encode_texts([query])
    if q_emb is None:
        return []

    results = col.query(query_embeddings=q_emb.tolist(), n_results=n_results)
    docs = []
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            docs.append({
                "id": results["ids"][0][i],
                "title": results["metadatas"][0][i].get("title", ""),
                "source": results["metadatas"][0][i].get("source", ""),
                "category": results["metadatas"][0][i].get("category", ""),
                "sentiment": results["metadatas"][0][i].get("sentiment", ""),
                "link": results["metadatas"][0][i].get("link", ""),
                "score": round(1 - results["distances"][0][i], 4),
                "snippet": results["documents"][0][i][:200] if results.get("documents") else "",
            })
    return docs


def find_similar(link: str, n_results: int = 5) -> List[Dict]:
    col = _get_chroma()
    if col is None:
        return []
    try:
        results = col.query(query_texts=[link], n_results=n_results + 1)
        docs = []
        for i in range(len(results["ids"][0])):
            if results["ids"][0][i] == link:
                continue
            docs.append({
                "id": results["ids"][0][i],
                "title": results["metadatas"][0][i].get("title", ""),
                "source": results["metadatas"][0][i].get("source", ""),
                "score": round(1 - results["distances"][0][i], 4),
            })
        return docs[:n_results]
    except Exception as e:
        logger.warning("Similar search failed: %s", e)
        return []


def get_collection_stats() -> Dict:
    col = _get_chroma()
    if col is None:
        return {"count": 0, "status": "disabled"}
    try:
        return {
            "count": col.count(),
            "status": "ready",
        }
    except Exception as e:
        return {"count": 0, "status": f"error: {e}"}
