"""Guardrails engine — enforces the rulebook in code.

Three enforcement points, all code-driven so they survive context growth (the
"pancake recipe after a long chat" failure mode):

  1. check_input(text)   — screen a candidate turn BEFORE the LLM reasons about
                           it. Detects prompt-injection (BLOCK) and off-topic
                           input (REDIRECT), and escalates to END after repeated
                           off-topic turns.
  2. sanction_output(kind, text) — verify a line the agent is about to SPEAK is
                           one of the sanctioned kinds and passes output limits.
                           A non-sanctioned line is blocked and replaced with a
                           safe fallback. This is the hard stop that prevents the
                           agent from ever saying something off-scope, no matter
                           what the model generated.
  3. budgets             — check_turn_budget / check_time_budget enforce hard
                           caps on turns and call duration.

The engine keeps per-session counters (off-topic count, turn count, start time).

An optional `classifier` callable can be injected for LLM-based intent
classification; if none is given, the engine uses fast keyword rules from the
rulebook. Both paths are code-authoritative — the classifier only advises.
"""

from __future__ import annotations

import re
import time
from typing import Callable, Optional

from ..types import GuardResult, GuardVerdict
from .rules import Rulebook, load_rulebook

# A classifier takes (text, rulebook) and returns one of:
#   "allow" | "off_topic" | "injection"
Classifier = Callable[[str, Rulebook], str]


def _contains_any(text: str, needles) -> Optional[str]:
    low = text.lower()
    for n in needles:
        if n and n in low:
            return n
    return None


class GuardrailEngine:
    def __init__(self, rulebook: Optional[Rulebook] = None, classifier: Optional[Classifier] = None):
        self.rules = rulebook or load_rulebook()
        self._classifier = classifier
        # Per-session state.
        self.offtopic_count = 0
        self.turn_count = 0
        self._start = time.monotonic()

    # --- lifecycle ---------------------------------------------------------
    def reset(self) -> None:
        self.offtopic_count = 0
        self.turn_count = 0
        self._start = time.monotonic()

    # --- 1) INPUT ----------------------------------------------------------
    def check_input(self, text: str) -> GuardResult:
        """Screen a candidate turn. ALLOW / REDIRECT / BLOCK / END."""
        self.turn_count += 1

        # Injection is checked first and always hard-blocked.
        hit = _contains_any(text, self.rules.injection_signals)
        cls = self._classify(text)
        if hit or cls == "injection":
            return GuardResult(
                verdict=GuardVerdict.BLOCK,
                reason=f"injection-signal:{hit}" if hit else "classifier:injection",
                rule_id="injection",
                replacement=self.rules.messages.blocked_injection,
            )

        # Off-topic -> redirect, escalating to END after the budget.
        off = _contains_any(text, self.rules.off_topic_signals)
        if off or cls == "off_topic":
            self.offtopic_count += 1
            if self.offtopic_count >= self.rules.budgets.max_offtopic_before_end:
                return GuardResult(
                    verdict=GuardVerdict.END,
                    reason="offtopic-budget-exceeded",
                    rule_id="offtopic",
                    replacement=self.rules.messages.end_offtopic,
                )
            # Last warning vs. normal redirect.
            final = self.offtopic_count == self.rules.budgets.max_offtopic_before_end - 1
            return GuardResult(
                verdict=GuardVerdict.REDIRECT,
                reason=f"off-topic:{off}" if off else "classifier:off_topic",
                rule_id="offtopic",
                replacement=(self.rules.messages.redirect_final if final
                             else self.rules.messages.redirect),
            )

        return GuardResult(verdict=GuardVerdict.ALLOW, reason="on-topic", rule_id="")

    def _classify(self, text: str) -> str:
        if self._classifier is None:
            return "allow"
        try:
            verdict = self._classifier(text, self.rules)
            return verdict if verdict in ("allow", "off_topic", "injection") else "allow"
        except Exception:  # noqa: BLE001 - classifier must never break the call
            return "allow"

    # --- 2) OUTPUT ---------------------------------------------------------
    def sanction_output(self, kind: str, text: str) -> GuardResult:
        """Verify an agent utterance is sanctioned. ALLOW or BLOCK(+replacement)."""
        limits = self.rules.output_limits

        if kind not in self.rules.allowed_output_kinds:
            return GuardResult(
                verdict=GuardVerdict.BLOCK,
                reason=f"unsanctioned-kind:{kind}",
                rule_id="output_kind",
                replacement=self.rules.messages.output_blocked_fallback,
            )

        banned = _contains_any(text, limits.banned_output_substrings)
        if banned:
            return GuardResult(
                verdict=GuardVerdict.BLOCK,
                reason=f"banned-substring:{banned}",
                rule_id="output_banned",
                replacement=self.rules.messages.output_blocked_fallback,
            )

        # Extra checks specific to generated follow-ups (the only free-form
        # agent output; greeting/question/closing/redirect are fixed strings).
        if kind == "followup":
            if len(text) > limits.followup_max_chars:
                return GuardResult(
                    verdict=GuardVerdict.BLOCK,
                    reason="followup-too-long",
                    rule_id="output_length",
                    replacement=self.rules.messages.output_blocked_fallback,
                )
            if limits.followup_must_end_with_question_mark and not text.strip().endswith("?"):
                return GuardResult(
                    verdict=GuardVerdict.BLOCK,
                    reason="followup-not-a-question",
                    rule_id="output_shape",
                    replacement=self.rules.messages.output_blocked_fallback,
                )

        return GuardResult(verdict=GuardVerdict.ALLOW, reason="sanctioned", rule_id="")

    # --- 3) BUDGETS --------------------------------------------------------
    def check_turn_budget(self) -> GuardResult:
        if self.turn_count >= self.rules.budgets.max_total_turns:
            return GuardResult(
                verdict=GuardVerdict.END,
                reason="turn-budget-exceeded",
                rule_id="budget_turns",
                replacement=self.rules.messages.end_offtopic,
            )
        return GuardResult(verdict=GuardVerdict.ALLOW)

    def check_time_budget(self) -> GuardResult:
        elapsed = time.monotonic() - self._start
        if elapsed >= self.rules.budgets.max_call_seconds:
            return GuardResult(
                verdict=GuardVerdict.END,
                reason="time-budget-exceeded",
                rule_id="budget_time",
                replacement=self.rules.messages.end_offtopic,
            )
        return GuardResult(verdict=GuardVerdict.ALLOW)
