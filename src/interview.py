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

from .filters import check_input
from .questionbank import Role
from .reasoner import ACTION_FOLLOW_UP, Reasoner


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
        if not role.questions:
            raise ValueError(f"Role {role.id!r} has no questions")

        self.role = role
        self.candidate_name = candidate_name
        self.reasoner = reasoner
        self.max_followups = max_followups

        self._index = 0
        self._followups_used = 0
        self._state = State.GREETING

    def is_finished(self) -> bool:
        return self._state == State.DONE

    def first_prompt(self) -> str:
        """Greeting + first question; move to LISTENING."""
        greeting = default_greeting(self.candidate_name, self.role.title)
        first_question = self.role.questions[self._index].text
        self._state = State.LISTENING
        return f"{greeting} {first_question}"

    def handle_answer(self, answer_text: str) -> AgentAction:
        """Filter -> reason -> enforce cap/advance -> AgentAction."""
        if self._state != State.LISTENING:
            raise RuntimeError(f"handle_answer called in state {self._state}")

        filter_result = check_input(answer_text)
        if not filter_result.allow:
            # Skeleton stub always allows; keep the seam ready for future
            # screening logic without needing a state-machine change.
            pass

        current_question = self.role.questions[self._index]

        decision = None
        if self.reasoner is not None and self._followups_used < self.max_followups:
            decision = self.reasoner.decide(
                role_title=self.role.title,
                question_text=current_question.text,
                category=current_question.category,
                probe_hint=current_question.probe_hint,
                answer=answer_text,
                followups_used=self._followups_used,
                max_followups=self.max_followups,
            )

        if (
            decision is not None
            and decision.action == ACTION_FOLLOW_UP
            and decision.follow_up_question
            and self._followups_used < self.max_followups
        ):
            self._followups_used += 1
            return AgentAction(kind=ActionKind.SPEAK, text=decision.follow_up_question)

        # Advance to the next question.
        self._index += 1
        self._followups_used = 0

        if self._index >= len(self.role.questions):
            self._state = State.DONE
            return AgentAction(kind=ActionKind.END, text=CLOSING)

        next_question = self.role.questions[self._index].text
        return AgentAction(kind=ActionKind.SPEAK, text=next_question)
