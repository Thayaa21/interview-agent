"""LiveKit Agents worker entrypoint (inbound interview, free demo).  [SKELETON]

Owner: Rishi (pipeline wiring) + Baradhwaj (worker registration / setup).

For the free inbound demo, `src/inbound_webhook.py` bridges a Twilio call into a
LiveKit room via the Twilio Connector and dispatches this named agent into it,
with the role passed as job metadata (candidate name/phone are NOT known ahead
of time for inbound — the caller is anonymous until they speak). When the agent
joins, it should:
  * read the role (and candidate name, if any) from job metadata,
  * load the role's question bank,
  * greet + ask preset questions one at a time (role + behavioral),
  * ask up to MAX_FOLLOWUPS follow-ups per question (GPT-4o decides, code caps),
  * close + hang up after the last question,
  * log every turn.

Intended usage once implemented:
    python -m src.agent dev

NOTE: written against livekit-agents ~1.x (AgentSession, Deepgram/Cartesia/
OpenAI/Silero plugins, LiveKit turn detector). Verify exact class/event names
against the installed SDK version before relying on this in a live call.
"""

from __future__ import annotations

import json

from .config import load_settings
from .interview import ActionKind, InterviewController
from .questionbank import load_role
from .reasoner import OpenAIReasoner
from .transcript import SPEAKER_AGENT, SPEAKER_CANDIDATE, create_logger


async def entrypoint(ctx) -> None:  # ctx: livekit.agents.JobContext
    """Per-call agent entrypoint."""
    from livekit import agents
    from livekit.agents import Agent, AgentSession
    from livekit.agents.inference import TurnDetector
    from livekit.plugins import cartesia, deepgram, openai as lk_openai, silero

    settings = load_settings(profile="runtime")
    await ctx.connect()

    metadata = json.loads(ctx.job.metadata or "{}")
    candidate_name = metadata.get("name") or "there"
    role_id = metadata.get("role") or settings.default_role
    candidate_phone = metadata.get("phone", "")

    role = load_role(role_id)
    logger = create_logger(
        session_id=ctx.room.name,
        backend=settings.transcript_backend,
        path=settings.transcript_path,
        candidate=candidate_name,
        role=role_id,
        phone=candidate_phone,
    )
    reasoner = OpenAIReasoner(api_key=settings.openai_api_key, model=settings.interview_model)
    controller = InterviewController(
        role=role,
        candidate_name=candidate_name,
        reasoner=reasoner,
        max_followups=settings.max_followups,
    )

    session = AgentSession(
        stt=deepgram.STT(model=settings.stt_model, api_key=settings.deepgram_api_key),
        llm=lk_openai.LLM(model=settings.interview_model, api_key=settings.openai_api_key),
        tts=cartesia.TTS(model=settings.tts_model, api_key=settings.cartesia_api_key),
        vad=silero.VAD.load(),
        turn_detection=TurnDetector(),
    )

    @session.on("user_input_transcribed")
    def _on_user_transcript(event) -> None:
        if not getattr(event, "is_final", False):
            return
        text = event.transcript
        logger.log(SPEAKER_CANDIDATE, text)

        action = controller.handle_answer(text)
        logger.log(SPEAKER_AGENT, action.text)
        session.say(action.text)

        if action.kind == ActionKind.END:
            logger.close()
            ctx.shutdown()

    await session.start(agent=Agent(instructions="Conduct the interview exactly as scripted."), room=ctx.room)

    opening = controller.first_prompt()
    logger.log(SPEAKER_AGENT, opening)
    session.say(opening)


if __name__ == "__main__":
    from livekit import agents
    from livekit.agents import WorkerOptions

    settings = load_settings(profile="none")
    agents.cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=settings.agent_name))
