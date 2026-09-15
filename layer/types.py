"""Shared types across the compliance + intelligence layer.

These are deliberately plain dataclasses with `to_dict()` so they serialize
cleanly to JSON for the API/WebSocket and the dashboard.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def now_ms() -> int:
    return int(time.time() * 1000)


# --- Speakers ---------------------------------------------------------------
class Speaker(str, Enum):
    AGENT = "agent"
    CANDIDATE = "candidate"
    SYSTEM = "system"  # guardrail / system events


# --- Guardrail outcomes -----------------------------------------------------
class GuardVerdict(str, Enum):
    ALLOW = "allow"          # input on-topic / output sanctioned
    REDIRECT = "redirect"    # off-topic input -> steer back
    BLOCK = "block"          # unsafe/injection input or non-sanctioned output
    END = "end"              # budget exceeded / repeated abuse -> end call


@dataclass
class GuardResult:
    verdict: GuardVerdict
    reason: str = ""
    rule_id: str = ""
    # Replacement text to speak instead (for REDIRECT/BLOCK on output, or the
    # redirect line for off-topic input).
    replacement: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


# --- Criteria interpretation ------------------------------------------------
class CriterionStatus(str, Enum):
    MET = "met"
    PARTIAL = "partial"
    NOT_MET = "not_met"
    NOT_ADDRESSED = "not_addressed"


@dataclass
class CriterionResult:
    criterion_id: str
    label: str
    status: CriterionStatus
    confidence: float               # 0..1
    evidence: str = ""              # short quote/paraphrase supporting the status

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class AnswerAnalysis:
    """Result of mapping one complete answer to a question's criteria."""

    question_id: str
    question_text: str
    answer_text: str
    criteria: List[CriterionResult] = field(default_factory=list)
    summary: str = ""
    score: float = 0.0              # 0..1 rollup for this answer

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "answer_text": self.answer_text,
            "criteria": [c.to_dict() for c in self.criteria],
            "summary": self.summary,
            "score": self.score,
        }


# --- Events (streamed to the dashboard) -------------------------------------
class EventType(str, Enum):
    SESSION_START = "session_start"
    TURN = "turn"                    # a completed turn (agent or candidate)
    PARTIAL = "partial"              # in-progress candidate transcript fragment
    GUARDRAIL = "guardrail"          # a guardrail decision
    ANALYSIS = "analysis"            # an AnswerAnalysis for a completed answer
    SESSION_END = "session_end"


@dataclass
class Event:
    type: EventType
    session_id: str
    ts_ms: int = field(default_factory=now_ms)
    payload: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: new_id("ev_"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "session_id": self.session_id,
            "ts_ms": self.ts_ms,
            "payload": self.payload,
        }


@dataclass
class SessionInfo:
    session_id: str
    candidate: str
    role: str
    phone: str = ""
    started_ms: int = field(default_factory=now_ms)
    ended_ms: Optional[int] = None
    status: str = "active"   # active | completed
    score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
