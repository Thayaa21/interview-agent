"""Candidate sheet loading.  [SKELETON]

Owner: Rishi (code), with the sheet itself maintained by Baradhwaj.
NOTE: candidate sheet is for OUTBOUND (funded-later); not used in the free demo.

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

import csv
import os
import re
from dataclasses import dataclass

_PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")
_REQUIRED_COLUMNS = ("name", "role", "phone")


class CandidateSheetError(RuntimeError):
    """Raised when the candidate sheet is missing or malformed."""


@dataclass(frozen=True)
class Candidate:
    name: str
    role: str
    phone: str


def load_candidates(path: str | None = None, valid_roles: set[str] | None = None) -> list[Candidate]:
    """Load + validate the candidate sheet.

    Raises CandidateSheetError on any missing file, missing column, or
    invalid row so a bad sheet fails before any call is placed.
    """
    sheet_path = path or "candidates.csv"
    if not os.path.isfile(sheet_path):
        raise CandidateSheetError(f"Candidate sheet not found: {sheet_path}")

    with open(sheet_path, newline="", encoding="utf-8") as f:
        lines = [
            (i, line) for i, line in enumerate(f, start=1)
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not lines:
            raise CandidateSheetError(f"Candidate sheet is empty: {sheet_path}")

        line_numbers = [i for i, _ in lines]
        reader = csv.DictReader(line for _, line in lines)
        if reader.fieldnames is None:
            raise CandidateSheetError(f"Candidate sheet is empty: {sheet_path}")

        missing_columns = [c for c in _REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing_columns:
            raise CandidateSheetError(
                f"Candidate sheet missing required column(s): {', '.join(missing_columns)}"
            )

        candidates: list[Candidate] = []
        for row_num, row in zip(line_numbers[1:], reader):
            i = row_num
            name = (row.get("name") or "").strip()
            role = (row.get("role") or "").strip()
            phone = (row.get("phone") or "").strip()

            if not name:
                raise CandidateSheetError(f"Row {i}: missing name")
            if not role:
                raise CandidateSheetError(f"Row {i}: missing role")
            if valid_roles is not None and role not in valid_roles:
                raise CandidateSheetError(
                    f"Row {i}: unknown role {role!r} (valid roles: {', '.join(sorted(valid_roles))})"
                )
            if not _PHONE_RE.match(phone):
                raise CandidateSheetError(f"Row {i}: phone {phone!r} is not valid E.164")

            candidates.append(Candidate(name=name, role=role, phone=phone))

    if not candidates:
        raise CandidateSheetError(f"Candidate sheet has no data rows: {sheet_path}")

    return candidates
