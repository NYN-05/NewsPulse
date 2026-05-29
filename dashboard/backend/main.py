"""
NewsPulse Intelligence API — Automated Continuous Pipeline

Single-entry process that:
1. Starts the FastAPI server to serve intelligence data
2. Runs the full pipeline immediately on startup
3. Schedules pipeline re-execution at a configurable interval
4. Writes all outputs atomically so the API never serves partial data
5. Exposes pipeline status (last run, next run, duration, errors)
6. Recovers gracefully from failures
"""

import os, sys, logging, math, threading, time
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import load_config, get, path_for, atomic_write_json, atomic_read_json

load_config()
logger = logging.getLogger("api")


# ---------------------------------------------------------------------------
# Pipeline state (thread-safe)
# ---------------------------------------------------------------------------

_PIPELINE_STATE = {
    "status": "idle",
    "last_run_at": None,
    "last_run_duration": None,
    "last_run_success": None,
    "last_error": None,
    "next_run_at": None,
    "run_count": 0,
    "articles_analyzed": 0,
}
_STATE_LOCK = threading.Lock()


def _update_state(**kw):
    with _STATE_LOCK:
        _PIPELINE_STATE.update(kw)


def _get_state():
    with _STATE_LOCK:
        return dict(_PIPELINE_STATE)


# ---------------------------------------------------------------------------
# Pipeline runner (runs in background thread)
# ---------------------------------------------------------------------------

def _run_pipeline():
    """Execute all pipeline steps and atomically write outputs."""
    from pipeline import (
        step_scrape, step_scrape_rss, step_dedup, step_fetch_details,
        step_analyze, step_entity_graph, step_cross_domain,
        step_narratives, step_signals, step_vector_index,
    )
    from storage.manager import DataManager
    import pandas as pd

    _update_state(status="running")
    start = time.time()
    data_mgr = DataManager()
    df = pd.DataFrame()
    error = None

    try:
        step_names = ["scrape", "rss", "dedup", "fetch", "analyze",
                      "entity_graph", "cross_domain", "narratives", "signals", "vector_index"]

        df = step_scrape(data_mgr)
        df = step_scrape_rss(data_mgr)
        df = step_dedup(df, data_mgr)
        df = step_fetch_details(df, data_mgr)
        df = step_analyze(df, data_mgr)

        step_entity_graph(df)
        step_cross_domain(df)
        step_narratives(df)
        step_signals(df)
        step_vector_index(df)

        article_count = len(df) if not df.empty else 0
        duration = round(time.time() - start, 1)
        _update_state(
            status="idle",
            last_run_at=datetime.now().isoformat(),
            last_run_duration=duration,
            last_run_success=True,
            last_error=None,
            run_count=_PIPELINE_STATE["run_count"] + 1,
            articles_analyzed=article_count,
        )
        logger.info("Pipeline completed in %.1f s — %d articles processed", duration, article_count)

    except Exception as e:
        duration = round(time.time() - start, 1)
        error = f"{type(e).__name__}: {e}"
        logger.error("Pipeline failed after %.1f s: %s", duration, error)
        _update_state(
            status="error",
            last_run_at=datetime.now().isoformat(),
            last_run_duration=duration,
            last_run_success=False,
            last_error=error,
        )


# ---------------------------------------------------------------------------
# Scheduler — runs pipeline on an interval in a background daemon thread
# ---------------------------------------------------------------------------

_PIPELINE_THREAD: Optional[threading.Thread] = None
_SCHEDULER_STOP = threading.Event()


def _scheduler_loop():
    """Daemon loop: run pipeline, sleep for interval, repeat."""
    interval = get("scheduler.interval_minutes", 15)
    initial_delay = get("scheduler.initial_delay_seconds", 10)

    logger.info("Scheduler: initial pipeline in %ds, then every %d min", initial_delay, interval)
    time.sleep(initial_delay)

    while not _SCHEDULER_STOP.is_set():
        _run_pipeline()
        # compute next run time
        next_run = datetime.now() + timedelta(minutes=interval)
        _update_state(next_run_at=next_run.isoformat())
        logger.info("Scheduler: next run at %s", next_run.isoformat())
        _SCHEDULER_STOP.wait(interval * 60)


