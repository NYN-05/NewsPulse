"""
WebSocket Manager — Phase 5.

Manages real-time intelligence streaming to connected clients.
Pushes pipeline completion events, new signals, and alerts.
"""

import json
import logging
import asyncio
from typing import Set, Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("ws")

_clients: Set[WebSocket] = set()


async def connect(ws: WebSocket):
    await ws.accept()
    _clients.add(ws)
    logger.info("WebSocket client connected (%d total)", len(_clients))


def disconnect(ws: WebSocket):
    _clients.discard(ws)
    logger.info("WebSocket client disconnected (%d remaining)", len(_clients))


async def broadcast(event: str, data: Any):
    """Send an event to all connected WebSocket clients."""
    if not _clients:
        return
    message = json.dumps({"event": event, "data": data, "timestamp": datetime.now().isoformat()})
    dead = set()
    for ws in _clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _clients.discard(ws)


async def broadcast_pipeline_complete(state: Dict):
    await broadcast("pipeline_complete", {
        "duration": state.get("last_run_duration"),
        "success": state.get("last_run_success"),
        "articles_analyzed": state.get("articles_analyzed"),
        "run_count": state.get("run_count"),
    })


async def broadcast_alert(alert: Dict):
    await broadcast("alert", alert)


async def broadcast_signal(signal: Dict):
    await broadcast("signal", signal)
