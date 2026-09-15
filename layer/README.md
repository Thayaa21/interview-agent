# Compliance + Intelligence Layer

This package sits **on top of** the `src/` interview skeleton (owned by Rishi,
untouched). It adds the robustness and intelligence features plus a live local
dashboard. Everything here is **implemented and runnable today** against mock
transcripts — no API keys or telephony required — with clean seams to hook into
the live LiveKit pipeline later.

## What's in here

```
layer/
  types.py            # shared dataclasses (events, guard results, analysis)
  pipeline.py         # orchestrator: assembler -> guardrails -> interpreter -> events
  compliance/
    rulebook.yaml     # declarative rules (scope, banned topics, budgets, messages)
    rules.py          # rulebook loader
    guardrails.py     # engine: input filter + output sanctioner + budgets
  analysis/
    turn_assembler.py # stitch multi-sentence spoken answers (handles pauses)
    criteria.yaml     # behavioral criteria per role/question (mapped from JD)
    criteria.py       # criteria loader
    interpreter.py    # map an answer -> criteria (met/partial/not) + score
  server/
    store.py          # in-memory session store + async event bus (pub/sub)
    mock_driver.py    # scripted end-to-end call (incl. off-topic + injection)
    app.py            # FastAPI: REST + WebSocket
  frontend/           # React (Vite) live dashboard
  smoke_test.py       # headless end-to-end run (prints every event)
```

## Run it

### 1. Headless proof (no servers)
```bash
python -m layer.smoke_test oncology_rn
```
Runs a scripted call through the whole pipeline and prints every turn, guardrail
decision, and criteria analysis.

### 2. Backend + live dashboard
```bash
# backend
pip install -r layer/requirements.txt
uvicorn layer.server.app:app --reload --port 8000

# frontend (separate terminal)
cd layer/frontend
npm install
npm run dev            # http://localhost:5173
```
Click **Start mock call** in the UI. The transcript, per-answer JD-criteria
mapping, guardrail feed, and overall score update live over the WebSocket.

## The four features

1. **Guardrails (robustness).** Code-enforced rules — an input filter
   (off-topic → redirect, injection → block, repeat abuse → end), an output
   sanctioner (the agent may only speak sanctioned utterance kinds; anything
   else is blocked and replaced), and hard budgets (turns/time/follow-ups). This
   is what prevents the "front-desk agent starts giving pancake recipes after a
   long chat" failure — see `COMPLIANCE.md`.
2. **Rulebook.** All rules live in `compliance/rulebook.yaml` as data, so scope,
   banned topics, budgets, and canned messages can be tuned without touching
   enforcement code.
3. **Answer → JD-criteria mapping.** For each behavioral question we define the
   competencies we're screening for (`analysis/criteria.yaml`, mapped from the
   JD). The interpreter maps each answer to those criteria (met / partial /
   not_met / not_addressed) with evidence and a score. Runs **post-answer** in
   real time. Heuristic backend by default; Claude backend when a key is present
   (auto-fallback on error).
4. **Robust turn assembly.** `turn_assembler.py` stitches fragmented,
   multi-sentence answers into one, using an end-of-turn signal or a debounce
   window so a mid-answer pause isn't mistaken for "done."

## Hooking into the live pipeline (later)
`pipeline.InterviewPipeline` is transport-agnostic and does not import from
`src/`. The live agent feeds it real STT fragments (via `TurnAssembler`) and
calls `submit_answer()` per completed answer; the same events flow to the same
dashboard. The guardrail seam maps to `src/filters.py` (input) and the agent's
output path (sanction before `session.say`).
