"""Candidate sheet loading.  [SKELETON]

Owner: Rishi (code), with the sheet itself maintained by Baradwaj.

The candidate sheet is a CSV with columns: name, role, phone.
Each row becomes one outbound call.
  * name  — used in the greeting.
  * role  — must match a role id in the question bank (roles/<role>.yaml).
  * phone — E.164 (e.g. +14155550123).

TODO(Rishi): implement load_candidates() — read the CSV, validate columns and
             each row (name/role present, role in valid_roles, phone is E.164),
             and return a list of Candidate. Raise CandidateSheetError on any
             problem so a bad sheet fails before any call is placed.
"""

from __future__ import annotations

from dataclasses import dataclass


class CandidateSheetError(RuntimeError):
    """Raised when the candidate sheet is missing or malformed."""


@dataclass(frozen=True)
class Candidate:
    name: str
    role: str
    phone: str


def load_candidates(path: str | None = None, valid_roles: set[str] | None = None) -> list[Candidate]:
    """Load + validate the candidate sheet. TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement load_candidates")
