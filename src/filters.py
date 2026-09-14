"""Input-filter hook.  [SKELETON]

Owner: Rishi.

The single seam where a candidate's transcribed answer is screened before the
interview logic reasons about it. The state machine calls this once per answer
(InterviewController.handle_answer), so logic added here needs no rewiring.

TODO(Rishi): for the skeleton, return allow=True (pass-through). Keep the
             FilterResult contract stable for any future screening logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FilterResult:
    allow: bool
    reason: str = ""


def check_input(text: str, ctx: dict[str, Any] | None = None) -> FilterResult:
    """Screen a candidate's answer. TODO(Rishi): stub -> allow everything."""
    raise NotImplementedError("TODO(Rishi): implement check_input (stub: allow all)")
