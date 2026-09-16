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

import json
import sqlite3
import threading
import time

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


class SqliteTranscriptLogger(TranscriptLogger):
    """Transcript logger backed by a sqlite database (default backend)."""

    def __init__(self, session_id: str, path: str, candidate: str = "", role: str = "", phone: str = ""):
        super().__init__(session_id, candidate, role, phone)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calls (
                    session_id TEXT PRIMARY KEY,
                    candidate TEXT,
                    role TEXT,
                    phone TEXT,
                    started_at REAL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    speaker TEXT,
                    text TEXT,
                    timestamp REAL
                )
                """
            )
            self._conn.execute(
                "INSERT OR IGNORE INTO calls (session_id, candidate, role, phone, started_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (self.session_id, self.candidate, self.role, self.phone, time.time()),
            )
            self._conn.commit()

    def log(self, speaker: str, text: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO turns (session_id, speaker, text, timestamp) VALUES (?, ?, ?, ?)",
                (self.session_id, speaker, text, time.time()),
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.commit()
            self._conn.close()


class JsonlTranscriptLogger(TranscriptLogger):
    """Transcript logger backed by a JSON-lines file, one line per turn."""

    def __init__(self, session_id: str, path: str, candidate: str = "", role: str = "", phone: str = ""):
        super().__init__(session_id, candidate, role, phone)
        self._lock = threading.Lock()
        self._file = open(path, "a", encoding="utf-8")
        self._write_record(
            {
                "type": "call_start",
                "session_id": self.session_id,
                "candidate": self.candidate,
                "role": self.role,
                "phone": self.phone,
                "timestamp": time.time(),
            }
        )

    def _write_record(self, record: dict) -> None:
        with self._lock:
            self._file.write(json.dumps(record) + "\n")
            self._file.flush()

    def log(self, speaker: str, text: str) -> None:
        self._write_record(
            {
                "type": "turn",
                "session_id": self.session_id,
                "speaker": speaker,
                "text": text,
                "timestamp": time.time(),
            }
        )

    def close(self) -> None:
        with self._lock:
            self._file.flush()
            self._file.close()


def create_logger(
    session_id: str,
    backend: str = "sqlite",
    path: str | None = None,
    candidate: str = "",
    role: str = "",
    phone: str = "",
) -> TranscriptLogger:
    """Factory: build a logger for the configured backend ("sqlite" | "jsonl")."""
    if backend == "sqlite":
        return SqliteTranscriptLogger(
            session_id, path or "transcripts.db", candidate=candidate, role=role, phone=phone
        )
    if backend == "jsonl":
        return JsonlTranscriptLogger(
            session_id, path or "transcripts.jsonl", candidate=candidate, role=role, phone=phone
        )
    raise ValueError(f"Unknown transcript backend: {backend!r}")
