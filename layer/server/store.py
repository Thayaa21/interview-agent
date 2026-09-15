"""In-memory session store + async event bus.

Holds live session state (sessions, turns, guardrail events, analyses) and
broadcasts every new Event to subscribers (the WebSocket clients) so the
dashboard updates in real time. In-memory is fine for the demo; a DB can back
this later behind the same interface.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, List, Set

from ..types import Event, EventType, SessionInfo


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionInfo] = {}
        self._events: Dict[str, List[Event]] = defaultdict(list)
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    # --- sessions ----------------------------------------------------------
    async def upsert_session(self, info: SessionInfo) -> None:
        async with self._lock:
            self._sessions[info.session_id] = info

    def get_session(self, session_id: str) -> SessionInfo | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[SessionInfo]:
        return sorted(self._sessions.values(), key=lambda s: s.started_ms, reverse=True)

    def get_events(self, session_id: str) -> List[Event]:
        return list(self._events.get(session_id, []))

    # --- events / pub-sub --------------------------------------------------
    async def publish(self, event: Event) -> None:
        async with self._lock:
            self._events[event.session_id].append(event)
            # Update session lifecycle from events.
            if event.type == EventType.SESSION_START:
                p = event.payload
                self._sessions[event.session_id] = SessionInfo(
                    session_id=event.session_id,
                    candidate=p.get("candidate", ""),
                    role=p.get("role", ""),
                    phone=p.get("phone", ""),
                )
            elif event.type == EventType.SESSION_END:
                s = self._sessions.get(event.session_id)
                if s:
                    s.status = "completed"
                    s.ended_ms = event.ts_ms
                    s.score = event.payload.get("score")
            subscribers = list(self._subscribers)

        for q in subscribers:
            # Non-blocking; drop if a slow client's queue is full.
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)


# A process-wide default store the API and drivers share.
STORE = SessionStore()
