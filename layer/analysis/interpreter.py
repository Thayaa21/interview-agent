"""Answer interpreter — map a completed behavioral answer to JD criteria.

For each question we defined behavioral criteria (criteria.yaml, from the JD).
The interpreter reads the candidate's assembled answer and, for each criterion,
decides: MET / PARTIAL / NOT_MET / NOT_ADDRESSED, with a confidence and a short
evidence note. It then rolls those up into a per-answer score.

Two backends behind one interface (Interpreter protocol):
  * HeuristicInterpreter — deterministic keyword/structure scoring. No API keys.
    Powers the demo out of the box and is fully testable.
  * OpenAIInterpreter    — LLM-based semantic mapping via OpenAI GPT-4o.
    PLACEHOLDER for now (call not wired yet); falls back to heuristic until
    enabled, so the demo works without it.

Runs POST-ANSWER (per user's choice): called once per completed answer, in real
time, so results stream to the dashboard as the interview proceeds.
"""

from __future__ import annotations

import json
import logging
import re
from typing import List, Optional, Protocol

from ..types import AnswerAnalysis, CriterionResult, CriterionStatus
from .criteria import Criterion, QuestionCriteria

logger = logging.getLogger(__name__)

_STATUS_WEIGHT = {
    CriterionStatus.MET: 1.0,
    CriterionStatus.PARTIAL: 0.5,
    CriterionStatus.NOT_MET: 0.0,
    CriterionStatus.NOT_ADDRESSED: 0.0,
}


def _rollup_score(results: List[CriterionResult]) -> float:
    if not results:
        return 0.0
    total = sum(_STATUS_WEIGHT[r.status] for r in results)
    return round(total / len(results), 3)


class Interpreter(Protocol):
    def interpret(
        self, question_id: str, question_text: str, answer_text: str, qc: QuestionCriteria
    ) -> AnswerAnalysis: ...


# --- Heuristic (no API keys) -----------------------------------------------
class HeuristicInterpreter:
    """Deterministic scorer: signal hits + answer substance decide each status.

    Logic per criterion:
      * count how many of the criterion's `signals` appear in the answer,
      * combine with overall answer substance (length/specificity),
      * MET if strong signal presence, PARTIAL if weak, NOT_ADDRESSED if none.
    Intended as a sensible, explainable baseline — not a replacement for the LLM.
    """

    def interpret(self, question_id, question_text, answer_text, qc: QuestionCriteria) -> AnswerAnalysis:
        answer = answer_text.strip()
        low = answer.lower()
        word_count = len(re.findall(r"\w+", low))
        results: List[CriterionResult] = []

        for c in qc.criteria:
            hits = [s for s in c.signals if s in low]
            n = len(hits)
            if n == 0:
                # No signal at all -> did they at least say something substantial?
                status = CriterionStatus.NOT_ADDRESSED if word_count < 8 else CriterionStatus.NOT_MET
                conf = 0.5
                evidence = ""
            elif n == 1 and word_count < 25:
                status = CriterionStatus.PARTIAL
                conf = 0.55
                evidence = f"mentions: {hits[0]}"
            else:
                status = CriterionStatus.MET
                conf = min(0.6 + 0.1 * n, 0.9)
                evidence = "mentions: " + ", ".join(hits[:3])

            results.append(
                CriterionResult(
                    criterion_id=c.id, label=c.label, status=status,
                    confidence=round(conf, 2), evidence=evidence,
                )
            )

        score = _rollup_score(results)
        summary = self._summary(qc.competency, results, score)
        return AnswerAnalysis(
            question_id=question_id, question_text=question_text,
            answer_text=answer, criteria=results, summary=summary, score=score,
        )

    @staticmethod
    def _summary(competency: str, results: List[CriterionResult], score: float) -> str:
        met = sum(1 for r in results if r.status == CriterionStatus.MET)
        return f"{competency}: {met}/{len(results)} criteria met (score {score:.0%})."


