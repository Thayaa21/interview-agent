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

import json
import re
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


_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_decision(raw_text: str) -> Decision:
    """Parse the LLM's JSON into a Decision; default to advance on failure."""
    try:
        match = _JSON_BLOCK_RE.search(raw_text)
        if match is None:
            return Decision(action=ACTION_ADVANCE, reason="no JSON found in model output")

        data = json.loads(match.group(0))
        action = data.get("action")
        if action not in (ACTION_FOLLOW_UP, ACTION_ADVANCE):
            return Decision(action=ACTION_ADVANCE, reason=f"invalid action: {action!r}")

        follow_up_question = data.get("follow_up_question")
        if action == ACTION_FOLLOW_UP and not follow_up_question:
            return Decision(action=ACTION_ADVANCE, reason="follow_up with no question text")

        return Decision(
            action=action,
            follow_up_question=follow_up_question,
            reason=data.get("reason", ""),
        )
    except Exception as e:
        return Decision(action=ACTION_ADVANCE, reason=f"parse error: {e}")


class OpenAIReasoner:
    """Reasoner backed by the OpenAI Chat Completions API (GPT-4o)."""

    def __init__(self, api_key: str, model: str = "gpt-4o", max_tokens: int = 300):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def decide(self, role_title, question_text, category, probe_hint, answer, followups_used, max_followups) -> Decision:
        if followups_used >= max_followups:
            return Decision(action=ACTION_ADVANCE, reason="follow-up cap reached")

        prompt = (
            f"You are assisting with a phone interview for the role of {role_title}.\n"
            f"Question ({category}): {question_text}\n"
            + (f"What to listen for: {probe_hint}\n" if probe_hint else "")
            + f"Candidate's answer: {answer}\n\n"
            f"Follow-ups used so far for this question: {followups_used} of {max_followups} allowed.\n\n"
            "Decide whether the answer needs one short follow-up question to get a "
            "clearer or more complete response, or whether we should advance to the "
            "next interview question. Respond with ONLY a JSON object of the form "
            '{"action": "follow_up" | "advance", "follow_up_question": "<text or null>", '
            '"reason": "<short reason>"}.'
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=self._max_tokens,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.choices[0].message.content or ""
            return parse_decision(raw_text)
        except Exception as e:
            return Decision(action=ACTION_ADVANCE, reason=f"reasoner error: {e}")
