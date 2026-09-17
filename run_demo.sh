#!/usr/bin/env bash
# One-command launcher for the browser voice demo.
# Starts ALL FOUR services: agent worker, token server, dashboard backend,
# and the frontend. Ctrl+C stops everything.
#
#   ./run_demo.sh
#
# Requires: a filled-in .env (LiveKit + Deepgram + OpenAI + Cartesia keys),
# a .venv with `pip install -r requirements.txt`, and `npm install` done once
# in layer/frontend. See baradhwaj/RUN.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "ERROR: no .env found. Run: cp .env.example .env  then fill in your keys."
  exit 1
fi
if [ ! -d .venv ]; then
  echo "ERROR: no .venv. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source .venv/bin/activate

if [ ! -d layer/frontend/node_modules ]; then
  echo "==> Installing frontend deps (first run)…"
  (cd layer/frontend && npm install --no-audit --no-fund)
fi

pids=()
cleanup() { echo; echo "Stopping all services…"; for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

echo "==> [1/4] agent worker (auto-dispatch)"
AGENT_AUTO_DISPATCH=1 python -m src.agent dev & pids+=($!)

echo "==> [2/4] token server (:8790)"
python -m src.token_server & pids+=($!)

echo "==> [3/4] dashboard backend (:8000)"
python -m uvicorn layer.server.app:app --port 8000 & pids+=($!)

sleep 2
echo "==> [4/4] dashboard frontend (:5173)"
echo "    Open http://localhost:5173 in Chrome, pick 'Oncology RN', click 'Talk to agent'."
(cd layer/frontend && npm run dev)
