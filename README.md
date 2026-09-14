# Soliant Outbound Interview Agent — Skeleton

A skeleton for an **outbound** voice interview agent for Soliant (healthcare &
education staffing). It reads a candidate sheet (name, role, phone), places
outbound phone calls, and asks each candidate a preset set of role-specific and
behavioral questions, logging every turn.

> This repo is a **skeleton only** — module structure, signatures, docstrings,
> and `TODO(...)` markers. No logic is implemented yet. The work split lives in
> `rishi/README.md` (technical) and `baradhwaj/README.md` (setup / product).

Demo scope: **2 roles** — `staff_pharmacist` and `oncology_rn`.

## What it will do (once implemented)
1. Load candidates from `candidates.csv`.
2. For each candidate, place an outbound call and dispatch the agent into a room.
3. Greet by name, ask the role's preset questions one at a time (role-specific +
   shared behavioral), with up to 2 code-capped follow-ups per question.
4. Hang up after the last question and log the full transcript.

## Stack
- LiveKit Agents (Python) + LiveKit SIP for outbound calls
- Twilio SIP trunk (phone number / PSTN)
- Deepgram Nova-3 (STT), Cartesia Sonic (TTS)
- Claude / Anthropic (follow-up decision)
- LiveKit VAD + turn detection

## Layout
```
src/
  config.py        # env settings (skeleton)
  candidates.py    # candidate sheet loader (skeleton)
  questionbank.py  # role-based question loader (skeleton)
  interview.py     # interview state machine (skeleton)
  reasoner.py      # Claude follow-up decision (skeleton)
  filters.py       # input filter stub (skeleton)
  transcript.py    # transcript logger (skeleton)
  dispatcher.py    # outbound call dispatcher (skeleton)
  agent.py         # LiveKit worker entrypoint (skeleton)
roles/
  behavioral.yaml            # shared behavioral questions
  staff_pharmacist.yaml      # demo role 1
  oncology_rn.yaml           # demo role 2
scripts/
  setup.md                   # setup checklist (Baradwaj)
  outbound_trunk.json        # LiveKit outbound trunk template
candidates.csv               # candidate sheet (example rows)
rishi/ baradhwaj/            # per-person task guides
ARCHITECTURE.md / GLOSSARY.md
```

## Getting started
- **Rishi (technical):** see `rishi/README.md` — implement the `TODO(Rishi)`
  items in `src/`.
- **Baradhwaj (setup / product):** see `baradhwaj/README.md` — accounts, keys,
  the SIP trunk, and the candidate sheet.

## Docs
- `ARCHITECTURE.md` — how the outbound flow and components fit together.
- `GLOSSARY.md` — plain-language definitions of the technical terms.
