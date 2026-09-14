# Glossary — Technical Terms

Plain-language definitions of the terms used in this project. Grouped by area.

## Telephony & SIP
- **PSTN** — the traditional phone network a normal call travels over.
- **DID** — a dialable phone number (E.164, e.g. +14155550123). Here it's the
  Twilio number used as the outbound caller ID.
- **E.164** — international phone-number format: `+`, country code, number, no
  spaces/dashes. The candidate sheet's phone column must use it.
- **SIP** — the signaling protocol that sets up/manages/ends calls over IP. It's
  the "call control" layer; it doesn't carry the audio itself.
- **RTP** — the protocol that actually carries the call audio (SRTP = encrypted).
- **SIP trunk** — a logical connection over SIP between two phone systems. Here
  it links Twilio (the phone number) to LiveKit (the agent).
- **Outbound trunk** — a trunk used to place calls *out* (us calling the
  candidate). This project is outbound.
- **Termination URI** — the Twilio SIP address that outbound calls are sent to
  when leaving LiveKit toward the PSTN.
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
- **`TODO(Rishi)` / `TODO(Baradwaj)`** — markers assigning each unimplemented
  piece to a work track (code vs. setup).
