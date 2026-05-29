import os, sys, json, logging, math
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import load_config, get, path_for

load_config()
logger = logging.getLogger("api")

app = FastAPI(title="NewsPulse Intelligence API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj


def _load_json(name):
    p = os.path.join(path_for("output_dir"), name)
    if os.path.isdir(p) or not os.path.exists(p):
        return {}
    with open(p) as f:
        return _clean(json.load(f))


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


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


@app.get("/api/entity-graph")
def entity_graph():
    return _load_json("entity_graph.json")


@app.get("/api/influence")
def influence():
    return _load_json("influence_map.json")


@app.get("/api/narratives")
def narratives():
    return _load_json("narrative_evolution.json")


@app.get("/api/breaking")
def breaking():
    return _load_json("breaking_events.json")


@app.get("/api/search")
def search(q: str = Query("", min_length=1), n: int = 10):
    try:
        from vector_store.chroma_store import semantic_search
        results = semantic_search(q, n_results=n)
        return {"results": results, "query": q}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
