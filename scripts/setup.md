# Setup Guide (Inbound, FREE) — Owner: Baradhwaj

Checklist for wiring the demo to live services on **free tiers**. We do
**inbound** only: a candidate calls a Twilio **trial** number and the agent
answers, via the **Voice webhook + Media Streams** path (no SIP trunk, no paid
upgrade). Steps needing a console login are marked ⚠️. See `../baradhwaj/README.md`
for the plain-language version.

> Outbound (us dialing candidates) needs a paid Elastic SIP Trunk — deferred to
> a funded-later phase. Ignore `outbound_trunk.json` and `candidates.csv` for now.

## 1. ⚠️ Accounts & keys (free tiers)
- LiveKit Cloud project → `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.
- Deepgram → `DEEPGRAM_API_KEY`.
- Anthropic → `ANTHROPIC_API_KEY`.
- Cartesia → `CARTESIA_API_KEY`.
- Copy `.env.example` → `.env` and fill these in. Leave `SIP_OUTBOUND_TRUNK_ID`
  and `OUTBOUND_CALLER_ID` blank (outbound-only).

## 2. ⚠️ Twilio trial number (FREE — do NOT upgrade)
- Create a free Twilio trial (includes ~75 free voice minutes + a trial number).
- Claim a voice-capable **trial number** → `.env` `TWILIO_PHONE_NUMBER`.
- Do NOT create an Elastic SIP Trunk and do NOT upgrade the account.

## 3. Inbound webhook + tunnel (Rishi runs; Baradhwaj wires the URL)
- Rishi runs the inbound webhook service (returns TwiML `<Connect><Stream>` that
  bridges the call into LiveKit via the **Twilio Connector**).
- Expose it publicly for the demo with **ngrok**: `ngrok http <webhook_port>`.
- In the Twilio number's **"A Call Comes In"** Voice webhook, paste the public
  ngrok URL (e.g. `https://xxxx.ngrok.io/incoming`) and save.

## 4. Agent worker
- The agent registers under `AGENT_NAME` (default `soliant-interviewer`) and
  waits in the LiveKit room the connector drops the caller into.

## 5. Run the demo (once Rishi's code is implemented)
- Start the agent worker:  `python -m src.agent dev`
- Start the inbound webhook + `ngrok` (Rishi).
- **Call the Twilio trial number** from any phone → the agent answers and runs
  the interview. Transcripts are logged.
- Optional: open the dashboard (`../layer/`) to watch turns, guardrails, and
  criteria mapping live.

## Where things live
| Concern | Owner | Location |
| --- | --- | --- |
| Accounts, keys, `.env` | Baradhwaj | ⚠️ consoles + `.env` |
| Twilio trial number + Voice webhook URL | Baradhwaj (with Rishi) | Twilio console |
| Inbound webhook + agent + interview code | Rishi | `src/` |
| Role questions | Rishi + team | `roles/` |
| Outbound trunk + candidate sheet | Later (funded) | `outbound_trunk.json`, `candidates.csv` |
