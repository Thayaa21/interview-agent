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

from dataclasses import dataclass, field

VALID_CATEGORIES = {"background", "technical", "behavioral"}


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


def available_roles(roles_dir: str | None = None) -> list[str]:
    """List role ids in roles/ (excluding behavioral.yaml). TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement available_roles")


def load_role(role_id: str, roles_dir: str | None = None) -> Role:
    """Load one role + shared behavioral questions merged in. TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement load_role")


def load_all_roles(roles_dir: str | None = None) -> dict[str, Role]:
    """Load every available role, keyed by id. TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement load_all_roles")
