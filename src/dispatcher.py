"""Outbound call dispatcher.  [SKELETON]

Owner: Rishi (code) + Baradwaj (SIP trunk / caller id it depends on).

Reads the candidate sheet and, for each candidate, places an outbound call by:
  1. dispatching the named agent into a fresh per-call room, then
  2. creating a SIP participant on the LiveKit outbound trunk that dials the
     candidate's number into that room.
Candidate context (name, role, phone) is passed as room/participant metadata so
the agent knows who it's calling and which role's questions to ask.

Intended usage once implemented:
    python -m src.dispatcher              # call everyone in the sheet
    python -m src.dispatcher --dry-run    # validate sheet + config, place no calls
    python -m src.dispatcher --only +1555...   # call one number

TODO(Rishi):  implement _place_call() using livekit-api (agent_dispatch +
              create_sip_participant) and the run()/main() CLI.
TODO(Baradwaj): provide SIP_OUTBOUND_TRUNK_ID + OUTBOUND_CALLER_ID via setup so
                _place_call has a working trunk to dial through.
"""

from __future__ import annotations

from .candidates import Candidate


def _room_name(candidate: Candidate) -> str:
    """Per-call room name. TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement _room_name")


async def _place_call(settings, candidate: Candidate) -> None:
    """Dispatch the agent + dial one candidate via LiveKit SIP. TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement _place_call")


async def run(only: str | None = None, dry_run: bool = False) -> None:
    """Load sheet + roles, then place calls (or dry-run). TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement run")


def main() -> None:
    """Parse --only/--dry-run and invoke run(). TODO(Rishi)."""
    raise NotImplementedError("TODO(Rishi): implement main")


if __name__ == "__main__":
    main()
