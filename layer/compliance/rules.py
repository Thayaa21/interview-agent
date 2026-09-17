"""Rulebook loader.

Parses rulebook.yaml into a typed Rulebook object. Rules are data; the
guardrails engine (guardrails.py) enforces them. Keeping this separate means
non-engineers can tune scope, banned topics, budgets, and messages without
touching enforcement code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

import yaml

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rulebook.yaml")


class RulebookError(RuntimeError):
    pass


@dataclass(frozen=True)
class OutputLimits:
    followup_max_chars: int = 240
    followup_must_end_with_question_mark: bool = True
    banned_output_substrings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Budgets:
    max_followups_per_question: int = 2
    max_total_turns: int = 60
    max_call_seconds: int = 900
    max_offtopic_before_end: int = 3


@dataclass(frozen=True)
class Messages:
    redirect: str = ""
    redirect_final: str = ""
    blocked_injection: str = ""
    end_offtopic: str = ""
    output_blocked_fallback: str = ""


@dataclass(frozen=True)
class Policy:
    """The single source of truth for scope — read by BOTH the classifier and
    the agent's instructions."""

    purpose: str = ""
    allowed: List[str] = field(default_factory=list)
    not_allowed: List[str] = field(default_factory=list)

    def as_text(self) -> str:
        """Render the policy as plain text for prompts (classifier + agent)."""
        allowed = "\n".join(f"  - {a}" for a in self.allowed)
        not_allowed = "\n".join(f"  - {n}" for n in self.not_allowed)
        return (
            f"{self.purpose.strip()}\n\n"
            f"ALLOWED (on-topic):\n{allowed}\n\n"
            f"NOT ALLOWED (off-topic or role-change attempts):\n{not_allowed}"
        )


@dataclass(frozen=True)
class Rulebook:
    policy: Policy
    off_topic_signals: List[str]
    injection_signals: List[str]
    allowed_output_kinds: List[str]
    output_limits: OutputLimits
    budgets: Budgets
    messages: Messages

    # Back-compat: some code reads .purpose directly.
    @property
    def purpose(self) -> str:
        return self.policy.purpose


def load_rulebook(path: str | None = None) -> Rulebook:
    path = path or _DEFAULT_PATH
    if not os.path.exists(path):
        raise RulebookError(f"Rulebook not found at {path!r}.")
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise RulebookError(f"Could not parse rulebook {path!r}: {exc}") from exc

    pol = data.get("policy", {}) or {}
    ol = data.get("output_limits", {}) or {}
    bg = data.get("budgets", {}) or {}
    ms = data.get("messages", {}) or {}

    return Rulebook(
        policy=Policy(
            purpose=(pol.get("purpose") or "").strip(),
            allowed=list(pol.get("allowed") or []),
            not_allowed=list(pol.get("not_allowed") or []),
        ),
        # off_topic_signals kept for back-compat; the classifier is primary now.
        off_topic_signals=[s.lower() for s in (data.get("off_topic_signals") or [])],
        injection_signals=[s.lower() for s in (data.get("injection_signals") or [])],
        allowed_output_kinds=list(data.get("allowed_output_kinds") or []),
        output_limits=OutputLimits(
            followup_max_chars=int(ol.get("followup_max_chars", 240)),
            followup_must_end_with_question_mark=bool(ol.get("followup_must_end_with_question_mark", True)),
            banned_output_substrings=[s.lower() for s in (ol.get("banned_output_substrings") or [])],
        ),
        budgets=Budgets(
            max_followups_per_question=int(bg.get("max_followups_per_question", 2)),
            max_total_turns=int(bg.get("max_total_turns", 60)),
            max_call_seconds=int(bg.get("max_call_seconds", 900)),
            max_offtopic_before_end=int(bg.get("max_offtopic_before_end", 3)),
        ),
        messages=Messages(
            redirect=ms.get("redirect", ""),
            redirect_final=ms.get("redirect_final", ""),
            blocked_injection=ms.get("blocked_injection", ""),
            end_offtopic=ms.get("end_offtopic", ""),
            output_blocked_fallback=ms.get("output_blocked_fallback", ""),
        ),
    )
