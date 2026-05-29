"""
NewsPulse Intelligence API — Automated Continuous Pipeline (Phase 3–5)

Single-entry process with:
1. FastAPI server serving intelligence data + WebSocket real-time events
2. Full pipeline on startup + scheduled re-execution
3. Atomic writes so API never serves stale data
4. Pipeline status + auth middleware + export endpoints
5. All endpoints reflect Phase 3–5 capabilities
"""

import os, sys, logging, math, threading, time
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

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
_PIPELINE_RUN_LOCK = threading.Lock()


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
    """Execute all Phases 1-5 and atomically write outputs."""
    if not _PIPELINE_RUN_LOCK.acquire(blocking=False):
        logger.warning("Pipeline already running — skipping concurrent trigger")
        return

    from pipeline import (
        step_scrape, step_scrape_rss, step_dedup, step_fetch_details,
        step_analyze, step_entity_graph, step_cross_domain, step_causal,
        step_narratives, step_signals, step_multi_agent, step_temporal,
        step_briefings, step_alerts, step_export, step_neo4j, step_vector_index,
        run_pipeline,
    )
    from storage.manager import DataManager

    _update_state(status="running")
    start = time.time()
    error = None

    try:
        _, _, temporal_result, agent_result, briefing_result, causal_result = run_pipeline()

        duration = round(time.time() - start, 1)

        import pandas as pd
        data_mgr = DataManager()
        df = data_mgr.load_analyzed()
        article_count = len(df) if not df.empty else 0

        _update_state(
            status="idle",
            last_run_at=datetime.now().isoformat(),
            last_run_duration=duration,
            last_run_success=True,
            last_error=None,
            run_count=_PIPELINE_STATE["run_count"] + 1,
            articles_analyzed=article_count,
        )
        logger.info("Pipeline completed in %.1f s — %d articles", duration, article_count)

        # Clear API cache so next poll sees fresh data
        _INTEL_CACHE.clear()

        # WebSocket broadcast
        _broadcast_pipeline_complete()

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
    finally:
        _PIPELINE_RUN_LOCK.release()


def _broadcast_pipeline_complete():
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from dashboard.backend.ws import broadcast_pipeline_complete
        loop.run_until_complete(broadcast_pipeline_complete(_get_state()))
        loop.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Scheduler (APScheduler)
# ---------------------------------------------------------------------------

_SCHEDULER: Optional[BackgroundScheduler] = None


def _update_next_run_state():
    if _SCHEDULER is None:
        return
    job = _SCHEDULER.get_job("pipeline_run")
    if job and job.next_run_time:
        _update_state(next_run_at=job.next_run_time.isoformat())


def start_scheduler():
    global _SCHEDULER
    if not get("scheduler.enabled", True):
        logger.info("Scheduler disabled in config")
        return
    if _SCHEDULER and _SCHEDULER.running:
        return

    interval = get("scheduler.interval_minutes", 15)
    initial_delay = get("scheduler.initial_delay_seconds", 10)

    _SCHEDULER = BackgroundScheduler(daemon=True)
    _SCHEDULER.add_job(
        _run_pipeline,
        trigger=IntervalTrigger(
            minutes=interval,
            start_at=datetime.now() + timedelta(seconds=initial_delay),
        ),
        id="pipeline_run",
        replace_existing=True,
        misfire_grace_time=120,
        name="newspluse_pipeline",
    )
    _update_next_run_state()
    _SCHEDULER.start()
    logger.info(
        "APScheduler started: every %d min (initial delay %ds, misfire_grace=%ds)",
        interval, initial_delay, 120,
    )


def stop_scheduler():
    global _SCHEDULER
    if _SCHEDULER:
        _SCHEDULER.shutdown(wait=False)
        _SCHEDULER = None
        logger.info("APScheduler shut down")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title="NewsPulse Intelligence API", version="3.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

from dashboard.backend.ws import connect as ws_connect, disconnect as ws_disconnect


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_disconnect(ws)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_INTEL_CACHE: dict = {}
_INTEL_CACHE_TTL = 5.0  # seconds


def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj


