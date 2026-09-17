# Pipeline & Architecture

How the Soliant voice interview agent is built, end to end, and **why** each
piece was chosen. This is the "how it works and why" document.

---

## 1. What it does

A candidate joins from a browser (or, later, a phone) and has a natural spoken
interview with an AI agent. The agent greets them by name, asks a role-specific
set of questions (Oncology RN / Staff Pharmacist for the demo), reacts and asks
brief follow-ups, and closes the call. Meanwhile a live dashboard shows the
transcript, a guardrail feed (off-topic / injection detection), and a per-answer
scoring of the candidate against the job's criteria.

Two things run at once:
- **The conversation** — real-time voice, low latency, natural turn-taking.
- **The intelligence layer** — guardrails + criteria scoring, streamed live.

---

## 2. The end-to-end pipeline

```
   Browser (mic + speaker, LiveKit JS client)
        │  WebRTC audio
        ▼
   LiveKit Cloud room  ◀── token minted by src/token_server.py
        │
        ▼
   Agent worker (src/agent.py, auto-dispatched into the room)
        │
   ┌──────────────── real-time voice pipeline ────────────────┐
   │  candidate audio                                          │
   │     → Deepgram STT (speech → text)                        │
   │     → GPT-4o (drives the conversation)                    │
   │     → Cartesia TTS (text → warm voice)                    │
   │  Silero VAD + LiveKit turn detector gate end-of-turn      │
   └───────────────────────────────────────────────────────────┘
        │                                   │
        │ (each candidate turn)             │ (data messages, topic "interview")
        ▼                                   ▼
   Compliance + analysis layer          Dashboard (React)
     • hybrid guardrail classifier        • live transcript
     • JD-criteria scoring                • guardrail feed
                                          • answer → criteria + score
```

**Request flow for one call:**
1. The browser asks `token_server` for a LiveKit join token; the chosen role is
   encoded in the room name (`interview-<role>-<rand>`).
2. The browser joins the LiveKit room and publishes its mic.
3. The agent worker is **auto-dispatched** into that room, reads the role, loads
   the question bank + criteria + rulebook, and greets the candidate.
4. Each turn: Deepgram transcribes → GPT-4o responds → Cartesia speaks.
5. On each candidate answer, the layer runs the **guardrail classifier** and the
   **criteria interpreter**, and publishes events to the room.
6. The browser renders those events on the dashboard in real time.

---

## 3. The components (and where they live)

| Component | File | Role |
| --- | --- | --- |
| Agent worker | `src/agent.py` | Joins the room, runs the voice pipeline, publishes dashboard events |
| Token server | `src/token_server.py` | Mints LiveKit join tokens; role encoded in room name |
| Config | `src/config.py` | Env-based settings, fail-fast validation |
| Question bank | `roles/*.yaml`, `src/questionbank.py` | Role-specific + shared behavioral questions |
| Rulebook | `layer/compliance/rulebook.yaml`, `rules.py` | Single source of truth for scope/policy |
| Guardrail engine | `layer/compliance/guardrails.py` | Hybrid enforcement structure |
| Persona classifier | `layer/compliance/classifier.py` | GPT-4o intent judge (allow/off_topic/injection) |
| Criteria + interpreter | `layer/analysis/` | Maps answers to JD competencies + scores |
| Backend API | `layer/server/app.py` | REST + WebSocket for the dashboard |
| Dashboard | `layer/frontend/` | React live UI |

---

## 4. Why these choices

### Why LiveKit Agents (not a raw STT→LLM→TTS loop)
Real-time voice is hard: barge-in, turn detection, audio sync, and telephony all
have sharp edges. LiveKit gives us a production-grade `AgentSession` that wires
STT/LLM/TTS with built-in **VAD + semantic turn detection**, and the *same* code
works for a browser client today and a real phone call (SIP) later. We didn't
want to hand-build turn-taking or WebRTC plumbing.

### Why a browser client for the demo (not the phone)
The phone path (Twilio) needs a paid SIP trunk / account upgrade. LiveKit lets a
**browser join the same room** for free — identical pipeline, identical agent,
no telephony cost. Twilio becomes a drop-in later without changing the agent.

### Why Deepgram / GPT-4o / Cartesia specifically
- **Deepgram Nova** — fast, accurate streaming STT tuned for conversational audio.
- **GPT-4o** — strong, low-latency reasoning; drives natural conversation and
  also powers the guardrail classifier and answer interpreter (one provider,
  one key to manage).
- **Cartesia Sonic** — natural, low-latency streaming TTS with selectable voices,
  which matters a lot for "does it sound human."
Each sits behind a plugin interface, so any one is swappable without touching the
interview logic.

### Why GPT-4o *drives* the conversation (Option 2)
We started with a strict code-driven state machine (the LLM only "advised"). It
was reliable but felt robotic and interrogative. Users wanted warmth and natural
reactions, so we let **GPT-4o own the conversation** with a strong instruction
set (persona + question list + scope policy) and a deterministic `end_interview`
tool. Tradeoff, chosen deliberately: more natural, slightly less rigid control —
with the guardrail layer as the safety observer.

### Why a rulebook as the single source of truth
Scope ("what the agent may/may not do") is defined ONCE in
`layer/compliance/rulebook.yaml`. Both the **agent's instructions** and the
**guardrail classifier** read from it. Change the policy in one place and both
stay consistent — no drift between "what the agent thinks it can do" and "what we
flag." Rules are data, editable by non-engineers.

### Why the dashboard consumes LiveKit data messages
The agent publishes structured events (`turn`, `guardrail`, `analysis`,
`session_*`) as room data messages. The browser already has a LiveKit connection
for audio, so it gets the events over the same channel — no extra socket, and the
dashboard updates live as the conversation happens.

### Why two layers (src/ vs layer/)
`src/` is the interview agent. `layer/` is the compliance + intelligence add-on
(guardrails, scoring, dashboard). Keeping them separate means the guardrail and
analysis work can evolve independently of the core interview flow, and the layer
is reusable.

---

## 5. Turn-taking (the part that's easy to get wrong)

Natural conversation depends on knowing when the candidate is *actually done*.
We use Silero **VAD** (is someone speaking?) plus LiveKit's **turn detector**
(semantic end-of-turn), tuned so mid-answer pauses don't cut people off
(`min_endpointing_delay`, `min_interruption_duration`). This is why the agent
waits for a full answer instead of interrupting on a breath.

---

## 6. Data & config

- **Secrets** live in `.env` (git-ignored): LiveKit, Deepgram, OpenAI, Cartesia.
  `config.py` validates them and fails fast with a clear message.
- **Transcripts** are logged (SQLite/JSONL) per call, keyed by room name.
- **No secrets in the repo**; each operator uses their own keys.

---

## 7. Extensibility

- **Add a role**: drop a `roles/<role>.yaml` + criteria; no code change.
- **Change scope**: edit `rulebook.yaml`.
- **Swap a provider**: change one plugin line.
- **Go to phone**: add the Twilio SIP path; the agent is unchanged.
- **Enforce guardrails harder**: wire the guardrail verdict to control the
  agent's spoken line (currently the layer observes + flags; enforcement is a
  documented next step).
