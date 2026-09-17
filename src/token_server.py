"""Tiny LiveKit token server for the browser demo.

Mints an access token so a browser can join a LiveKit room on your project.
The agent worker (run with AGENT_AUTO_DISPATCH=1) auto-joins that room and starts
the interview using the real pipeline (Deepgram + GPT-4o + Cartesia).

Run:
    python -m src.token_server           # serves http://localhost:8790

Endpoints:
    GET /token?identity=you&room=interview-demo
        -> {"url": "<LIVEKIT_URL>", "token": "<jwt>", "room": "..."}
    GET /                                  -> a minimal connect page (uses the
        LiveKit Agents Playground link, prefilled) + raw token for copy/paste.
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from livekit import api

from .config import load_settings

app = FastAPI(title="LiveKit demo token server")


def _mint_token(identity: str, room: str) -> str:
    settings = load_settings(profile="none")
    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room))
    )
    return token.to_jwt()


@app.get("/token")
async def token(identity: str = "candidate", room: str = "", role: str = ""):
    settings = load_settings(profile="none")
    # Encode the role into the room name so the auto-dispatch agent can read it
    # (browser path has no job metadata). Format: interview-<role>-<rand>.
    if not room:
        role = role or settings.default_role
        room = f"interview-{role}-{uuid.uuid4().hex[:6]}"
    return {"url": settings.livekit_url, "token": _mint_token(identity, room), "room": room}


# allow CORS for the dev frontend
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/", response_class=HTMLResponse)
async def index():
    settings = load_settings(profile="none")
    room = f"interview-demo-{uuid.uuid4().hex[:6]}"
    jwt = _mint_token("candidate", room)
    url = settings.livekit_url
    playground = "https://agents-playground.livekit.io/"
    return f"""<!doctype html><html><head><meta charset=utf-8>
<title>Soliant Interview — connect</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0d1117;color:#e6edf3;max-width:720px;margin:40px auto;padding:0 20px;line-height:1.5}}
 code,pre{{background:#161b22;border:1px solid #2a3038;border-radius:6px;padding:2px 6px;word-break:break-all;white-space:pre-wrap}}
 pre{{padding:12px}} a{{color:#4c8dff}} h1{{font-size:20px}} .box{{margin:16px 0}}
 .k{{color:#8b949e;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
</style></head><body>
<h1>Talk to the Soliant interview agent</h1>
<p>The agent worker must be running in auto-dispatch mode:
<br><code>AGENT_AUTO_DISPATCH=1 python -m src.agent dev</code></p>
<ol>
<li>Open the <a href="{playground}" target=_blank>LiveKit Agents Playground</a> (Chrome/Edge).</li>
<li>Choose "Manual" / "Connect with token" and paste the values below.</li>
<li>Allow the mic. The agent joins room <b>{room}</b> and starts the interview.</li>
</ol>
<div class=box><div class=k>LiveKit URL</div><pre>{url}</pre></div>
<div class=box><div class=k>Room</div><pre>{room}</pre></div>
<div class=box><div class=k>Token</div><pre>{jwt}</pre></div>
<p class=k>Refresh this page for a fresh room + token.</p>
</body></html>"""


if __name__ == "__main__":
    import uvicorn

    settings = load_settings(profile="none")
    uvicorn.run(app, host="0.0.0.0", port=8790)
