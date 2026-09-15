"""LiveKit Agents worker entrypoint (outbound interview).  [SKELETON]

Owner: Rishi (pipeline wiring) + Baradhwaj (worker registration / dispatch config).

The dispatcher creates a per-call room, dispatches this named agent into it with
candidate context (name, role, phone) as job metadata, then dials the candidate.
When the candidate answers, the agent should:
  * read candidate context from job metadata,
  * load the role's question bank,
  * greet by name, ask preset questions one at a time (role + behavioral),
  * ask up to MAX_FOLLOWUPS follow-ups per question (GPT-4o decides, code caps),
  * close + hang up after the last question,
  * log every turn.

Intended usage once implemented:
    python -m src.agent dev

TODO(Rishi): build the AgentSession (Deepgram STT, OpenAI GPT-4o LLM, Cartesia TTS,
             Silero VAD + LiveKit turn detection), read job metadata, drive the
             InterviewController on each final transcript, log turns, hang up on END.
TODO(Baradhwaj): make sure the worker's agent_name matches the dispatch config
                 and the setup (see scripts/setup.md).
"""

from __future__ import annotations


async def entrypoint(ctx) -> None:  # ctx: livekit.agents.JobContext
    """Per-call agent entrypoint. TODO(Rishi).

    Steps:
      1. load_settings(profile="runtime")  # fail fast on missing keys
      2. await ctx.connect()
      3. parse candidate context (name/role/phone) from ctx.job.metadata
      4. load_role(role_id); build TranscriptLogger + OpenAIReasoner + InterviewController
      5. start AgentSession(stt, llm, tts, vad, turn_detection)
      6. on each FINAL user transcript: log it, controller.handle_answer(),
         speak the result, and disconnect on ActionKind.END
      7. speak controller.first_prompt() to open the call
      8. flush transcript on shutdown
    """
    raise NotImplementedError("TODO(Rishi): implement entrypoint")


if __name__ == "__main__":
    # TODO(Rishi/Baradhwaj): register the worker with LiveKit, e.g.
    #   from livekit import agents
    #   from livekit.agents import WorkerOptions
    #   settings = load_settings(profile="none")
    #   agents.cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint,
    #                                    agent_name=settings.agent_name))
    raise SystemExit("TODO: wire up WorkerOptions + agents.cli.run_app")
