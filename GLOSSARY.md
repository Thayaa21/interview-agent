# Glossary — Technical Terms

Plain-language definitions of the terms used in this project. Grouped by area.

## Inbound (free path — what the demo uses)
- **Inbound call** — the *candidate* dials our number and the agent answers.
  This is the free demo path (no paid trunk).
- **Twilio trial** — a free Twilio account with limited free voice minutes
  (~75) and a trial number. Enough to demo inbound. Callers hear a short "trial"
  message. No upgrade/payment required for this path.
- **Voice webhook** — a URL Twilio calls when a call comes in, asking "what do I
  do with this call?" We answer with TwiML. This is the free mechanism (the one
  Baradhwaj used before) and needs **no SIP trunk**.
- **TwiML** — Twilio's XML instruction format returned by the webhook (e.g.
  `<Say>`, `<Connect><Stream>`).
- **Media Streams** — Twilio feature that streams a call's raw audio over a
  **WebSocket** to a server you choose. Triggered by TwiML `<Connect><Stream>`.
  This is how we get call audio into our app without a SIP trunk.
- **Twilio Connector (LiveKit)** — LiveKit's built-in bridge that accepts a
  Twilio Media Stream and drops the caller into a LiveKit room — no SIP trunk.
- **ngrok** — a tool that gives your local server a temporary public URL, so
  Twilio can reach the webhook running on your laptop during the demo. Free.

## Telephony & SIP (outbound — funded-later)
- **PSTN** — the traditional phone network a normal call travels over.
- **DID** — a dialable phone number (E.164, e.g. +14155550123).
- **E.164** — international phone-number format: `+`, country code, number, no
  spaces/dashes. The candidate sheet's phone column must use it.
- **SIP** — the signaling protocol that sets up/manages/ends calls over IP. It's
  the "call control" layer; it doesn't carry the audio itself.
- **RTP** — the protocol that actually carries the call audio (SRTP = encrypted).
- **SIP trunk** — a logical connection over SIP between two phone systems. This
  is Twilio's **paid** "Elastic SIP Trunk" product — the one that forces a trial
  upgrade, which is why the demo avoids it and uses the Voice webhook instead.
- **Outbound trunk** — a trunk used to place calls *out* (us calling the
  candidate). Funded-later phase.
- **Termination URI** — the Twilio SIP address outbound calls are sent to when
  leaving LiveKit toward the PSTN.
- **Caller ID** — the number shown to the person you call (`OUTBOUND_CALLER_ID`).

## LiveKit
- **LiveKit** — a real-time audio/video platform (built on WebRTC). We use
  LiveKit Cloud (hosted).
- **Room** — a session where participants exchange audio. One room per call.
- **Participant** — anyone in a room: the **SIP participant** (candidate) and the
  **agent**.
- **SIP participant** — the LiveKit participant representing the phone caller.
  For outbound, we create it to dial the candidate.
- **Agent worker** — the long-lived process (`src/agent.py`) that LiveKit
  dispatches into a room to run the interview.
- **Agent dispatch** — LiveKit launching your named agent into a room. The
  worker's `agent_name` must match the dispatch request.
- **Job metadata** — data attached to a dispatch (here: candidate name, role,
  phone) that the agent reads to know who/what to interview.
- **AgentSession** — the LiveKit Agents object that runs the realtime pipeline
  (STT + LLM + TTS + turn detection).
- **livekit-api** — the server SDK used by the dispatcher to create rooms,
  dispatch agents, and create SIP participants.
- **`lk` CLI** — LiveKit's command-line tool, used to create the outbound trunk.

## AI voice pipeline
- **STT (Speech-to-Text)** — turns the candidate's speech into text. Deepgram
  Nova-3, streaming.
- **TTS (Text-to-Speech)** — turns the agent's text into speech. Cartesia Sonic,
  streaming.
- **LLM** — the reasoning model. Claude (Anthropic); used for the follow-up
  decision.
- **VAD (Voice Activity Detection)** — detects whether someone is speaking.
  Silero VAD.
- **Turn detection / end-of-turn** — deciding when the candidate has *finished*
  speaking so the agent can respond without interrupting.
- **Streaming** — processing audio/text continuously as it arrives (keeps the
  conversation responsive).

## Project-specific
- **Dispatcher** — reads the candidate sheet and places outbound calls
  (`src/dispatcher.py`).
- **Candidate sheet** — `candidates.csv` (name, role, phone); one row = one call.
- **Role** — a job (e.g. `staff_pharmacist`, `oncology_rn`) with its own
  questions, defined in `roles/<role>.yaml`.
- **Question bank** — role-specific questions + shared behavioral questions.
- **Behavioral questions** — questions asked to every candidate regardless of
  role (`roles/behavioral.yaml`).
- **Interview state machine (`InterviewController`)** — the code that owns
  progression: greet → ask preset questions → capped follow-ups → close.
- **Reasoner** — the wrapper around the Claude call that returns a follow-up
  `Decision`; only advises. Fails safe to "advance".
- **Follow-up cap (`MAX_FOLLOWUPS`)** — hard limit (2) on follow-ups per
  question, enforced in code.
- **Input filter** — a single checkpoint that screens an answer before reasoning
  (skeleton: allow everything).
- **Transcript logger** — records every turn (speaker, text, timestamp) to
  SQLite or JSONL, keyed by room name.
- **Fail fast** — detect a missing key/config at startup and stop with a clear
  error, rather than failing mid-call.
- **`.env`** — local, git-ignored file holding secrets/config; documented by
  `.env.example`.
- **Skeleton** — structure and stubs only (signatures + `TODO` markers), no
  implemented logic yet.
- **`TODO(Rishi)` / `TODO(Baradhwaj)`** — markers assigning each unimplemented
  piece to a work track (code vs. setup).
