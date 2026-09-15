"""Interview pipeline orchestrator.

Ties the layer together for one session:

  candidate speech fragments
        -> TurnAssembler (stitch multi-sentence answer)
        -> GuardrailEngine.check_input (scope/injection/budgets)
             * ALLOW    -> InterviewController-style advance (question flow)
                        -> Interpreter.interpret (map answer to JD criteria)
             * REDIRECT -> speak redirect, re-ask, DON'T advance
             * BLOCK    -> speak safe line, DON'T advance
             * END      -> speak closing, end call
        -> GuardrailEngine.sanction_output on every agent line
        -> emit Events (turn / guardrail / analysis) to the store

This is transport-agnostic. The mock driver feeds it scripted fragments; the
live agent (Rishi's src/) can feed it real STT fragments + end-of-turn signals
using the same methods. It does NOT import from src/ — it takes the question
list + criteria as plain data, so the two layers stay decoupled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .analysis.criteria import QuestionCriteria
from .analysis.interpreter import Interpreter, HeuristicInterpreter
from .compliance.guardrails import GuardrailEngine
from .types import (
    AnswerAnalysis,
    Event,
    EventType,
    GuardResult,
    GuardVerdict,
    Speaker,
    now_ms,
)


@dataclass
class PipelineQuestion:
    id: str
    text: str
    kind: str = "question"  # "question" (from bank) — sanctioned output kind


# Emit callback: receives an Event to publish (sync wrapper; the driver adapts
# it to async publish).
EmitFn = Callable[[Event], None]


class InterviewPipeline:
    def __init__(
        self,
        session_id: str,
        questions: List[PipelineQuestion],
        criteria: Dict[str, QuestionCriteria],
        guardrails: GuardrailEngine,
        interpreter: Optional[Interpreter] = None,
        emit: Optional[EmitFn] = None,
    ):
        self.session_id = session_id
        self._questions = questions
        self._criteria = criteria
        self._guard = guardrails
        self._interp = interpreter or HeuristicInterpreter()
        self._emit = emit or (lambda ev: None)

        self.index = 0
        self.finished = False
        self.scores: List[float] = []

    # --- helpers -----------------------------------------------------------
    def _emit_event(self, etype: EventType, payload: dict) -> None:
        self._emit(Event(type=etype, session_id=self.session_id, payload=payload))

    def _current(self) -> Optional[PipelineQuestion]:
        return self._questions[self.index] if self.index < len(self._questions) else None

    def _speak(self, kind: str, text: str) -> str:
        """Sanction, then emit an agent turn. Returns the text actually spoken."""
        res = self._guard.sanction_output(kind, text)
        spoken = text
        if res.verdict == GuardVerdict.BLOCK:
            spoken = res.replacement or "Let's continue."
            self._emit_event(EventType.GUARDRAIL, {
                "stage": "output", **res.to_dict(), "attempted": text,
            })
        self._emit_event(EventType.TURN, {
            "speaker": Speaker.AGENT.value, "kind": kind, "text": spoken,
        })
        return spoken

    # --- lifecycle ---------------------------------------------------------
    def start(self, candidate: str, role: str, phone: str = "") -> str:
        self._emit_event(EventType.SESSION_START, {
            "candidate": candidate, "role": role, "phone": phone,
        })
        greeting = (
            f"Hi {candidate}, this is the automated screening assistant from "
            f"Soliant. I'll ask a few questions one at a time. Let's begin."
        )
        self._speak("greeting", greeting)
        q = self._current()
        return self._speak("question", q.text) if q else self._close()

    def _close(self, message: Optional[str] = None) -> str:
        self.finished = True
        closing = message or (
            "That's all the questions I have. Thank you for your time — a Soliant "
            "recruiter will follow up. Goodbye."
        )
        spoken = self._speak("closing", closing)
        overall = round(sum(self.scores) / len(self.scores), 3) if self.scores else 0.0
        self._emit_event(EventType.SESSION_END, {"score": overall})
        return spoken

    # --- the main entry: a completed candidate answer ----------------------
    def submit_answer(self, answer_text: str) -> str:
        """Process one COMPLETE candidate answer (already assembled).

        Returns the agent's next spoken line.
        """
        if self.finished:
            return ""

        # Log the candidate turn.
        self._emit_event(EventType.TURN, {
            "speaker": Speaker.CANDIDATE.value, "text": answer_text,
        })

        # Budgets first (turn/time) — hard caps.
        for budget in (self._guard.check_turn_budget(), self._guard.check_time_budget()):
            if budget.verdict == GuardVerdict.END:
                self._emit_event(EventType.GUARDRAIL, {"stage": "budget", **budget.to_dict()})
                return self._close(budget.replacement)

        # Input guardrail.
        gin = self._guard.check_input(answer_text)
        if gin.verdict != GuardVerdict.ALLOW:
            self._emit_event(EventType.GUARDRAIL, {"stage": "input", **gin.to_dict()})
            if gin.verdict == GuardVerdict.END:
                return self._close(gin.replacement)
            # REDIRECT or BLOCK: speak the safe line and re-ask; do NOT advance.
            self._speak("redirect", gin.replacement or "Let's continue.")
            q = self._current()
            return self._speak("question", q.text) if q else self._close()

        # On-topic: interpret the answer against this question's criteria.
        q = self._current()
        if q is not None:
            qc = self._criteria.get(q.id)
            if qc is not None:
                analysis = self._interp.interpret(q.id, q.text, answer_text, qc)
                self.scores.append(analysis.score)
                self._emit_event(EventType.ANALYSIS, analysis.to_dict())

        # Advance to the next question (this demo layer does not itself run
        # follow-ups; the live agent's InterviewController owns that and would
        # call submit_answer again for a follow-up answer).
        self.index += 1
        nxt = self._current()
        if nxt is None:
            return self._close()
        return self._speak("question", nxt.text)
