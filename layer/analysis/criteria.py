"""Criteria loading — behavioral competencies mapped from each role's JD."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List

import yaml

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "criteria.yaml")


class CriteriaError(RuntimeError):
    pass


@dataclass(frozen=True)
class Criterion:
    id: str
    label: str
    signals: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class QuestionCriteria:
    question_id: str
    competency: str
    criteria: List[Criterion]


def load_criteria(path: str | None = None) -> Dict[str, Dict[str, QuestionCriteria]]:
    """Return {role_id: {question_id: QuestionCriteria}}."""
    path = path or _DEFAULT_PATH
    if not os.path.exists(path):
        raise CriteriaError(f"Criteria file not found at {path!r}.")
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    out: Dict[str, Dict[str, QuestionCriteria]] = {}
    for role_id, role_block in data.items():
        questions = (role_block or {}).get("questions", {}) or {}
        out[role_id] = {}
        for qid, qblock in questions.items():
            crits = [
                Criterion(id=c["id"], label=c["label"], signals=[s.lower() for s in c.get("signals", [])])
                for c in (qblock.get("criteria") or [])
            ]
            out[role_id][qid] = QuestionCriteria(
                question_id=qid,
                competency=qblock.get("competency", ""),
                criteria=crits,
            )
    return out
