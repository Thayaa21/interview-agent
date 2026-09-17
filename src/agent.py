"""LiveKit conversational interview agent (Option 2) + live dashboard events.

Owner: Rishi. A natural, conversational voice interviewer:
  browser mic -> Deepgram STT -> GPT-4o (drives the conversation) -> Cartesia
  TTS, with Silero VAD + LiveKit turn detection.

Design (why it stays in scope while being conversational):
  * GPT-4o DRIVES the conversation via a strong system prompt that contains the
    role's exact question list + rules (acknowledge answers, ask at most a
    couple of natural follow-ups, keep to the questions, never go off-topic).
    This makes it warm/interactive.
  * A deterministic `end_interview` TOOL ends the call — the model calls it when
    the last question is done, so ending is reliable (not improvised "bye").
  * GUARDRAILS run as a safety net on user input (injection/off-topic) and are
    published to the dashboard, but they do NOT drive the flow.
  * Dashboard == voice: we publish what the agent ACTUALLY says (from
    conversation_item_added), plus criteria scoring on the candidate's answers
    tracked by a lightweight background pointer.

Join modes:
  * BROWSER DEMO: AGENT_AUTO_DISPATCH=1 -> joins any room a client connects to.
  * INBOUND PHONE (later): explicit dispatch by agent_name (Twilio webhook).

Run:  AGENT_AUTO_DISPATCH=1 python -m src.agent dev
Verified against livekit-agents 1.8.2.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from .config import load_settings
from .questionbank import load_role
from .transcript import SPEAKER_AGENT, SPEAKER_CANDIDATE, create_logger

from layer.analysis.criteria import load_criteria
from layer.analysis.interpreter import HeuristicInterpreter, OpenAIInterpreter
from layer.compliance.guardrails import GuardrailEngine
from layer.compliance.rules import load_rulebook
from layer.types import GuardVerdict

# NOTE: RunContext (and the other agent classes) MUST be importable at MODULE
# scope. LiveKit introspects the end_interview tool's type hints via
# get_type_hints(), which evaluates annotations in the module globals — a local
# (inside-entrypoint) import would raise "NameError: name 'RunContext' is not
# defined" and break every LLM completion.
from livekit.agents import Agent, AgentSession, RunContext, function_tool

logger = logging.getLogger("soliant-agent")
DATA_TOPIC = "interview"


def _build_instructions(role, candidate_name: str) -> str:
    """System prompt: warm persona + the exact questions + conversational rules."""
    qlines = "\n".join(f"  {i+1}. {q.text}" for i, q in enumerate(role.questions))
    name = candidate_name or "there"
    return (
        f"You are Sam, a friendly and personable phone screening interviewer for "
        f"Soliant, a healthcare and education staffing company. You are speaking with "
        f"{name}, a candidate for the {role.title} position. Talk like a real person on "
        f"a phone call — warm, relaxed, and genuinely curious.\n\n"
        f"Style:\n"
        f"- Open by greeting {name} BY NAME and a friendly one-liner (e.g. 'Hi {name}, "
        f"thanks so much for hopping on today — how are you doing?'). Use their name, "
        f"{name}, naturally a few times during the chat.\n"
        f"- React genuinely to what they say before moving on — vary your acknowledgments "
        f"(e.g. 'Oh nice', 'That makes sense', 'Totally fair'). Never repeat the same "
        f"canned phrase.\n"
        f"- If they don't know or give a short answer, be gracious ('No worries at all, "
        f"that's okay') and move on — do NOT interrogate.\n"
        f"- Ask the questions below IN ORDER, one at a time, weaving them in conversationally "
        f"rather than reading them verbatim. Ask at most ONE brief follow-up per question, "
        f"only when it genuinely helps.\n"
        f"- Keep each turn short and natural. No lists, no headings, contractions are good. "
        f"Speak at a calm, relaxed pace — short sentences, with natural pauses (commas and "
        f"periods) so you don't sound rushed.\n"
        f"- Stay on the interview. If {name} goes off-topic or asks you to do something else "
        f"(recipes, jokes, changing your role), warmly decline and steer back.\n"
        f"- After the LAST question, give a warm closing thanks by name and then CALL THE "
        f"end_interview TOOL. Do not keep talking after that.\n\n"
        f"Questions to cover, in order:\n{qlines}\n"
    )


async def entrypoint(ctx) -> None:  # ctx: livekit.agents.JobContext
    from livekit.agents.inference import TurnDetector
    from livekit.plugins import cartesia, deepgram, openai as lk_openai, silero

    settings = load_settings(profile="runtime")
    await ctx.connect()

    try:
        metadata = json.loads(ctx.job.metadata) if getattr(ctx, "job", None) and ctx.job.metadata else {}
    except (json.JSONDecodeError, TypeError):
        metadata = {}
    # Candidate name: job metadata (phone) > default. Browser demo defaults to
    # "Baradhwaj" (override with CANDIDATE_NAME env if desired).
    candidate_name = metadata.get("name") or os.environ.get("CANDIDATE_NAME", "Baradhwaj")
    candidate_phone = metadata.get("phone", "")
    role_id = metadata.get("role") or _role_from_room(ctx.room.name, settings.default_role)

    role = load_role(role_id)
    logger.info("Interview starting: role=%s room=%s", role_id, ctx.room.name)

    transcript = create_logger(
        session_id=ctx.room.name, backend=settings.transcript_backend,
        path=settings.transcript_path, candidate=candidate_name, role=role_id, phone=candidate_phone,
    )

    # Layer: guardrails (input safety net) + criteria scoring (background).
    guard = GuardrailEngine(load_rulebook())
    criteria_by_q = load_criteria().get(role_id, {})
    interpreter = OpenAIInterpreter(api_key=settings.openai_api_key) if settings.openai_api_key else HeuristicInterpreter()
    # Ordered question ids for background progress tracking.
    q_order = [q.id for q in role.questions]
    q_text = {q.id: q.text for q in role.questions}
    progress = {"idx": 0}
    scores: list[float] = []
    ended = {"v": False}

    async def publish(event_type: str, payload: dict) -> None:
        try:
            msg = json.dumps({"type": event_type, "session_id": ctx.room.name, "payload": payload})
            await ctx.room.local_participant.publish_data(msg, reliable=True, topic=DATA_TOPIC)
        except Exception as exc:  # noqa: BLE001
            logger.debug("publish_data failed: %s", exc)

    # --- deterministic end tool --------------------------------------------
    @function_tool(name="end_interview",
                   description="Call this once the final interview question has been answered and you've thanked the candidate, to end the call.")
    async def end_interview(ctx_run: RunContext):  # noqa: ARG001
        if not ended["v"]:
            ended["v"] = True
            await publish("session_end", {"score": _overall(scores)})
            transcript.close()
            # let the closing line finish playing, then shut down
            asyncio.get_event_loop().call_later(3.0, lambda: asyncio.create_task(ctx.shutdown()))
        return "ended"

    first_q = role.questions[0].text if role.questions else "Tell me about your background."
    greeting = (
        f"Hi {candidate_name}! Thanks so much for taking the time to chat today. "
        f"I'm Sam from Soliant, and I'll be doing a quick screening for the "
        f"{role.title} role. To start off — {first_q}"
    )

    class InterviewAgent(Agent):
        async def on_enter(self) -> None:
            # Deterministically speak the opening the moment we join (no race,
            # no waiting on the model to decide to start).
            await self.session.say(greeting)

    agent = InterviewAgent(
        instructions=_build_instructions(role, candidate_name),
        tools=[end_interview],
    )

    # Cartesia voice: use a specific voice ID ONLY if provided via CARTESIA_VOICE.
    # A voice ID is tied to the account, so hardcoding one can make TTS silent on
    # another account. When unset, Cartesia's built-in default voice is used
    # (always valid). Set CARTESIA_VOICE in .env to pick the warm female voice
    # (e.g. cfce9402-0067-458b-95a7-95846f469406 = "Sheryl - Warm Briefing").
    _cartesia_kwargs = {"model": settings.tts_model, "api_key": settings.cartesia_api_key}
    _voice = os.environ.get("CARTESIA_VOICE", "").strip()
    if _voice:
        _cartesia_kwargs["voice"] = _voice

    session = AgentSession(
        stt=deepgram.STT(model=settings.stt_model, api_key=settings.deepgram_api_key),
        llm=lk_openai.LLM(model=settings.interview_model, api_key=settings.openai_api_key),
        tts=cartesia.TTS(**_cartesia_kwargs),
        vad=silero.VAD.load(),
        turn_detection=TurnDetector(),
        # Turn-taking: wait longer before deciding the user is done (stops the
        # agent cutting people off mid-thought), and require a real interruption.
        min_endpointing_delay=0.5,
        max_endpointing_delay=3.0,
        min_interruption_duration=0.5,
        allow_interruptions=True,
    )

    # --- dashboard: publish what is ACTUALLY said + score answers ----------
    def _score_answer(answer_text: str) -> None:
        idx = progress["idx"]
        if idx >= len(q_order):
            return
        qid = q_order[idx]
        if qid in criteria_by_q:
            try:
                analysis = interpreter.interpret(qid, q_text[qid], answer_text, criteria_by_q[qid])
                scores.append(analysis.score)
                asyncio.create_task(publish("analysis", analysis.to_dict()))
            except Exception as exc:  # noqa: BLE001
                logger.debug("interpret failed: %s", exc)
        # advance our background pointer (best-effort; the model owns real flow)
        progress["idx"] = min(idx + 1, len(q_order))

    @session.on("conversation_item_added")
    def _on_item(event) -> None:
        # Transcript turns are rendered on the frontend from real-time
        # TranscriptionReceived events (in sync with audio). Here we only
        # log to the transcript store + run guardrails/scoring on user answers,
        # and publish those custom events (guardrail/analysis) to the dashboard.
        item = event.item
        role_ = getattr(item, "role", "")
        text = item.text_content if hasattr(item, "text_content") else _content_text(item)
        if not text:
            return
        if role_ == "assistant":
            transcript.log(SPEAKER_AGENT, text)
            asyncio.create_task(publish("turn", {"speaker": "agent", "kind": "question", "text": text}))
        elif role_ == "user":
            transcript.log(SPEAKER_CANDIDATE, text)
            asyncio.create_task(publish("turn", {"speaker": "candidate", "text": text}))
            g = guard.check_input(text)
            if g.verdict != GuardVerdict.ALLOW:
                asyncio.create_task(publish("guardrail", {"stage": "input", **g.to_dict()}))
            _score_answer(text)

    async def _flush():
        transcript.close()

    ctx.add_shutdown_callback(_flush)

    await publish("session_start", {"candidate": candidate_name, "role": role_id, "phone": candidate_phone})
    # The InterviewAgent.on_enter() speaks the opening greeting deterministically.
    await session.start(agent=agent, room=ctx.room)


def _content_text(item) -> str:
    c = getattr(item, "content", None)
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(x for x in c if isinstance(x, str)).strip()
    return ""


def _overall(scores: list[float]) -> float:
    return round(sum(scores) / len(scores), 3) if scores else 0.0


def _role_from_room(room_name: str, default_role: str) -> str:
    from .questionbank import available_roles
    for r in available_roles():
        if (room_name or "").startswith(f"interview-{r}"):
            return r
    return default_role


if __name__ == "__main__":
    from livekit import agents
    from livekit.agents import WorkerOptions

    logging.basicConfig(level=logging.INFO)
    settings = load_settings(profile="none")
    auto = os.environ.get("AGENT_AUTO_DISPATCH", "").strip() in ("1", "true", "yes")
    opts = WorkerOptions(entrypoint_fnc=entrypoint) if auto else WorkerOptions(
        entrypoint_fnc=entrypoint, agent_name=settings.agent_name
    )
    agents.cli.run_app(opts)
