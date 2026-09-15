# Rishi — Technical Track

You own the **code**. Everything under `src/` and the question content under
`roles/` is yours to implement. The repo is a skeleton: every function/class has
a signature, a docstring describing what it should do, and a
`raise NotImplementedError("TODO(Rishi): ...")` placeholder. Your job is to
replace each placeholder with a working implementation.

Baradhwaj (product) handles all the accounts, API keys, the Twilio trial number,
and the interview content — see `../baradhwaj/`. You can build and unit-test
almost everything before his setup is done by using fakes.

---

## Demo scope — FREE, INBOUND first

We are doing **inbound** for the demo: the **candidate calls a Twilio trial
number** and the agent answers. This is free because it uses Twilio's **Voice
webhook + Media Streams** (`<Connect><Stream>`) bridged into LiveKit via the
**Twilio Connector** — **no Elastic SIP Trunk** (the SIP trunk is the paid
product that forces a trial upgrade, so we avoid it).

**Outbound is deferred to a "funded later" phase.** The `src/dispatcher.py`
outbound engine and `candidates.csv` stay in the repo but are NOT needed for the
demo — implement them only when we fund outbound dialing.

- **2 roles only**: `staff_pharmacist` and `oncology_rn` (files in `roles/`).
- Company context: Soliant (healthcare/education staffing).

---

## What to build, in order

Each item points to the file and the `TODO(Rishi)` inside it.

1. **`src/config.py` — `load_settings()`**
   Load `.env` (use `python-dotenv`), validate the required variables for the
   requested profile (`runtime` vs `dispatch`), and fail fast with a clear error
   naming any missing variable. Return a populated `Settings`.

2. **`src/candidates.py` — `load_candidates()`**
   Read the CSV (`name, role, phone`). Validate columns and each row: name and
   role present, role is in the allowed set, phone is valid E.164
   (`+` then digits). Raise `CandidateSheetError` on any problem so a bad sheet
   fails before any call is placed. Return a list of `Candidate`.

3. **`src/questionbank.py` — `available_roles`, `load_role`, `load_all_roles`**
   Parse `roles/<role>.yaml` (role metadata + role-specific questions) and
   `roles/behavioral.yaml` (shared questions). A role's question list =
   role-specific questions **+** shared behavioral questions. Validate ids,
   categories (`background|technical|behavioral`), and text.

4. **`src/filters.py` — `check_input()`**
   Skeleton behavior: return `FilterResult(allow=True, ...)` (pass everything
   through). This is the single seam where answer-screening could go later; keep
   the return type stable.

5. **`src/reasoner.py` — `parse_decision()` + `ClaudeReasoner.decide()`**
   `decide()` calls Claude (Anthropic Messages API) with the current question and
   answer and expects a JSON decision (`follow_up` or `advance`, plus follow-up
   wording). `parse_decision()` parses it defensively. **Fail safe:** on any API
   or parse error, return an `advance` decision so a candidate is never stuck.

6. **`src/interview.py` — `InterviewController`**
   The heart of the flow. Implement `__init__`, `first_prompt`, `handle_answer`,
   `is_finished`. `handle_answer` must: run the filter → ask the reasoner →
   enforce `max_followups` and question ordering **in code** → return an
   `AgentAction` (SPEAK the next line, or END with the closing message). The LLM
   only advises; your code guarantees the flow and the 2-follow-up cap.

7. **`src/transcript.py` — sqlite + jsonl loggers + `create_logger()`**
   Record every turn (speaker, text, timestamp) keyed by session id (the room
   name), plus call metadata (candidate, role, phone). Make it safe to call from
   LiveKit callbacks (thread-safe) and flush on `close()`.

8. **`src/agent.py` — `entrypoint()` + worker registration**
   The per-call agent. Load the role, build the `AgentSession` (Deepgram STT,
   Anthropic LLM, Cartesia TTS, Silero VAD + LiveKit turn detection), greet,
   then on each final transcript drive the `InterviewController`, speak the
   result, log turns, and hang up on END. Register the worker with `agent_name`.
   (For inbound, candidate context can be minimal — no candidate sheet needed.)

9. **Inbound webhook bridge (the free path) — NEW, replaces the trunk**
   Add a small webhook service (e.g. `src/inbound_webhook.py`, FastAPI/Flask)
   that Twilio calls when a candidate dials in. It returns **TwiML** with
   `<Connect><Stream>` pointing at the **LiveKit Twilio Connector** so the
   caller's audio is bridged into a LiveKit room where the agent is waiting.
   - Reference: LiveKit "Twilio Connector" (Media Streams) — bridges a Twilio
     call into a room **without** a SIP trunk.
   - Run it locally behind an **ngrok** tunnel; give Baradhwaj the public URL to
     paste into the number's Voice webhook.

10. **`roles/` — finalize question wording** for the two demo roles.

### Deferred (funded-later, outbound)
- **`src/dispatcher.py` — `_place_call`, `run`, `main`.** The outbound engine
  (agent dispatch + create SIP participant on an outbound trunk) and
  `candidates.csv`. Implement only when outbound is funded. Leave the stubs.

---

## Verify the LiveKit API names
`src/agent.py` (and, later, `src/dispatcher.py`) are written against LiveKit
Agents / `livekit-api` 1.x. After `pip install -r requirements.txt`, confirm the
exact class/event/method names against the installed version (the file headers
list what to check). Also check the current **Twilio Connector / Media Streams**
setup in the LiveKit telephony docs for the inbound bridge in step 9.

## How to work without waiting on Baradhwaj
- Steps 1–7 need no live accounts. Write small fakes (e.g. a fake reasoner) and
  test `InterviewController`, `questionbank`, and the transcript loggers locally.
- The compliance/analysis/dashboard layer (`../layer/`) already runs end-to-end
  against mock transcripts (`python -m layer.smoke_test`) — useful for exercising
  guardrails + criteria mapping without any phone setup.
- Live inbound (steps 8–9) needs Baradhwaj's `.env` + Twilio trial number + the
  webhook URL wired to the number.

## Done when (inbound demo)
- The agent worker + inbound webhook are running (webhook exposed via ngrok).
- Calling the Twilio trial number connects to the agent, which asks the role +
  behavioral questions with follow-ups capped at 2 and hangs up after the last.
- Every turn is written to the transcript store.

## Note on the there being two "layers"
- `src/` = the interview agent (your track).
- `../layer/` = compliance guardrails + answer→JD-criteria analysis + live
  dashboard (already implemented). When wiring live, feed real STT fragments to
  the layer's turn-assembler and route agent output through its guardrails —
  seams are documented in `../layer/README.md`.
