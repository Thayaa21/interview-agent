"""FastAPI backend — REST + WebSocket for the live dashboard.

Endpoints:
  GET  /api/health                     -> {"ok": true}
  GET  /api/rulebook                   -> the active rulebook (for the UI)
  GET  /api/sessions                   -> list of sessions
  GET  /api/sessions/{id}              -> session info
  GET  /api/sessions/{id}/events       -> all events for a session (replay)
  POST /api/mock/start                 -> start a scripted mock call
  WS   /ws                             -> live event stream (all sessions)

Run:
  uvicorn layer.server.app:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
from typing import Optional

from ..analysis.criteria import load_criteria
from ..compliance.rules import load_rulebook
from ..types import new_id
from .mock_driver import run_mock_call
from .store import STORE

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "FastAPI is required for the backend. Install with: pip install -r layer/requirements.txt"
    ) from exc


app = FastAPI(title="Interview Agent Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev only
    allow_methods=["*"],
    allow_headers=["*"],
)


class MockStartRequest(BaseModel):
    candidate: str = "Alex Taylor"
    role: str = "oncology_rn"
    speed: float = 4.0


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/rulebook")
async def rulebook():
    rb = load_rulebook()
    return {
        "purpose": rb.purpose,
        "off_topic_signals": rb.off_topic_signals,
        "injection_signals": rb.injection_signals,
        "allowed_output_kinds": rb.allowed_output_kinds,
        "budgets": rb.budgets.__dict__,
    }


@app.get("/api/criteria")
async def criteria():
    data = load_criteria()
    return {
        role: {qid: {"competency": qc.competency,
                     "criteria": [{"id": c.id, "label": c.label} for c in qc.criteria]}
               for qid, qc in qmap.items()}
        for role, qmap in data.items()
    }


@app.get("/api/sessions")
async def sessions():
    return [s.to_dict() for s in STORE.list_sessions()]


@app.get("/api/sessions/{session_id}")
async def session(session_id: str):
    s = STORE.get_session(session_id)
    return s.to_dict() if s else {"error": "not found"}


@app.get("/api/sessions/{session_id}/events")
async def session_events(session_id: str):
    return [e.to_dict() for e in STORE.get_events(session_id)]


@app.post("/api/mock/start")
async def mock_start(req: MockStartRequest):
    session_id = new_id("sess_")
    # Fire and forget; events stream over the WebSocket.
    asyncio.create_task(run_mock_call(req.candidate, req.role, session_id, speed=req.speed))
    return {"session_id": session_id}


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    queue = STORE.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event.to_dict())
    except WebSocketDisconnect:
        pass
    finally:
        STORE.unsubscribe(queue)
