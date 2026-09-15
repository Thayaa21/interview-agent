"""Headless smoke test: run a mock call through the full pipeline and print
every event. No FastAPI, no frontend, no API keys — proves the layer works.

Run:  python -m layer.smoke_test [role]
"""

from __future__ import annotations

import asyncio
import sys

from .server.mock_driver import run_mock_call
from .server.store import SessionStore
from .types import Event, EventType


async def main(role: str) -> None:
    store = SessionStore()
    q = store.subscribe()
    done = asyncio.Event()

    async def printer():
        while not done.is_set() or not q.empty():
            try:
                ev: Event = await asyncio.wait_for(q.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            _print_event(ev)

    printer_task = asyncio.create_task(printer())
    await run_mock_call("Alex Taylor" if role == "oncology_rn" else "Jordan Pharm",
                        role, session_id=f"smoke_{role}", store=store, speed=20.0)
    await asyncio.sleep(0.6)  # let trailing events flush
    done.set()
    await printer_task


def _print_event(ev: Event) -> None:
    p = ev.payload
    if ev.type == EventType.TURN:
        who = p.get("speaker")
        kind = f"[{p.get('kind')}]" if p.get("kind") else ""
        print(f"  {who:9} {kind:11} {p.get('text','')}")
    elif ev.type == EventType.GUARDRAIL:
        print(f"  >> GUARDRAIL {p.get('stage')}: {p.get('verdict')} ({p.get('reason')})")
    elif ev.type == EventType.ANALYSIS:
        crits = ", ".join(f"{c['criterion_id']}={c['status']}" for c in p.get("criteria", []))
        print(f"  ~~ ANALYSIS {p.get('question_id')}: score={p.get('score')} | {crits}")
    elif ev.type == EventType.SESSION_END:
        print(f"  == SESSION END overall score={p.get('score')}")
    elif ev.type == EventType.SESSION_START:
        print(f"  == SESSION START {p.get('candidate')} / {p.get('role')}")


if __name__ == "__main__":
    role = sys.argv[1] if len(sys.argv) > 1 else "oncology_rn"
    asyncio.run(main(role))
