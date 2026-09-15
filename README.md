# Soliant Voice Interview Agent — Skeleton

A skeleton for a voice interview agent for Soliant (healthcare & education
staffing). It runs a phone interview: greets the candidate, asks preset
role-specific and behavioral questions one at a time, asks code-capped
follow-ups, and logs every turn.

> This repo is a **skeleton** — `src/` modules have signatures, docstrings, and
> `TODO(...)` markers (no logic yet). The compliance + analysis + dashboard
> **`layer/` is fully implemented** and runnable against mock transcripts. The
> work split lives in `rishi/README.md` (technical) and `baradhwaj/README.md`
> (setup / product).

## Call direction — INBOUND first (free), outbound later (funded)

- **Now (free, inbound):** the **candidate calls a Twilio trial number** and the
  agent answers, via Twilio **Voice webhook + Media Streams** bridged into
  LiveKit with the **Twilio Connector** — **no SIP trunk**, so no paid upgrade.
- **Later (funded, outbound):** us dialing candidates from `candidates.csv` via
  `src/dispatcher.py` + an Elastic SIP Trunk. Deferred until outbound is funded.

Demo scope: **2 roles** — `staff_pharmacist` and `oncology_rn`.

## What it does (inbound demo, once implemented)
1. A candidate calls the Twilio trial number.
2. Twilio's Voice webhook streams the call into a LiveKit room (Media Streams →
   Twilio Connector).
3. The agent greets them and asks the role's preset questions one at a time
   (role-specific + shared behavioral), with up to 2 code-capped follow-ups.
4. Hangs up after the last question and logs the full transcript.

## Stack
- LiveKit Agents (Python)
- Twilio trial number + Voice webhook / Media Streams (inbound; free)
- Deepgram Nova-3 (STT), Cartesia Sonic (TTS)
- OpenAI GPT-4o (follow-up decision + answer interpretation)
- LiveKit VAD + turn detection

## Layout
```
src/                  # interview agent (skeleton — Rishi's track)
  config.py  questionbank.py  interview.py  reasoner.py
  filters.py  transcript.py  agent.py
  candidates.py  dispatcher.py    # outbound — funded-later
roles/                # question banks (2 demo roles + shared behavioral)
layer/                # compliance + analysis + live dashboard (IMPLEMENTED)
  compliance/  analysis/  server/  frontend/   (see layer/README.md)
scripts/setup.md      # inbound setup checklist
rishi/ baradhwaj/     # per-person task guides
ARCHITECTURE.md  GLOSSARY.md  COMPLIANCE.md
candidates.csv  scripts/outbound_trunk.json   # outbound — funded-later
```

## Getting started
- **Rishi (technical):** see `rishi/README.md` — implement the `TODO(Rishi)`
  items in `src/` and the inbound webhook bridge.
- **Baradhwaj (setup / product):** see `baradhwaj/README.md` — free accounts,
  keys, the Twilio trial number + Voice webhook.

## Docs
- `ARCHITECTURE.md` — how the flow and components fit together.
- `COMPLIANCE.md` — how guardrails keep the agent in scope.
- `GLOSSARY.md` — plain-language definitions of the technical terms.
- `layer/README.md` — the implemented compliance/analysis/dashboard layer.
