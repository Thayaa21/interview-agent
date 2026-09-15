"""Compliance + intelligence layer for the interview agent.

This package sits ON TOP of the src/ interview skeleton (which is owned by
Rishi and left untouched). It adds:

  * compliance/  — rulebook + guardrails engine (keep the agent in scope)
  * analysis/    — turn assembly + JD-criteria behavioral interpretation
  * server/      — FastAPI backend (REST + WebSocket) and the mock-call driver
  * frontend/    — React live dashboard

Everything here runs today against mock transcripts, with clean seams to hook
into the live LiveKit pipeline later.
"""
