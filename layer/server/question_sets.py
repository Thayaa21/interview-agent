"""Question sets per role for the demo (shared by mock driver + live sessions).

Order = role-specific questions first, then shared behavioral. These mirror the
content in ../../roles/*.yaml but are kept here as plain dicts so the layer/
demo has no dependency on Rishi's src/ loaders.
"""

from __future__ import annotations

from typing import Dict, List

_TITLES = {
    "oncology_rn": "Registered Nurse - Oncology",
    "staff_pharmacist": "Staff Pharmacist",
}

QUESTION_SETS: Dict[str, List[dict]] = {
    "oncology_rn": [
        {"id": "rn_1", "text": "Tell me about your nursing background and your experience in oncology or infusion settings."},
        {"id": "rn_2", "text": "Walk me through how you safely prepare for and administer chemotherapy."},
        {"id": "rn_3", "text": "How do you recognize and respond to an adverse reaction during an infusion?"},
        {"id": "beh_1", "text": "Tell me about a time you had to handle a high-pressure situation at work. What did you do?"},
        {"id": "beh_2", "text": "Describe a time you disagreed with a colleague or supervisor. How did you resolve it?"},
        {"id": "beh_3", "text": "Why are you interested in this role, and what are you looking for in your next position?"},
    ],
    "staff_pharmacist": [
        {"id": "rx_1", "text": "Can you walk me through your pharmacy background and your current licensure status?"},
        {"id": "rx_2", "text": "How do you verify a prescription and check for potential drug interactions before dispensing?"},
        {"id": "rx_3", "text": "Tell me about a time you caught a medication error. What did you do?"},
        {"id": "beh_1", "text": "Tell me about a time you had to handle a high-pressure situation at work. What did you do?"},
        {"id": "beh_2", "text": "Describe a time you disagreed with a colleague or supervisor. How did you resolve it?"},
        {"id": "beh_3", "text": "Why are you interested in this role, and what are you looking for in your next position?"},
    ],
}


def role_display_name(role_id: str) -> str:
    return _TITLES.get(role_id, role_id)
