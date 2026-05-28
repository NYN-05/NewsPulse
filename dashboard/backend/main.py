import os, sys, json, logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import load_config, get, path_for

load_config()
logger = logging.getLogger("api")

app = FastAPI(title="NewsPulse API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_analyzed: Optional[pd.DataFrame] = None


def _load_data() -> pd.DataFrame:
    global _analyzed
    if _analyzed is not None:
        return _analyzed
    p = path_for("analyzed_parquet")
    if os.path.exists(p):
        _analyzed = pd.read_parquet(p)
        logger.info("Loaded %d rows from %s", len(_analyzed), p)
    else:
        _analyzed = pd.DataFrame()
        logger.warning("Parquet file not found at %s", p)
    return _analyzed


def _resolve_time_col(df):
    for c in ["published", "scraped_at", "analyzed_at"]:
        if c in df.columns and df[c].notna().sum() > len(df) * 0.3:
            return c
    return None


def _parse_dates(df, time_col):
    parsed = pd.to_datetime(df[time_col], utc=True, errors="coerce")
    parsed[pd.to_datetime(df[time_col], utc=True, errors="coerce") < pd.Timestamp("2020-01-01", tz="UTC")] = pd.NaT
    return parsed


def _load_json(name):
    p = os.path.join(path_for("output_dir"), name)
    if os.path.isdir(p):
        return {}
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {}


# ---- Health ----
@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ---- Summary / KPIs ----
@app.get("/api/summary")
def summary():
    df = _load_data()
    if df.empty:
        return {}
    n = len(df)
    avg_sent = float(df["compound"].mean()) if "compound" in df.columns else 0
    avg_sens = float(df["sensationalism_score"].mean()) if "sensationalism_score" in df.columns else 0
    avg_viral = float(df["virality_score"].mean()) if "virality_score" in df.columns else 0
    sources = int(df["source"].nunique()) if "source" in df.columns else 0
    cats = int(df["category"].nunique()) if "category" in df.columns else 0
    return {
        "total_articles": n,
        "avg_sentiment": round(avg_sent, 4),
        "avg_sensationalism": round(avg_sens, 4),
        "avg_virality": round(avg_viral, 4),
        "sources": sources,
        "categories": cats,
        "vector_indexed": 2020,
        "last_updated": datetime.now().isoformat(),
    }


# ---- Sentiment ----
@app.get("/api/sentiment")
def sentiment(source: Optional[str] = None, category: Optional[str] = None, days: int = 30):
    df = _load_data()
    if df.empty:
        return {}
    df = _apply_filters(df, source, category, days)
    dist = df["sentiment"].value_counts().to_dict() if "sentiment" in df.columns else {}
    return {
        "distribution": {k: int(v) for k, v in dist.items()},
        "avg_compound": round(float(df["compound"].mean()), 4) if "compound" in df.columns else 0,
    }


# ---- Categories ----
@app.get("/api/categories")
def categories(source: Optional[str] = None, days: int = 30):
    df = _load_data()
    if df.empty:
        return []
    df = _apply_filters(df, source, None, days)
    if "category" not in df.columns:
        return []
    cats = df["category"].fillna("Uncategorized").value_counts().head(30)
    return [{"name": k, "count": int(v)} for k, v in cats.items()]


# ---- Top Keywords / Trends ----
@app.get("/api/trends")
def trends():
    df = _load_data()
    if df.empty or "text" not in df.columns:
        return {}
    stop = set(get("trending.stop_words", []))
    from collections import Counter
    words = Counter()
    for t in df["text"].dropna().head(2000):
        for w in str(t).lower().split():
            wc = w.strip(".,!?\"'():;")
            if len(wc) > 3 and wc not in stop:
                words[wc] += 1
    return {"top_keywords": [{"word": w, "count": c} for w, c in words.most_common(20)]}


# ---- Clusters ----
@app.get("/api/clusters")
def clusters():
    df = _load_data()
    if df.empty or "cluster_label" not in df.columns:
        return []
    groups = df.groupby("cluster_label").agg(
        count=("cluster_label", "size"),
        avg_sentiment=("compound", "mean"),
        top_source=("source", lambda x: x.mode().iloc[0] if not x.mode().empty else ""),
    ).reset_index()
    result = []
    for _, r in groups.iterrows():
        result.append({
            "label": str(r["cluster_label"]),
            "count": int(r["count"]),
            "avg_sentiment": round(float(r["avg_sentiment"]), 4),
            "top_source": str(r["top_source"]),
        })
    return sorted(result, key=lambda x: -x["count"])


# ---- Cross-Domain Relationships ----
@app.get("/api/cross-domain")
def cross_domain():
    links = _load_json("cross_domain_links.json")
    chains = _load_json("impact_chains.json")
    sector_map = _load_json("sector_map.json")
    return {
        "links": links if isinstance(links, list) else [],
        "chains": chains if isinstance(chains, list) else [],
        "sector_map": sector_map if isinstance(sector_map, dict) else {},
    }


# ---- Entity Graph ----
@app.get("/api/entity-graph")
def entity_graph():
    return _load_json("entity_graph.json")


# ---- Influence Map ----
@app.get("/api/influence")
def influence():
    return _load_json("influence_map.json")


# ---- Entity Trends ----
@app.get("/api/entity-trends")
def entity_trends():
    return _load_json("entity_trends.json")


# ---- Narrative Evolution ----
@app.get("/api/narratives")
def narratives():
    return _load_json("narrative_evolution.json")


# ---- Breaking Events ----
@app.get("/api/breaking")
def breaking():
    return _load_json("breaking_events.json")


# ---- Topic Evolution ----
@app.get("/api/topic-evolution")
def topic_evolution():
    return _load_json("topic_evolution.json")


# ---- Source Reliability ----
@app.get("/api/source-reliability")
def source_reliability():
    return _load_json("source_reliability.json")


# ---- Virality Distribution ----
@app.get("/api/virality")
def virality(source: Optional[str] = None, days: int = 30):
    df = _load_data()
    if df.empty or "virality_score" not in df.columns:
        return {}
    df = _apply_filters(df, source, None, days)
    scores = df["virality_score"].dropna().tolist()
    top = df.nlargest(10, "virality_score")[["title", "source", "virality_score", "sentiment", "link"]].to_dict("records")
    return {
        "distribution": scores,
        "avg_virality": round(float(np.mean(scores)), 4) if scores else 0,
        "top_viral": [{k: str(v)[:100] for k, v in t.items()} for t in top],
    }


# ---- Bias Analysis ----
@app.get("/api/bias")
def bias():
    df = _load_data()
    if df.empty or "political_leaning" not in df.columns:
        return {}
    leaning = df["political_leaning"].value_counts().to_dict()
    return {
        "political_leaning": {k: int(v) for k, v in leaning.items()},
        "avg_clickbait": round(float(df["clickbait_score"].mean()), 4) if "clickbait_score" in df.columns else 0,
        "avg_emotional": round(float(df["emotional_score"].mean()), 4) if "emotional_score" in df.columns else 0,
    }


# ---- Language Distribution ----
@app.get("/api/languages")
def languages():
    df = _load_data()
    if df.empty or "language" not in df.columns:
        return []
    lang = df["language"].value_counts().head(15)
    return [{"code": k, "count": int(v)} for k, v in lang.items()]


# ---- Semantic Search ----
@app.get("/api/search")
def search(q: str = Query("", min_length=1), n: int = 10):
    try:
        from vector_store.chroma_store import semantic_search
        results = semantic_search(q, n_results=n)
        return {"results": results, "query": q}
    except Exception as e:
        return {"error": str(e)}


# ---- Raw Data Export ----
@app.get("/api/data")
def data(source: Optional[str] = None, category: Optional[str] = None, days: int = 30, limit: int = 100):
    df = _load_data()
    if df.empty:
        return []
    df = _apply_filters(df, source, category, days)
    exclude = {"text", "full_text", "entities", "summary"}
    cols = [c for c in df.columns if c not in exclude]
    df = df[cols].head(limit)
    return json.loads(df.to_json(orient="records", date_format="iso"))


# ---- Sources List ----
@app.get("/api/sources")
def sources():
    df = _load_data()
    if df.empty or "source" not in df.columns:
        return []
    srcs = df["source"].value_counts()
    return [{"name": k, "count": int(v)} for k, v in srcs.items()]


def _apply_filters(df, source=None, category=None, days=30):
    df = df.copy()
    time_col = _resolve_time_col(df)
    if time_col:
        parsed = _parse_dates(df, time_col)
        cutoff = datetime.now() - timedelta(days=days)
        df = df[parsed >= pd.Timestamp(cutoff, tz="UTC")]
    if source and "source" in df.columns:
        df = df[df["source"].str.contains(source, case=False, na=False)]
    if category and "category" in df.columns:
        df = df[df["category"].str.lower() == category.lower()]
    return df


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
