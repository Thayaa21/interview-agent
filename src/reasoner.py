"""Follow-up reasoner.  [SKELETON]

Owner: Rishi.

After each answer, ask the LLM one bounded question: follow up, or advance?
The InterviewController enforces the follow-up cap + ordering in code — the
reasoner only advises and supplies follow-up wording.

LLM: OpenAI GPT-4o for now (we have an OpenAI API key). The provider is
deliberately isolated to this module so it can be swapped later.

TODO(Rishi):
  * implement OpenAIReasoner.decide() (call the OpenAI Chat Completions API with
    model gpt-4o, expect a JSON decision, parse it),
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
    """Parse the LLM's JSON into a Decision; default to advance on failure.
    TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement parse_decision")


class OpenAIReasoner:
    """Reasoner backed by the OpenAI Chat Completions API (GPT-4o). TODO(Rishi)."""

    def __init__(self, api_key: str, model: str = "gpt-4o", max_tokens: int = 300):
        # TODO(Rishi): construct the OpenAI client (lazy import: from openai import OpenAI).
        raise NotImplementedError("TODO(Rishi): implement OpenAIReasoner.__init__")

    def decide(self, role_title, question_text, category, probe_hint, answer, followups_used, max_followups) -> Decision:
        # TODO(Rishi): build prompt, call the API (model=gpt-4o), parse_decision(response),
        #              fail safe to advance on error.
        raise NotImplementedError("TODO(Rishi): implement OpenAIReasoner.decide")
