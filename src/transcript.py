"""Transcript logging.  [SKELETON]

Owner: Rishi.

Records every turn (speaker, text, timestamp) for one call, plus call metadata
(candidate name, role, phone). Backends: sqlite (default) and jsonl.
session_id is unique per call (the LiveKit room name).

TODO(Rishi): implement the two backends + create_logger factory. Both must be
             safe to call from LiveKit callbacks (thread-safe) and flush on
             close().
"""

from __future__ import annotations

SPEAKER_AGENT = "agent"
SPEAKER_CANDIDATE = "candidate"


class TranscriptLogger:
    """Base interface. Use create_logger() to build a configured backend."""

    def __init__(self, session_id: str, candidate: str = "", role: str = "", phone: str = ""):
        self.session_id = session_id
        self.candidate = candidate
        self.role = role
        self.phone = phone

    def log(self, speaker: str, text: str) -> None:
        raise NotImplementedError("TODO(Rishi): implement log")

    def close(self) -> None:
        raise NotImplementedError("TODO(Rishi): implement close")


def create_logger(
    session_id: str,
    backend: str = "sqlite",
    path: str | None = None,
    candidate: str = "",
    role: str = "",
    phone: str = "",
) -> TranscriptLogger:
    """Factory: build a logger for the configured backend. TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement create_logger (sqlite + jsonl)")