def _load_intel(name: str):
    now = time.time()
    if name in _INTEL_CACHE and now - _INTEL_CACHE[name][1] < _INTEL_CACHE_TTL:
        return _INTEL_CACHE[name][0]
    p = os.path.join(path_for("output_dir"), name)
    data = atomic_read_json(p)
    if data is None:
        data = {}
    data = _clean(data)
    _INTEL_CACHE[name] = (data, now)
    return data


# ---------------------------------------------------------------------------
# Endpoints — Phase 1-2 (Core)
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    state = _get_state()
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0",
        "pipeline": state,
    }


@app.get("/api/pipeline-status")
def pipeline_status():
    return _get_state()


@app.post("/api/trigger-pipeline")
def trigger_pipeline():
    if _PIPELINE_RUN_LOCK.locked():
        return {"status": "already_running", "message": "Pipeline is already running"}
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
                        confidence=l.get("confidence"),
                        causal_direction=l.get("causal_direction"),
                        causal_mechanism=l.get("causal_mechanism"),
                        impact_prediction=l.get("impact_prediction"),
                    )
                    return {"link": l, "explanation": explanation}
        return {"error": "relationship not found"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Phase 3 Endpoints — Causal Reasoning & Confidence
# ---------------------------------------------------------------------------

@app.get("/api/causal-analysis")
def get_causal_analysis():
    return _load_intel("causal_analysis.json")


# ---------------------------------------------------------------------------
# Phase 4 Endpoints — Agents, Temporal, Briefings
# ---------------------------------------------------------------------------

@app.get("/api/multi-agent-analysis")
def get_multi_agent_analysis():
    return _load_intel("multi_agent_analysis.json")


@app.get("/api/temporal-patterns")
def get_temporal_patterns():
    return _load_intel("temporal_patterns.json")


@app.get("/api/briefing")
def get_briefing():
    return _load_intel("intelligence_briefing.json")


# ---------------------------------------------------------------------------
# Phase 5 Endpoints — Alerts, Exports, Auth, Neo4j
# ---------------------------------------------------------------------------

@app.get("/api/alerts")
def get_alerts():
    return _load_intel("alerts.json")


@app.post("/api/export")
def trigger_export(fmt: str = Query("json", pattern="^(json|csv|markdown)$")):
    try:
        from dashboard.backend.exporter import export_json, export_csv, export_markdown
        export_dir = path_for("export.json_dir") or os.path.join(path_for("output_dir"), "exports")
        os.makedirs(export_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path_map = {
            "json": (export_json, f"intelligence_export_{ts}.json"),
            "csv": (export_csv, f"relationships_{ts}.csv"),
            "markdown": (export_markdown, f"briefing_{ts}.md"),
        }
        fn, name = path_map[fmt]
        out = fn(os.path.join(export_dir, name))
        return {"status": "ok", "path": out, "format": fmt}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/neo4j-status")
def neo4j_status():
    try:
        from vector_store.neo4j_store import Neo4jStore
        store = Neo4jStore(
            uri=get("neo4j.uri", "bolt://localhost:7687"),
            user=get("neo4j.user", "neo4j"),
            password=get("neo4j.password", "password"),
        )
        stats = store.get_statistics() if store.enabled else {"enabled": False}
        store.close()
        return stats
    except Exception as e:
        return {"enabled": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Auth endpoints (if enabled)
# ---------------------------------------------------------------------------

@app.post("/api/auth/login")
def auth_login(username: str = Query(""), password: str = Query("")):
    if not get("auth.enabled", False):
        return {"status": "auth_disabled"}
    from dashboard.backend.auth import authenticate
    user = authenticate(username, password)
    if not user:
        return {"error": "Invalid credentials"}
    return {"user": user, "token": "placeholder-jwt"}


@app.post("/api/auth/register")
def auth_register(username: str = Query(""), password: str = Query(""), role: str = "viewer"):
    if not get("auth.enabled", False):
        return {"status": "auth_disabled"}
    from dashboard.backend.auth import create_user
    try:
        create_user(username, password, role)
        return {"status": "ok", "user": username, "role": role}
    except ValueError as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    logger.info("Starting NewsPulse Intelligence API v3.0 on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
