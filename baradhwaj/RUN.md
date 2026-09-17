# How to run the voice demo (Baradhwaj)

The browser voice demo: talk to the interview agent in your browser (no phone
needed). Uses the real pipeline — Deepgram (speech-to-text), OpenAI GPT-4o,
Cartesia (voice), LiveKit.

You need your OWN keys for: LiveKit, Deepgram, OpenAI, Cartesia. `.env` is NOT
in git, so you must create it (step 2).

## One-time setup

```bash
# 1) from the repo root, create a Python env + install (first time is slow)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2) create your .env from the template and fill in YOUR keys
cp .env.example .env
#   then edit .env and set:
#     LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET   (your LiveKit project)
#     DEEPGRAM_API_KEY, OPENAI_API_KEY, CARTESIA_API_KEY
#   leave CARTESIA_VOICE blank for now (uses the default voice). If you want the
#   warm female voice, paste a voice ID from YOUR Cartesia account.

# 3) install the dashboard frontend deps (first time)
cd layer/frontend
npm install
cd ../..
```

## Every time you run it — start 4 things (4 terminals)

Each terminal: run `source .venv/bin/activate` first (except the frontend one).

```bash
# Terminal 1 — the voice agent worker
AGENT_AUTO_DISPATCH=1 python -m src.agent dev

# Terminal 2 — the token server (lets the browser join)
python -m src.token_server

# Terminal 3 — the dashboard backend
python -m uvicorn layer.server.app:app --port 8000

# Terminal 4 — the dashboard frontend
cd layer/frontend
npm run dev
```

## Then

1. Open http://localhost:5173 in **Google Chrome**.
2. Choose the role **"Oncology RN"** in the dropdown.
3. Click **"Talk to agent"**, allow the mic, wait ~5 seconds for the greeting.
4. Follow `baradhwaj/demo_script.txt` to test the flow, scoring, and guardrails.

## If something's off
- **Agent is silent:** make sure CARTESIA_VOICE is blank (a voice ID from
  another account won't exist in yours). Check Terminal 1 for errors.
- **"missing environment variable" error:** a key is empty in `.env`.
- **Voice button disabled:** you're not in Chrome/Edge.
- **First response is slow:** normal on the first call (models warm up).
