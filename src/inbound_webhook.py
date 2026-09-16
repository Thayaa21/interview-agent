"""Twilio inbound Voice webhook (free path — no SIP trunk).

Owner: Rishi. Run locally behind ngrok; give Baradhwaj the public URL to paste
into the Twilio number's "A Call Comes In" webhook (see scripts/setup.md).

Flow (per LiveKit's Twilio Connector — https://docs.livekit.io/telephony/connectors/twilio/):
  1. Twilio POSTs to /incoming when someone calls the trial number.
  2. We call `connector.connect_twilio_call` (livekit-api) with a fresh room
     name and a RoomAgentDispatch (agent_name + role/phone as JSON metadata —
     the caller is anonymous for inbound, so no name is known ahead of time).
     This single call both dispatches our agent into the room AND returns a
     `connect_url` (a per-call WebSocket URL) — there is no static/dashboard
     connector URL to configure.
  3. We return TwiML `<Connect><Stream url="{connect_url}">` so Twilio Media
     Streams bridges the caller's audio into that room.

Run:
    uvicorn src.inbound_webhook:app --port 8080 --reload
    ngrok http 8080
"""

from __future__ import annotations

import json
import logging
import re
from xml.sax.saxutils import escape, quoteattr

from fastapi import FastAPI, Query, Request, Response

from .config import load_settings
from .questionbank import available_roles

logger = logging.getLogger(__name__)
app = FastAPI(title="Soliant inbound interview webhook")


def _room_name(call_sid: str) -> str:
    safe_sid = re.sub(r"[^A-Za-z0-9]", "", call_sid) or "unknown"
    return f"interview-inbound-{safe_sid}"


def _say_and_hangup_twiml(message: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Say>{escape(message)}</Say><Hangup/></Response>"
    )


def _connect_stream_twiml(stream_url: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Connect><Stream url={quoteattr(stream_url)}/></Connect></Response>"
    )


async def _connect_twilio_call(call_sid: str, caller_phone: str, role_id: str) -> str:
    """Dispatch the agent + bridge this call into a fresh room; return connect_url."""
    from livekit import api

    settings = load_settings(profile="runtime")
    room_name = _room_name(call_sid)
    metadata = json.dumps({"role": role_id, "phone": caller_phone})

    lkapi = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    try:
        res = await lkapi.connector.connect_twilio_call(
            api.ConnectTwilioCallRequest(
                twilio_call_direction=api.ConnectTwilioCallRequest.TWILIO_CALL_DIRECTION_INBOUND,
                room_name=room_name,
                participant_identity=caller_phone or call_sid,
                participant_name=caller_phone or "caller",
                agents=[api.RoomAgentDispatch(agent_name=settings.agent_name, metadata=metadata)],
            )
        )
        return res.connect_url
    finally:
        await lkapi.aclose()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/incoming")
async def incoming_call(request: Request, role: str = Query(default="")) -> Response:
    """Twilio "A Call Comes In" webhook. Returns TwiML bridging into LiveKit."""
    settings = load_settings(profile="runtime")

    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    caller_phone = form.get("From", "")

    valid_roles = set(available_roles())
    role_id = role if role in valid_roles else settings.default_role
    if role_id not in valid_roles:
        twiml = _say_and_hangup_twiml("Sorry, this interview line is not configured correctly. Goodbye.")
        return Response(content=twiml, media_type="application/xml")

    try:
        connect_url = await _connect_twilio_call(call_sid, caller_phone, role_id)
    except Exception:
        logger.exception("Failed to connect Twilio call %s into a LiveKit room", call_sid)
        twiml = _say_and_hangup_twiml(
            "Sorry, we couldn't connect you to an interviewer right now. Please try again later."
        )
        return Response(content=twiml, media_type="application/xml")

    return Response(content=_connect_stream_twiml(connect_url), media_type="application/xml")
