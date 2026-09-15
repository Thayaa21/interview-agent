# Baradhwaj — Setup & Product Track

You're coming at this from **product**, not deep engineering — so this guide
explains not just *what* to do but *what each piece is* and *why it matters*.
You don't write the app code (that's Rishi, in `../rishi/`). You set up the
"outside world" the app depends on: the accounts, the secret keys, the phone
number, and the questions/candidate content.

Think of it like this: Rishi builds the interviewer's brain and mouth. You give
it a phone number to receive calls on, permission to use the AI services, and
the interview content.

---

## IMPORTANT: we are doing FREE, INBOUND-only for now

We are **not** doing outbound calling yet (us dialing candidates). Outbound
requires Twilio's **Elastic SIP Trunk**, which is a paid/"advanced" product that
forces a trial upgrade with a minimum top-up (~$20). We're skipping that.

Instead, the demo is **inbound**: the **candidate calls a Twilio trial number**,
and the AI agent answers. This works on Twilio's **free trial** because it uses
the **Voice webhook + Media Streams** path (not a SIP trunk). Twilio's trial
gives free voice minutes (~75 min) — plenty for a demo.

> Outbound calling and the candidate sheet (`candidates.csv`) become a
> **"funded later"** phase. For now, ignore them.

---

## The big picture (how a free inbound call works)

1. A candidate dials our **Twilio trial phone number**.
2. Twilio calls our **Voice webhook** (a small URL we control) and asks "what
   should I do with this call?"
3. Our webhook answers with **TwiML** (Twilio's instruction format) that says
   "stream this call's audio to our server" using `<Connect><Stream>` — this is
   **Media Streams**, a WebSocket audio feed. No SIP trunk needed.
4. LiveKit's **Twilio Connector** receives that audio stream and drops the caller
   into a **LiveKit room**.
5. Our **AI agent** is already in that room: it greets the candidate, asks the
   preset questions, listens, and responds. Every turn is logged.

The only "extra" for the free path vs. a paid trunk: because Twilio needs to
reach our webhook over the public internet, we run a small free tunnel
(**ngrok**) during the demo that gives Twilio a public URL pointing at the local
machine. Rishi handles the webhook code; you handle the Twilio number + keys.

Demo scope: **2 roles** — Staff Pharmacist and Oncology RN. Company context:
Soliant (healthcare/education staffing).

---

## The services involved, in plain language

- **LiveKit** — the "meeting room" service. Each call happens in a virtual room
  where the candidate's audio and the AI agent meet. We use *LiveKit Cloud*
  (hosted) so nobody runs servers.
- **Twilio** — the phone company. It gives us a phone number and, via the
  **Voice webhook + Media Streams**, streams the call audio to our app. On the
  **free trial** this is free within the included minutes.
- **Deepgram** — turns the candidate's *speech into text* (so the AI understands).
- **Cartesia** — turns the AI's *text into speech* (so the candidate hears a voice).
- **OpenAI (GPT-4o)** — the AI that decides follow-up questions.

Each service gives us an **API key** — a secret password our software uses.
Your job includes collecting these keys and putting them in one place (`.env`)
safely.

---

## What "keys in a .env file" means (and why it matters)

- An **API key** is a secret credential. If it leaks, someone can run up charges
  on our accounts. So keys must **never** be committed to the repo or shared in
  chat/email.
- We keep them in a file named **`.env`** (there's a template, `.env.example`,
  listing exactly which keys are needed). `.env` stays only on the demo machine
  and is git-ignored already.
- Your deliverable: a filled-in `.env`, kept private.

---

## Your checklist (do these in order)

Steps marked ⚠️ need a console login. None of this requires paying.

### 1. ⚠️ Create the accounts and collect keys (all free tiers)
- LiveKit Cloud → project URL + an **API key** and **API secret**.
- Deepgram → one API key (free credit on signup).
- OpenAI → one API key (GPT-4o). We already have this one.
- Cartesia → one API key (free tier).

### 2. Fill in the `.env` file
- Copy the template: `cp .env.example .env`
- Paste each value next to its name (e.g. `DEEPGRAM_API_KEY=...`).
- Leave the outbound-only fields (`SIP_OUTBOUND_TRUNK_ID`, `OUTBOUND_CALLER_ID`)
  **blank for now** — they belong to the funded-later outbound phase.

### 3. ⚠️ Twilio trial number (FREE — do NOT upgrade)
- Sign up for a free Twilio trial. It comes with free voice minutes (~75) and a
  trial number.
- Buy/claim a **trial phone number** that can receive voice calls, using the
  trial credit. Put it in `.env` as `TWILIO_PHONE_NUMBER`.
- **Do not** click "Upgrade account" and **do not** create an Elastic SIP Trunk
  — that's the paid path we're avoiding.
- Note: on a trial, callers hear a short "trial account" message first, and
  there can be verified-number restrictions. That's fine for the demo.

### 4. Point the number's Voice webhook at our app (with Rishi)
- In the number's config, there's a **"A Call Comes In"** Voice webhook URL.
- Rishi will run the webhook + the ngrok tunnel and give you a public URL like
  `https://xxxx.ngrok.io/incoming`. You paste that into the number's Voice
  webhook field and save.
- This is the one step you and Rishi do together.

### 5. Keep the demo content ready
- **Question content** — `../roles/*.yaml` and `../roles/behavioral.yaml`. The
  wording, tone, and what we screen for is a product call. Review/refine these.
- (Candidate sheet `candidates.csv` is for the outbound phase — skip for now.)

### 6. Run the demo (once Rishi's code is ready)
Rishi confirms when the webhook + agent are implemented. Then:
- Rishi starts the agent worker and the webhook + ngrok tunnel.
- You (or anyone) **call the Twilio trial number** from a phone.
- The agent answers, runs the interview, and every turn is logged.

---

## Product-side things worth owning
- **Question content & tone** in `../roles/` (as above).
- **Roles for the demo** — we're limiting to two; if a different pair demos
  better, decide and tell Rishi.
- **Consent/compliance** — an AI answering candidate calls may need a spoken
  disclosure/consent line at the start. Decide the wording; it lives in the
  greeting.
- **When to fund outbound** — decide if/when we pay to enable outbound dialing
  (Twilio upgrade or LiveKit Phone Numbers), which unlocks `candidates.csv` +
  the dispatcher.

---

## Where everything lives
| Thing | You touch? | Location |
| --- | --- | --- |
| API keys / secrets | Yes | `.env` (from `.env.example`) |
| Twilio trial number + Voice webhook | Yes (with Rishi) | Twilio console |
| Question wording | Shared | `../roles/*.yaml` |
| Webhook / agent / interview code | No (Rishi) | `../src/` |
| Candidate sheet (outbound, later) | Later | `../candidates.csv` |

## Glossary
Every technical term here (webhook, Media Streams, TwiML, LiveKit, ngrok, etc.)
is defined in plain language in `../GLOSSARY.md`.
