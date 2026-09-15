# Architecture — Voice Interview Agent (Skeleton)

How the interview flow and components fit together. `src/` is a skeleton to be
filled in; the compliance/analysis/dashboard `layer/` is implemented.

Demo scope: 2 roles — `staff_pharmacist`, `oncology_rn`.
Call direction: **INBOUND first (free)**; outbound is a funded-later phase.

## 1. Flow overview (inbound, free)

```
   candidate dials the Twilio TRIAL number
        │
        ▼
   Twilio Programmable Voice
     → hits our Voice webhook (src/inbound_webhook.py)
     → returns TwiML <Connect><Stream>  (Media Streams over WebSocket)
        │  (no SIP trunk — this is the free path)
        ▼
   LiveKit Twilio Connector  → drops the caller into a LiveKit Room
        │
        ▼
   LiveKit Room
     ├── caller audio (from the media stream)
     └── Agent worker (src/agent.py)
              │
              ▼
   ┌──────────── AgentSession pipeline ────────────┐
   │ caller audio → Deepgram STT → InterviewController    │
   │                                       │              │
   │                          GPT-4o (follow-up decision) │
   │ next line → Cartesia TTS → caller                    │
   │ VAD + turn detector gate end-of-turn                 │
   │ TranscriptLogger records every turn                  │
   └───────────────────────────────────────────────┘
                    │
                    ▼  (events)
   layer/ : guardrails + answer→JD-criteria analysis + live dashboard
```

Key idea: for the free demo the **candidate initiates** the call; Twilio's
webhook + Media Streams bridge it into LiveKit via the Twilio Connector (no SIP
trunk). The `InterviewController` owns flow in code; GPT-4o only advises on
follow-ups.

## 2. Inbound call lifecycle (free path)
1. Candidate dials the Twilio trial number.
2. Twilio calls our Voice webhook; it returns TwiML `<Connect><Stream>`.
3. Media Streams sends the call audio (WebSocket) to the LiveKit Twilio
   Connector, which places the caller in a LiveKit room.
4. The agent (already in the room) greets and asks question 1.
5. After each answer: filter → reasoner → code enforces follow-up cap + ordering.
6. After the last question: closing message, hang up; transcript flushed.

## 2b. Outbound lifecycle (FUNDED-LATER — not in the demo)
`src/dispatcher.py` reads `candidates.csv`, dispatches the agent into a room per
candidate, and creates an outbound SIP participant (Elastic SIP Trunk) to dial
them. Requires paid trunking; deferred until funded.

## 3. Components (all in `src/`)
- **config.py** — env-based `Settings` + fail-fast validation (runtime vs.
  dispatch profiles).
- **candidates.py** — load + validate the CSV sheet into `Candidate` rows.
- **questionbank.py** — load a `Role` = role-specific questions + shared
  behavioral questions from `roles/`.
- **interview.py** — `InterviewController` state machine (greeting → questions +
  capped follow-ups → closing).
- **reasoner.py** — `OpenAIReasoner` (GPT-4o) bounded "follow up or advance"
  decision; fails safe to advance.
- **filters.py** — single input-filter seam (stub: allow all).
- **transcript.py** — sqlite / jsonl turn logger keyed by room name.
- **agent.py** — LiveKit worker entrypoint; wires the realtime pipeline and
  drives the controller.
- **inbound_webhook.py** (to add) — Twilio Voice webhook returning TwiML
  `<Connect><Stream>` to bridge the inbound call into LiveKit (free path).
- **dispatcher.py** — outbound (funded-later): dispatch agent + create SIP
  participant per candidate.

See `layer/` (implemented) for guardrails, answer→JD-criteria analysis, and the
live dashboard that consume this pipeline's events.

## 4. Question bank model
- `roles/behavioral.yaml` — shared behavioral questions (every candidate).
- `roles/<role_id>.yaml` — role metadata + role-specific questions.
- A role's interview list = role-specific questions **+** shared behavioral.

## 5. Design intent
- **Code-driven loop, bounded LLM** — deterministic flow, guaranteed max-2
  follow-ups; GPT-4o only picks/wordsmiths follow-ups.
- **Per-call isolation** — one room + one controller + one transcript per call;
  room name is the transcript key.
- **Single filter seam** — future screening drops in without rewiring.
- **Two ownership tracks** — code (Rishi) vs. accounts/keys/number (Baradhwaj).
