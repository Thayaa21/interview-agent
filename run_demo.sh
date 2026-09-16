#!/usr/bin/env bash
# One-command launcher for the browser voice demo.
#
#   ./run_demo.sh
#
# Starts the FastAPI backend (:8000) and the Vite dashboard (:5173), then open
# http://localhost:5173 in Chrome or Edge and click "📞 Call me".
#
# No API keys required — the demo runs on the heuristic interpreter and the
# code-driven guardrails. If OPENAI_API_KEY is set in the environment, the
# answer interpreter will use GPT-4o (once its call is wired).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "==> Checking Python deps (fastapi, uvicorn, pyyaml)…"
python3 -c "import fastapi, uvicorn, yaml" 2>/dev/null || {
  echo "Installing layer backend deps…"
  python3 -m pip install -r layer/requirements.txt
}

echo "==> Starting backend on http://localhost:8000"
python3 -m uvicorn layer.server.app:app --port 8000 &
BACKEND_PID=$!

cleanup() { echo; echo "Stopping…"; kill "$BACKEND_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

cd layer/frontend
if [ ! -d node_modules ]; then
  echo "==> Installing frontend deps (first run)…"
  npm install --no-audit --no-fund
fi

echo "==> Starting dashboard on http://localhost:5173"
echo "    Open it in Chrome/Edge and click '📞 Call me'."
npm run dev
