"""Environment-based configuration.  [SKELETON]

Owner: Baradhwaj (owns env/secrets/setup), with Rishi consuming Settings in code.

Loads settings from a local `.env` and exposes a typed `Settings` object.
Should validate that required variables are present and fail fast with a clear
error naming any that are missing.

TODO(Baradhwaj): decide the final list of required vars and the validation
                 profiles (agent runtime vs. outbound dispatcher).
TODO(Rishi):    implement load_settings() to read + validate + return Settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


# Variables the running agent worker needs.
REQUIRED_RUNTIME_VARS: list[str] = [
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "DEEPGRAM_API_KEY",
    "OPENAI_API_KEY",
    "CARTESIA_API_KEY",
]

# Extra variables the outbound dispatcher needs to place calls.
REQUIRED_DISPATCH_VARS: list[str] = [
    "SIP_OUTBOUND_TRUNK_ID",
    "OUTBOUND_CALLER_ID",
]


@dataclass(frozen=True)
class Settings:
    """Typed view of configuration. TODO(Rishi): fill fields as needed."""

    # LiveKit
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    # Outbound SIP
    sip_outbound_trunk_id: str = ""
    outbound_caller_id: str = ""
    # Providers
    deepgram_api_key: str = ""
    openai_api_key: str = ""
    cartesia_api_key: str = ""
    # App
    candidate_sheet: str = "candidates.csv"
    interview_model: str = "gpt-4o"
    stt_model: str = "nova-3"
    tts_model: str = "sonic-2"
    transcript_backend: str = "sqlite"
    transcript_path: str = "transcripts.db"
    max_followups: int = 2
    agent_name: str = "soliant-interviewer"
    # Inbound webhook (free path)
    default_role: str = "staff_pharmacist"
    webhook_port: int = 8080


def load_settings(profile: str = "runtime") -> Settings:
    """Load + validate settings for a profile ("runtime" | "dispatch" | "none").

    Loads `.env` (if present) into the process environment, validates the
    required-var list for `profile`, and returns a populated Settings.
    """
    load_dotenv()

    if profile == "runtime":
        required = REQUIRED_RUNTIME_VARS
    elif profile == "dispatch":
        required = REQUIRED_RUNTIME_VARS + REQUIRED_DISPATCH_VARS
    elif profile == "none":
        required = []
    else:
        raise ConfigError(f"Unknown settings profile: {profile!r}")

    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ConfigError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )

    defaults = Settings()
    return Settings(
        livekit_url=os.environ.get("LIVEKIT_URL", defaults.livekit_url),
        livekit_api_key=os.environ.get("LIVEKIT_API_KEY", defaults.livekit_api_key),
        livekit_api_secret=os.environ.get("LIVEKIT_API_SECRET", defaults.livekit_api_secret),
        sip_outbound_trunk_id=os.environ.get("SIP_OUTBOUND_TRUNK_ID", defaults.sip_outbound_trunk_id),
        outbound_caller_id=os.environ.get("OUTBOUND_CALLER_ID", defaults.outbound_caller_id),
        deepgram_api_key=os.environ.get("DEEPGRAM_API_KEY", defaults.deepgram_api_key),
        openai_api_key=os.environ.get("OPENAI_API_KEY", defaults.openai_api_key),
        cartesia_api_key=os.environ.get("CARTESIA_API_KEY", defaults.cartesia_api_key),
        candidate_sheet=os.environ.get("CANDIDATE_SHEET", defaults.candidate_sheet),
        interview_model=os.environ.get("INTERVIEW_MODEL", defaults.interview_model),
        stt_model=os.environ.get("STT_MODEL", defaults.stt_model),
        tts_model=os.environ.get("TTS_MODEL", defaults.tts_model),
        transcript_backend=os.environ.get("TRANSCRIPT_BACKEND", defaults.transcript_backend),
        transcript_path=os.environ.get("TRANSCRIPT_PATH", defaults.transcript_path),
        max_followups=int(os.environ.get("MAX_FOLLOWUPS", defaults.max_followups)),
        agent_name=os.environ.get("AGENT_NAME", defaults.agent_name),
        default_role=os.environ.get("DEFAULT_ROLE", defaults.default_role),
        webhook_port=int(os.environ.get("WEBHOOK_PORT", defaults.webhook_port)),
    )
