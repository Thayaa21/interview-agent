"""Role-based question bank loading.  [SKELETON]

Owner: Rishi (loader code); question content in roles/ maintained jointly.

Layout (roles/ directory):
  * behavioral.yaml  — shared behavioral questions asked to every candidate.
  * <role_id>.yaml   — one file per role: role metadata + role-specific questions.

For a role, the interview question list = role-specific questions + shared
behavioral questions.

TODO(Rishi): implement the loaders below — parse + validate YAML, merge role
             questions with the shared behavioral set, and return Role objects.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml

VALID_CATEGORIES = {"background", "technical", "behavioral"}
_DEFAULT_ROLES_DIR = "roles"
_BEHAVIORAL_FILE = "behavioral.yaml"


class QuestionBankError(RuntimeError):
    """Raised when the question bank is missing or malformed."""


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    text: str
    probe_hint: str | None = None


@dataclass(frozen=True)
class Role:
    id: str
    title: str
    description: str
    requirements: list[str] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)


def _parse_question(raw: dict, source: str) -> Question:
    try:
        qid = raw["id"]
        category = raw["category"]
        text = raw["text"]
    except KeyError as e:
        raise QuestionBankError(f"{source}: question missing required field {e}") from e

    if category not in VALID_CATEGORIES:
        raise QuestionBankError(
            f"{source}: question {qid!r} has invalid category {category!r} "
            f"(must be one of {sorted(VALID_CATEGORIES)})"
        )
    if not text:
        raise QuestionBankError(f"{source}: question {qid!r} has empty text")

    return Question(id=qid, category=category, text=text, probe_hint=raw.get("probe_hint"))


def _load_behavioral_questions(roles_dir: str) -> list[Question]:
    path = os.path.join(roles_dir, _BEHAVIORAL_FILE)
    if not os.path.isfile(path):
        raise QuestionBankError(f"Behavioral question file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    raw_questions = data.get("behavioral")
    if not raw_questions:
        raise QuestionBankError(f"{path}: missing or empty 'behavioral' list")

    return [_parse_question(q, path) for q in raw_questions]


def available_roles(roles_dir: str | None = None) -> list[str]:
    """List role ids in roles/ (excluding behavioral.yaml)."""
    directory = roles_dir or _DEFAULT_ROLES_DIR
    if not os.path.isdir(directory):
        raise QuestionBankError(f"Roles directory not found: {directory}")

    role_ids = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".yaml") or name == _BEHAVIORAL_FILE:
            continue
        role_ids.append(os.path.splitext(name)[0])
    return role_ids


def load_role(role_id: str, roles_dir: str | None = None) -> Role:
    """Load one role + shared behavioral questions merged in."""
    directory = roles_dir or _DEFAULT_ROLES_DIR
    path = os.path.join(directory, f"{role_id}.yaml")
    if not os.path.isfile(path):
        raise QuestionBankError(f"Role file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    role_block = data.get("role")
    if not role_block:
        raise QuestionBankError(f"{path}: missing 'role' block")

    try:
        rid = role_block["id"]
        title = role_block["title"]
        description = role_block["description"]
    except KeyError as e:
        raise QuestionBankError(f"{path}: role block missing required field {e}") from e

    if rid != role_id:
        raise QuestionBankError(
            f"{path}: role id {rid!r} does not match filename-derived id {role_id!r}"
        )

    requirements = role_block.get("requirements", []) or []
    raw_questions = data.get("questions", []) or []
    questions = [_parse_question(q, path) for q in raw_questions]
    questions += _load_behavioral_questions(directory)

    return Role(
        id=rid,
        title=title,
        description=description,
        requirements=list(requirements),
        questions=questions,
    )


def load_all_roles(roles_dir: str | None = None) -> dict[str, Role]:
    """Load every available role, keyed by id."""
    directory = roles_dir or _DEFAULT_ROLES_DIR
    return {rid: load_role(rid, directory) for rid in available_roles(directory)}
