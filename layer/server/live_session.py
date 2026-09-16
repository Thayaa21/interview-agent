"""Live (interactive) interview session engine for the browser demo.

Reuses the same InterviewPipeline as the mock driver — so guardrails, criteria
interpretation, and scoring are identical — but instead of feeding scripted
answers, it processes answers submitted one at a time from the browser
("Call me" voice UI: mic -> Web Speech API -> here).

Session lifecycle:
  * start(candidate, role) -> greeting + first question (agent's opening line)
  * answer(text)           -> processes one candidate answer, returns the
                              agent's next line (follow-up / next question /
                              redirect / closing)

Every turn / guardrail / analysis event is published to the shared store so the
dashboard updates live over the WebSocket. Sessions are held in memory keyed by
session_id.

The layer pipeline advances one question per answer (it does not itself run
LLM follow-ups — that's the src/ live agent's job). The answer INTERPRETER uses
OpenAI GPT-4o when OPENAI_API_KEY is set, otherwise the heuristic scorer, so the
demo runs with zero keys.
"""

from __future__ import annotations

import asyncio
import os
from typing import Dict, Optional

from ..analysis.criteria import load_criteria
from ..analysis.interpreter import HeuristicInterpreter, Interpreter, OpenAIInterpreter
from ..compliance.guardrails import GuardrailEngine
from ..compliance.rules import load_rulebook
from ..pipeline import InterviewPipeline, PipelineQuestion
from ..types import Event
from .question_sets import QUESTION_SETS, role_display_name
from .store import STORE, SessionStore


def _make_interpreter() -> Interpreter:
    """GPT-4o interpreter if a key is set, else the heuristic one."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        # OpenAIInterpreter falls back to heuristic internally until its call is
        # wired, so this is always safe.
        return OpenAIInterpreter(api_key=key)
    return HeuristicInterpreter()


class LiveSession:
    """One interactive interview, driven by browser-submitted answers."""

    def __init__(self, session_id: str, candidate: str, role: str, store: SessionStore):
        self.session_id = session_id
        self.candidate = candidate or "there"
        self.role = role
        self._store = store
        self._loop = asyncio.get_event_loop()

        questions = [PipelineQuestion(q["id"], q["text"]) for q in QUESTION_SETS[role]]
        criteria = load_criteria().get(role, {})

        self.pipeline = InterviewPipeline(
            session_id=session_id,
            questions=questions,
            criteria=criteria,
            guardrails=GuardrailEngine(load_rulebook()),
            interpreter=_make_interpreter(),
            emit=self._emit,
        )

    def _emit(self, ev: Event) -> None:
        # Bridge the sync pipeline to the async store (schedule the coroutine).
        asyncio.create_task(self._store.publish(ev))

    def start(self) -> str:
        return self.pipeline.start(candidate=self.candidate, role=self.role)

    def answer(self, text: str) -> str:
        return self.pipeline.submit_answer(text)

    @property
    def finished(self) -> bool:
        return self.pipeline.finished


class LiveSessionManager:
    """Holds active browser sessions keyed by session_id."""

    def __init__(self, store: SessionStore = STORE):
        self._store = store
        self._sessions: Dict[str, LiveSession] = {}

    def create(self, session_id: str, candidate: str, role: str) -> LiveSession:
        if role not in QUESTION_SETS:
            raise ValueError(f"Unknown role {role!r}. Known: {list(QUESTION_SETS)}")
        session = LiveSession(session_id, candidate, role, self._store)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[LiveSession]:
        return self._sessions.get(session_id)

    def roles(self) -> list[dict]:
        return [{"id": r, "title": role_display_name(r)} for r in QUESTION_SETS]


MANAGER = LiveSessionManager()
