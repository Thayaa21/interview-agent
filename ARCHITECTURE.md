# Architecture — Outbound Interview Agent (Skeleton)

How the outbound interview flow and components fit together. This describes the
intended design; the code is a skeleton to be filled in (see `TASKS.md`).

Demo scope: 2 roles — `staff_pharmacist`, `oncology_rn`.

## 1. Flow overview

```
candidates.csv (name, role, phone)
        │
        ▼
   Dispatcher (src/dispatcher.py)
     for each candidate:
        1) dispatch named agent into a new room  (with candidate metadata)
        2) create outbound SIP participant → dials the candidate's phone
        │
        ▼
   Twilio SIP trunk ──(PSTN)──▶ candidate's phone rings
        │
        ▼
   LiveKit Room (one per call)
     ├── SIP participant (candidate audio)
     └── Agent worker (src/agent.py)
              │
              ▼
   ┌──────────── AgentSession pipeline ────────────┐
   │ candidate audio → Deepgram STT → InterviewController │
   │                                       │        │
   │                          Claude (follow-up decision) │
   │ next line → Cartesia TTS → candidate                 │
   │ VAD + turn detector gate end-of-turn                 │
   │ TranscriptLogger records every turn                  │
   └───────────────────────────────────────────────┘
```

Key idea: the **dispatcher** initiates calls (outbound); the **agent** runs the
interview once the candidate answers. The `InterviewController` owns flow in
code; Claude only advises on follow-ups.

## 2. Outbound call lifecycle
1. Dispatcher reads the candidate sheet and validates it against known roles.
2. For each candidate: dispatch the named agent into a fresh room, passing
   candidate context (name, role, phone) as metadata.
3. Dispatcher creates a SIP participant on the outbound trunk that dials the
   candidate into that room.
4. Candidate answers → agent greets by name and asks question 1.
5. After each answer: filter → reasoner → code enforces follow-up cap + ordering.
6. After the last question: closing message, then hang up; transcript flushed.

## 3. Components (all in `src/`)
- **config.py** — env-based `Settings` + fail-fast validation (runtime vs.
  dispatch profiles).
- **candidates.py** — load + validate the CSV sheet into `Candidate` rows.
- **questionbank.py** — load a `Role` = role-specific questions + shared
  behavioral questions from `roles/`.
- **interview.py** — `InterviewController` state machine (greeting → questions +
  capped follow-ups → closing).
- **reasoner.py** — `ClaudeReasoner` bounded "follow up or advance" decision;
  fails safe to advance.
- **filters.py** — single input-filter seam (stub: allow all).
- **transcript.py** — sqlite / jsonl turn logger keyed by room name.
- **dispatcher.py** — outbound: dispatch agent + create SIP participant per
  candidate.
- **agent.py** — LiveKit worker entrypoint; wires the realtime pipeline and
  drives the controller.

## 4. Question bank model
- `roles/behavioral.yaml` — shared behavioral questions (every candidate).
- `roles/<role_id>.yaml` — role metadata + role-specific questions.
- A role's interview list = role-specific questions **+** shared behavioral.

## 5. Design intent
- **Code-driven loop, bounded LLM** — deterministic flow, guaranteed max-2
  follow-ups; Claude only picks/wordsmiths follow-ups.
- **Per-call isolation** — one room + one controller + one transcript per call;
  room name is the transcript key.
- **Single filter seam** — future screening drops in without rewiring.
- **Two ownership tracks** — code (Rishi) vs. accounts/trunk/sheet (Baradwaj).
