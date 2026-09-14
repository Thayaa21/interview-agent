# Setup Guide (Outbound) — Owner: Baradwaj

This is the skeleton checklist for wiring the demo to live services. Nothing here
is implemented yet; it lists what Baradwaj needs to set up so Rishi's code has
working accounts, keys, and a trunk to dial through. Steps needing account /
console access are marked ⚠️.

## 1. ⚠️ Accounts & keys
- LiveKit Cloud project → `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.
- Deepgram → `DEEPGRAM_API_KEY`.
- Anthropic → `ANTHROPIC_API_KEY`.
- Cartesia → `CARTESIA_API_KEY`.
- Copy `.env.example` → `.env` and fill everything in.

## 2. ⚠️ Twilio (outbound)
- Buy a voice-capable number → `TWILIO_PHONE_NUMBER` / `OUTBOUND_CALLER_ID`.
- Create an Elastic SIP Trunk with a **Termination** SIP URI.
- Note the termination URI + credentials for the LiveKit outbound trunk.

## 3. LiveKit outbound trunk
- Fill in `scripts/outbound_trunk.json` (address, numbers, auth).
- Create it: `lk sip outbound create scripts/outbound_trunk.json`.
- Put the returned trunk id (`ST_...`) in `.env` as `SIP_OUTBOUND_TRUNK_ID`.

## 4. ⚠️ `lk` CLI
- Install the LiveKit CLI and authenticate to the project.

## 5. Agent dispatch
- The agent registers under `AGENT_NAME` (default `soliant-interviewer`).
- The dispatcher dispatches that agent per call; keep names consistent.

## 6. Run the demo (once code is implemented by Rishi)
- Start the worker:   `python -m src.agent dev`
- Validate the sheet: `python -m src.dispatcher --dry-run`
- Place calls:        `python -m src.dispatcher`

## Where things live
| Concern | Owner | Location |
| --- | --- | --- |
| Accounts, keys, Twilio trunk, `.env` | Baradwaj | ⚠️ consoles + `.env` |
| LiveKit outbound trunk + dispatch | Baradwaj | `lk` CLI + `scripts/` |
| Agent / dispatcher / interview code | Rishi | `src/` |
| Role questions | Rishi + team | `roles/` |
| Candidate sheet | Baradwaj | `candidates.csv` |
