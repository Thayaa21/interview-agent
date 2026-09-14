# Baradhwaj — Setup & Product Track

You're coming at this from **product**, not deep engineering — so this guide
explains not just *what* to do but *what each piece is* and *why it matters*.
You don't write the app code (that's Rishi, in `../rishi/`). You set up the
"outside world" the app depends on: the accounts, the secret keys, the phone
line, and the list of people to call. Without your track, Rishi's code has
nothing to run against.

Think of it like this: Rishi builds the interviewer's brain and mouth.
You give it a phone, a phone number, permission to use the AI services, and the
list of candidates to call.

---

## The big picture (how a call actually happens)

1. We keep a **candidate sheet** — a spreadsheet/CSV with each person's name,
   the role they're interviewing for, and their phone number.
2. Our software reads that sheet and, one by one, **places an outbound call** to
   each candidate.
3. When the candidate picks up, an **AI voice agent** greets them and asks a set
   of preset questions for their role, listening and asking short follow-ups.
4. Every question and answer is **saved to a transcript** for review.

For step 2 and 3 to work, several external services have to be connected. That
connection work is your track.

Demo scope: **2 roles only** — Staff Pharmacist and Oncology RN. Company context:
Soliant (healthcare/education staffing).

---

## The services involved, in plain language

- **LiveKit** — the "meeting room" service. Each phone call happens inside a
  virtual room. LiveKit is where the candidate's audio and the AI agent meet. We
  use *LiveKit Cloud* (their hosted version) so nobody has to run servers.
- **Twilio** — the phone company. It gives us a real phone number and the ability
  to actually dial out over the normal phone network.
- **SIP trunk** — the "pipe" that connects Twilio's phone network to our LiveKit
  room. "Outbound" means it's set up for *us calling out* to candidates. You
  don't need the deep technical detail; just know it's the plumbing between the
  phone number and the software, and it has to be created once.
- **Deepgram** — turns the candidate's *speech into text* (so the AI can
  understand what they said).
- **Cartesia** — turns the AI's *text into speech* (so the candidate hears a
  natural voice).
- **Anthropic (Claude)** — the AI that decides whether to ask a follow-up
  question.

Each of these services gives us an **API key** — basically a password that lets
our software use that service. Your job includes collecting all these keys and
putting them in one place (a `.env` file) safely.

---

## What "keys in a .env file" means (and why it matters)

- An **API key** is a secret credential. If it leaks, someone else can run up
  charges on our accounts. So keys must **never** be committed to the code
  repository or shared in chat/email.
- We store them in a file named **`.env`** (there's a template called
  `.env.example` showing exactly which keys are needed). The `.env` file stays
  only on the machine running the demo and is git-ignored (already configured).
- Your deliverable here: a complete, filled-in `.env`, kept private.

---

## Your checklist (do these in order)

Steps marked ⚠️ require logging into a company/console and may involve billing.
Take your time; ask Rishi if a value is unclear.

### 1. ⚠️ Create the accounts and collect keys
Sign up for (or get access to) each service and copy its key:
- LiveKit Cloud → gives you a project URL and two values: an **API key** and an
  **API secret**.
- Deepgram → one API key.
- Anthropic → one API key.
- Cartesia → one API key.

### 2. Fill in the `.env` file
- Copy the template: `cp .env.example .env`
- Open `.env` and paste each value next to its name (e.g. `DEEPGRAM_API_KEY=...`).
- Leave the app-setting lines (model names, etc.) at their defaults unless Rishi
  asks to change them.
- The file `.env.example` documents every field; you're just filling the blanks.

### 3. ⚠️ Get a phone number and phone connection from Twilio
- In Twilio, buy a phone number that can make voice calls. This becomes our
  **caller ID** — the number candidates see when we call them.
- Set up an **Elastic SIP Trunk** in Twilio. During that setup Twilio gives you a
  "termination" address and login credentials. Save these — they connect Twilio
  to LiveKit in the next step.
- Put the phone number in `.env` as `OUTBOUND_CALLER_ID` (and
  `TWILIO_PHONE_NUMBER`).

### 4. Connect Twilio to LiveKit (the outbound trunk)
- There's a template file `../scripts/outbound_trunk.json`. Fill in the Twilio
  termination address, the phone number, and the credentials from step 3.
- Create the trunk using the LiveKit command-line tool (`lk`):
  `lk sip outbound create scripts/outbound_trunk.json`
- This returns a **trunk id** that looks like `ST_...`. Put it in `.env` as
  `SIP_OUTBOUND_TRUNK_ID`. This is the ID our software uses to place calls.

### 5. ⚠️ Install and log in to the LiveKit CLI (`lk`)
- The `lk` tool is a small program that talks to LiveKit from the command line.
  Install it and authenticate it to our LiveKit project (one-time). Rishi can
  help if the install step is unfamiliar. You need this for step 4.

### 6. Keep the "agent name" consistent
- Our software registers the AI agent under a name (default:
  `soliant-interviewer`, set as `AGENT_NAME` in `.env`). The same name has to be
  used when calls are dispatched. As long as you don't change `AGENT_NAME`, this
  just works — only flag it if Rishi renames it.

### 7. Maintain the candidate sheet
- The file `../candidates.csv` is the list of people to call. It has exactly
  three columns: **name**, **role**, **phone**.
  - `name` — how the AI greets them (e.g. "Alex Taylor").
  - `role` — must be one of the two demo roles **exactly**: `staff_pharmacist`
    or `oncology_rn`. (These match the question sets in `../roles/`.)
  - `phone` — must be in **E.164** format: a `+`, the country code, then the
    number, no spaces or dashes. Example: `+14155550123`.
- Replace the example rows with real candidates. A wrong role name or a badly
  formatted phone number will be caught and rejected before any call is placed,
  so it's safe to fix and re-run.

### 8. Run the demo (with Rishi, once his code is ready)
Three commands (Rishi will confirm when the code is done):
- Start the AI agent so it's ready to answer calls:
  `python -m src.agent dev`
- Do a **dry run** first — this checks the sheet and settings without calling
  anyone: `python -m src.dispatcher --dry-run`
- When the dry run looks clean, place the real calls:
  `python -m src.dispatcher`
- To test with just one person: `python -m src.dispatcher --only +14155550123`

---

## Product-side things worth owning
Beyond the setup mechanics, these are natural fits for the product track:
- **Question content** — the actual questions in `../roles/*.yaml` and the shared
  `../roles/behavioral.yaml`. Rishi wires them up, but the *wording, tone, and
  what we're screening for* is a product call. Review and refine these.
- **Roles for the demo** — we're limiting to two. If a different pair tells a
  better story, decide that and let Rishi know (he adds a `roles/<id>.yaml`).
- **Compliance/consent** — calling candidates with an AI may require a spoken
  disclosure/consent line at the start. Decide the wording; it lives in the
  greeting. Confirm any legal requirements for the regions we call.
- **The candidate list** — who we call, and making sure numbers/consent are
  legitimate.

---

## Where everything lives
| Thing | You touch? | Location |
| --- | --- | --- |
| API keys / secrets | Yes | `.env` (from `.env.example`) |
| Twilio number + SIP trunk | Yes | Twilio console + `../scripts/outbound_trunk.json` |
| LiveKit outbound trunk id | Yes | created via `lk`, stored in `.env` |
| Candidate list | Yes | `../candidates.csv` |
| Question wording | Shared | `../roles/*.yaml` |
| Application code | No (Rishi) | `../src/` |

## Glossary
Every technical term here (SIP, trunk, E.164, API key, LiveKit, etc.) is defined
in plain language in `../GLOSSARY.md`. Keep it open as you go.
