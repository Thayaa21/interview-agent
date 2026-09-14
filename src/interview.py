"""Code-driven interview state machine (per candidate, per role).  [SKELETON]

Owner: Rishi.

InterviewController owns interview progression for one candidate:
  * greet the candidate by name + state the role,
  * ask the role's preset questions in order (role-specific then behavioral),
  * consult the reasoner for a bounded follow-up decision after each answer,
  * enforce the follow-up cap + question ordering IN CODE,
  * close gracefully after the last question.

The LLM only advises; the machine guarantees flow and the max-follow-up limit.

TODO(Rishi): implement first_prompt() and handle_answer(). handle_answer must:
  1. run the input filter (filters.check_input),
  2. ask the reasoner (follow up or advance),
  3. enforce max_followups + advance the index in code,
  4. return an AgentAction (SPEAK next line, or END with the closing).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .questionbank import Role
from .reasoner import Reasoner


def default_greeting(candidate_name: str, role_title: str) -> str:
    return (
        f"Hi {candidate_name}, this is the automated screening assistant calling "
        f"from Soliant about the {role_title} position. I'll ask a few questions "
        f"one at a time — please answer out loud. Let's begin."
    )


CLOSING = (
    "That's all the questions I have. Thank you for your time — a Soliant "
    "recruiter will follow up with next steps. Goodbye."
)


class State(str, Enum):
    GREETING = "greeting"
    LISTENING = "listening"
    DONE = "done"


class ActionKind(str, Enum):
    SPEAK = "speak"  # say text, keep listening
    END = "end"      # say closing, then hang up


@dataclass(frozen=True)
class AgentAction:
    kind: ActionKind
    text: str


class InterviewController:
    def __init__(
        self,
        role: Role,
        candidate_name: str,
        reasoner: Optional[Reasoner] = None,
        max_followups: int = 2,
    ):
        # TODO(Rishi): validate role has questions; init index/followups/state.
        raise NotImplementedError("TODO(Rishi): implement InterviewController.__init__")

    def is_finished(self) -> bool:
        raise NotImplementedError("TODO(Rishi): implement is_finished")

    def first_prompt(self) -> str:
        """Greeting + first question; move to LISTENING. TODO(Rishi)."""
        raise NotImplementedError("TODO(Rishi): implement first_prompt")

    def handle_answer(self, answer_text: str) -> AgentAction:
        """Filter -> reason -> enforce cap/advance -> AgentAction. TODO(Rishi)."""
        raise NotImplementedError("TODO(Rishi): implement handle_answer")