def start_scheduler():
    global _PIPELINE_THREAD
    if not get("scheduler.enabled", True):
        logger.info("Scheduler is disabled in config")
        return
    if _PIPELINE_THREAD and _PIPELINE_THREAD.is_alive():
        logger.warning("Scheduler already running")
        return
    _SCHEDULER_STOP.clear()
    _PIPELINE_THREAD = threading.Thread(target=_scheduler_loop, daemon=True, name="pipeline-scheduler")
    _PIPELINE_THREAD.start()
    logger.info("Background pipeline scheduler started")


def stop_scheduler():
    _SCHEDULER_STOP.set()
    logger.info("Scheduler stop signal sent")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(title="NewsPulse Intelligence API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def on_startup():
    """Auto-start the scheduler when the API server starts."""
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    """Gracefully stop the scheduler."""
    stop_scheduler()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj


def _load_intel(name):
    """Atomically read an intelligence output file, returning cleaned data."""
    p = os.path.join(path_for("output_dir"), name)
    data = atomic_read_json(p)
    if data is None:
        return {}
    return _clean(data)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    state = _get_state()
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "pipeline": state,
    }


@app.get("/api/pipeline-status")
def pipeline_status():
    return _get_state()


@app.post("/api/trigger-pipeline")
def trigger_pipeline():
    """On-demand pipeline execution — runs in background, returns immediately."""
    t = threading.Thread(target=_run_pipeline, daemon=True)
    t.start()
    return {"status": "triggered", "message": "Pipeline started in background"}


@app.get("/api/cross-domain")
def cross_domain():
    links = _load_intel("cross_domain_links.json")
    chains = _load_intel("impact_chains.json")
    sector_map = _load_intel("sector_map.json")
    return {
        "links": links if isinstance(links, list) else [],
        "chains": chains if isinstance(chains, list) else [],
        "sector_map": sector_map if isinstance(sector_map, dict) else {},
    }


@app.get("/api/entity-graph")
def entity_graph():
    return _load_intel("entity_graph.json")


@app.get("/api/narratives")
def narratives():
    return _load_intel("narrative_evolution.json")


@app.get("/api/signals")
def signals():
    data = _load_intel("breaking_events.json")
    if isinstance(data, dict):
        return data
    return {"signals": data if isinstance(data, list) else [], "summary": {}}


@app.get("/api/search")
def search(q: str = Query("", min_length=1), n: int = 10):
    try:
        from vector_store.chroma_store import semantic_search
        results = semantic_search(q, n_results=n)
        return {"results": results, "query": q}
    except Exception as e:
        return {"error": str(e), "results": []}


@app.get("/api/explain")
def explain_relationship(source: str = Query(""), target: str = Query("")):
    if not source or not target:
        return {"error": "source and target required"}
    try:
        links = _load_intel("cross_domain_links.json")
        if isinstance(links, list):
            for l in links:
                if l.get("source_entity") == source and l.get("target_entity") == target:
                    from intelligence.explanation import explain_relationship as explain
                    explanation = explain(
                        source_entity=l["source_entity"],
                        target_entity=l["target_entity"],
                        source_sector=l.get("source_sector", "unknown"),
                        target_sector=l.get("target_sector", "unknown"),
                        cooccurrence_count=l.get("cooccurrence_count", 0),
                        source_diversity=l.get("source_diversity", 0),
                        strength=l.get("strength", 0),
                    )
                    return {"link": l, "explanation": explanation}
        return {"error": "relationship not found"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Entry point — single command to start everything
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    logger.info("Starting NewsPulse Intelligence API on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
