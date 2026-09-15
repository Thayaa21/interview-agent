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

from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


# Variables the running agent worker needs.
REQUIRED_RUNTIME_VARS: list[str] = [
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "DEEPGRAM_API_KEY",
    "ANTHROPIC_API_KEY",
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
    anthropic_api_key: str = ""
    cartesia_api_key: str = ""
    # App
    candidate_sheet: str = "candidates.csv"
    interview_model: str = "claude-sonnet-4-5"
    stt_model: str = "nova-3"
    tts_model: str = "sonic-2"
    transcript_backend: str = "sqlite"
    transcript_path: str = "transcripts.db"
    max_followups: int = 2
    agent_name: str = "soliant-interviewer"


def load_settings(profile: str = "runtime") -> Settings:
    """Load + validate settings for a profile ("runtime" | "dispatch" | "none").

    TODO(Rishi): load from .env (python-dotenv), validate the appropriate
    required-var list for `profile`, raise ConfigError naming any missing var,
    and return a populated Settings.
    """
    raise NotImplementedError("TODO(Rishi): implement load_settings")
