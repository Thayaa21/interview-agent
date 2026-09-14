# Rishi — Technical Track

You own the **code**. Everything under `src/` and the question content under
`roles/` is yours to implement. The repo is a skeleton: every function/class has
a signature, a docstring describing what it should do, and a
`raise NotImplementedError("TODO(Rishi): ...")` placeholder. Your job is to
replace each placeholder with a working implementation.

Baradhwaj (product) handles all the accounts, API keys, phone/SIP trunk setup,
and the candidate sheet — see `../baradhwaj/`. You can build and unit-test almost
everything before his setup is done by using fakes and dry runs.

---

## Demo scope
- **Outbound** calling only (we call the candidate, not the other way around).
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

8. **`src/dispatcher.py` — `_place_call`, `run`, `main`**
   The outbound engine. For each candidate: dispatch the named agent into a new
   room (carrying candidate context as metadata), then create a SIP participant
   on the outbound trunk to dial the candidate. Support `--dry-run` (validate
   sheet + config, place no calls) and `--only <phone>`.

9. **`src/agent.py` — `entrypoint()` + worker registration**
   The per-call agent. Read candidate context from job metadata, load the role,
   build the `AgentSession` (Deepgram STT, Anthropic LLM, Cartesia TTS, Silero
   VAD + LiveKit turn detection), greet, then on each final transcript drive the
   `InterviewController`, speak the result, log turns, and hang up on END.
   Register the worker with `agent_name` matching the dispatch config.

10. **`roles/` — finalize question wording** for the two demo roles.

---

## Verify the LiveKit API names
`src/agent.py` and `src/dispatcher.py` are written against LiveKit Agents /
`livekit-api` 1.x. After `pip install -r requirements.txt`, confirm the exact
class/event/method names against the installed version (the file headers list
what to check) and adjust if the SDK changed.

## How to work without waiting on Baradhwaj
- Steps 1–7 need no live accounts. Write small fakes (e.g. a fake reasoner) and
  test `InterviewController`, `load_candidates`, `questionbank`, and the
  transcript loggers locally.
- Use `python -m src.dispatcher --dry-run` to validate the sheet + roles once
  `config`, `candidates`, and `questionbank` are done.
- Live calls (steps 8–9 end to end) need Baradhwaj's `.env` + SIP trunk.

## Done when
- `python -m src.dispatcher --dry-run` validates cleanly.
- Worker + dispatcher together place a real call, ask role + behavioral
  questions with follow-ups capped at 2, and hang up after the last question.
- Every turn is written to the transcript store.
