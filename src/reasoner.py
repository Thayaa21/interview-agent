"""Claude follow-up reasoner.  [SKELETON]

Owner: Rishi.

After each answer, ask Claude one bounded question: follow up, or advance?
The InterviewController enforces the follow-up cap + ordering in code — the
reasoner only advises and supplies follow-up wording.

TODO(Rishi):
  * implement ClaudeReasoner.decide() (call Anthropic Messages API, expect a
    JSON decision, parse it),
  * implement parse_decision() defensively,
  * FAIL SAFE: on any API/parse error, return an `advance` Decision so a
    candidate is never trapped on a question.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

ACTION_FOLLOW_UP = "follow_up"
ACTION_ADVANCE = "advance"


@dataclass(frozen=True)
class Decision:
    action: str
    follow_up_question: Optional[str] = None
    reason: str = ""


class Reasoner(Protocol):
    """Interface so the controller can accept a real or fake reasoner."""

    def decide(
        self,
        role_title: str,
        question_text: str,
        category: str,
        probe_hint: Optional[str],
        answer: str,
        followups_used: int,
        max_followups: int,
    ) -> Decision: ...


def parse_decision(raw_text: str) -> Decision:
    """Parse Claude's JSON into a Decision; default to advance on failure.
    TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement parse_decision")


class ClaudeReasoner:
    """Reasoner backed by the Anthropic Messages API. TODO(Rishi)."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5", max_tokens: int = 300):
        # TODO(Rishi): construct the Anthropic client (lazy import).
        raise NotImplementedError("TODO(Rishi): implement ClaudeReasoner.__init__")

    def decide(self, role_title, question_text, category, probe_hint, answer, followups_used, max_followups) -> Decision:
        # TODO(Rishi): build prompt, call the API, parse_decision(response),
        #              fail safe to advance on error.
        raise NotImplementedError("TODO(Rishi): implement ClaudeReasoner.decide")
