import logging
import os

import sentry_sdk
from livekit.plugins import deepgram, openai
from livekit.plugins.turn_detector.multilingual import (  # noqa: F401 (openrtc shared prewarm)
    MultilingualModel,
)
from openrtc import AgentPool

from src.agents.agent_realty import RealtyAgent
from src.core.config import config

logger = logging.getLogger("agent")

# Quiet noisy third-party loggers.
for _noisy in ("livekit.plugins", "livekit.turn_detector", "asyncio"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        traces_sample_rate=0.2,
        environment=os.getenv("FLY_APP_NAME", "development"),
    )


def build_pool() -> AgentPool:
    """Construct the openrtc pool that hosts RealtyAgent.

    One worker runs many concurrent calls as asyncio tasks (coroutine isolation),
    lifting the box from a handful of calls to ~50. openrtc shares one Silero VAD +
    turn detector across every session (prewarmed once per worker), so the per-call
    setup that used to live in the entrypoint now runs in RealtyAgent.on_enter
    (post-connect, where the participant and room are available). Set
    AGENT_ISOLATION=process for hard per-call crash isolation.
    """
    pool = AgentPool(
        default_stt=deepgram.STT(model="nova-3"),
        default_llm=openai.LLM(model="gpt-4.1-mini"),
        # Deepgram Aura TTS reads DEEPGRAM_API_KEY, the same funded key as the STT.
        default_tts=deepgram.TTS(model="aura-2-thalia-en"),
        isolation=os.getenv("AGENT_ISOLATION", "coroutine"),
        max_concurrent_sessions=int(os.getenv("AGENT_MAX_CONCURRENT_SESSIONS", "50")),
        drain_timeout=300,
    )
    # greeting=None: on_enter owns the opening reply (recording disclosure + the
    # realtor's persona + returning-caller recall). One agent, addressed by the
    # worker's agent_name; the room name carries the realtor (tenant).
    pool.add(config.AGENT_NAME, RealtyAgent, greeting=None)
    return pool


if __name__ == "__main__":
    build_pool().run()