# --- OpenAI GPT-4o (semantic) ----------------------------------------------
# LLM backend is OpenAI GPT-4o (we have an OpenAI key). The actual API call is
# left as a PLACEHOLDER for now — until it's wired, this backend transparently
# uses the HeuristicInterpreter, so the dashboard/demo keeps working with no key.
# The prompt + JSON parsing (_parse) are ready for when the call is added.
_SYSTEM = (
    "You evaluate a candidate's spoken interview answer against a set of "
    "behavioral criteria for a healthcare staffing role. For each criterion, "
    "decide met / partial / not_met / not_addressed based ONLY on the answer. "
    "Be strict: reward specificity and concrete actions; penalize vague or "
    "generic answers. Respond with a single JSON object only."
)


def _build_prompt(question_text: str, answer_text: str, qc: QuestionCriteria) -> str:
    crit_lines = "\n".join(f'- {c.id}: {c.label}' for c in qc.criteria)
    return (
        f"Competency: {qc.competency}\n"
        f"Question: {question_text}\n\n"
        f"Criteria:\n{crit_lines}\n\n"
        f'Candidate answer:\n"""{answer_text.strip() or "(no answer)"}"""\n\n'
        'Respond with ONLY JSON:\n'
        '{"criteria": [{"id": "<criterion_id>", "status": "met|partial|not_met|not_addressed", '
        '"confidence": 0.0-1.0, "evidence": "<short quote/paraphrase>"}], '
        '"summary": "<one sentence>"}'
    )


class OpenAIInterpreter:
    """LLM interpreter backed by OpenAI GPT-4o.

    PLACEHOLDER: the API call is not wired yet (will be added later). Until then
    it falls back to the heuristic interpreter, so nothing breaks. To enable it,
    implement `_call_llm()` with the OpenAI Chat Completions API (model gpt-4o,
    system=_SYSTEM, user=_build_prompt(...), JSON response) and return the raw
    text; `_parse()` below already turns that into an AnswerAnalysis.
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4o", max_tokens: int = 600):
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._fallback = HeuristicInterpreter()

    def _call_llm(self, question_text: str, answer_text: str, qc: QuestionCriteria) -> str:
        # TODO(later): wire the OpenAI GPT-4o call and return the raw JSON text.
        #   from openai import OpenAI
        #   client = OpenAI(api_key=self._api_key)
        #   resp = client.chat.completions.create(
        #       model=self._model, max_tokens=self._max_tokens,
        #       response_format={"type": "json_object"},
        #       messages=[{"role": "system", "content": _SYSTEM},
        #                 {"role": "user", "content": _build_prompt(question_text, answer_text, qc)}])
        #   return resp.choices[0].message.content
        raise NotImplementedError("OpenAI GPT-4o call not wired yet")

    def interpret(self, question_id, question_text, answer_text, qc: QuestionCriteria) -> AnswerAnalysis:
        try:
            text = self._call_llm(question_text, answer_text, qc)
            return self._parse(question_id, question_text, answer_text, qc, text)
        except Exception as exc:  # noqa: BLE001 - never break the interview
            logger.warning("OpenAIInterpreter unavailable (%s); using heuristic.", exc)
            return self._fallback.interpret(question_id, question_text, answer_text, qc)

    def _parse(self, question_id, question_text, answer_text, qc: QuestionCriteria, raw: str) -> AnswerAnalysis:
        try:
            obj = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            return self._fallback.interpret(question_id, question_text, answer_text, qc)

        by_id = {c["id"]: c for c in obj.get("criteria", []) if isinstance(c, dict)}
        results: List[CriterionResult] = []
        for c in qc.criteria:
            item = by_id.get(c.id, {})
            status = _coerce_status(item.get("status"))
            conf = item.get("confidence", 0.5)
            conf = float(conf) if isinstance(conf, (int, float)) else 0.5
            results.append(
                CriterionResult(
                    criterion_id=c.id, label=c.label, status=status,
                    confidence=round(max(0.0, min(1.0, conf)), 2),
                    evidence=str(item.get("evidence", ""))[:200],
                )
            )
        score = _rollup_score(results)
        summary = str(obj.get("summary", "")) or f"{qc.competency}: score {score:.0%}."
        return AnswerAnalysis(
            question_id=question_id, question_text=question_text,
            answer_text=answer_text.strip(), criteria=results, summary=summary, score=score,
        )


def _coerce_status(v) -> CriterionStatus:
    try:
        return CriterionStatus(str(v).strip().lower())
    except ValueError:
        return CriterionStatus.NOT_ADDRESSED
