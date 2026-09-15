"""Turn assembler — stitch multi-sentence spoken answers into one answer.

Problem: a candidate answers in several sentences with pauses. Streaming STT
emits many partial and final fragments. A pause mid-thought must NOT be treated
as "they finished." We only consider the answer complete when EITHER:

  * the pipeline signals a hard end-of-turn (VAD + turn detector), OR
  * a debounce window passes with no new speech after the last fragment
    (a natural "they've stopped for good" gap).

This component is transport-agnostic: feed it fragments + timestamps and ask it
whether the turn is complete. It works identically for the live LiveKit pipeline
and for mock/recorded transcripts.

Typical wiring (live):
  * on interim STT result:  add_partial(text, ts)
  * on final STT result:    add_final(text, ts)
  * on end-of-turn signal:  mark_end_of_turn()  -> then assemble()
  * or poll should_finalize(now) using the debounce timer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class _Fragment:
    text: str
    ts_ms: int
    is_final: bool


@dataclass
class TurnAssembler:
    # How long to wait (ms) after the last fragment with no new speech before we
    # decide the turn is complete on our own (used when no hard end-of-turn
    # signal arrives). Tuned to tolerate natural mid-answer pauses.
    debounce_ms: int = 1500
    # Ignore trailing fragments shorter than this many chars when they are just
    # filler ("um", "uh") — kept simple; real filtering can grow later.
    _fragments: List[_Fragment] = field(default_factory=list)
    _end_of_turn: bool = False
    _last_ts: int = 0

    # --- ingest ------------------------------------------------------------
    def add_partial(self, text: str, ts_ms: int) -> None:
        """A non-final interim transcript. Replaces the trailing partial."""
        text = text.strip()
        if not text:
            return
        # Keep only one trailing partial; finals accumulate.
        if self._fragments and not self._fragments[-1].is_final:
            self._fragments[-1] = _Fragment(text, ts_ms, False)
        else:
            self._fragments.append(_Fragment(text, ts_ms, False))
        self._last_ts = ts_ms

    def add_final(self, text: str, ts_ms: int) -> None:
        """A finalized STT segment (one sentence/phrase). Accumulates."""
        text = text.strip()
        if not text:
            return
        # Drop a trailing partial that the final supersedes.
        if self._fragments and not self._fragments[-1].is_final:
            self._fragments.pop()
        self._fragments.append(_Fragment(text, ts_ms, True))
        self._last_ts = ts_ms

    def mark_end_of_turn(self) -> None:
        """Hard signal from VAD/turn-detector that the candidate is done."""
        self._end_of_turn = True

    # --- decide ------------------------------------------------------------
    def should_finalize(self, now_ms: int) -> bool:
        """True when the turn is complete (hard signal or debounce elapsed)."""
        if not self._has_content():
            return False
        if self._end_of_turn:
            return True
        return (now_ms - self._last_ts) >= self.debounce_ms

    def _has_content(self) -> bool:
        return any(f.text for f in self._fragments)

    # --- assemble ----------------------------------------------------------
    def assemble(self) -> str:
        """Join fragments into one clean answer string."""
        parts = [f.text for f in self._fragments if f.text]
        joined = " ".join(parts)
        # Collapse whitespace and de-duplicate a repeated trailing partial/final.
        joined = " ".join(joined.split())
        return joined

    def reset(self) -> None:
        self._fragments.clear()
        self._end_of_turn = False
        self._last_ts = 0
