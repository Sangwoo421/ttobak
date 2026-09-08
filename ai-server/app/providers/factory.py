"""Provider selection (by Settings) + SafeLLM, the try/except wrapper app/core/state_machine.py calls as ctx.llm.

build_* pick the Gemini provider (app/providers/gemini_provider.py) when settings.gemini_api_key is
set, and fall back to the stub providers when it is not — or when constructing the real provider
raises. /ai/health reports the choice per capability via app.state.provider_names. Gemini's STT/TTS
models are previews that rate-limit, so the Gemini providers themselves also degrade to stub output
on a per-call failure; the demo must never die on the wire.
"""
from __future__ import annotations

import logging

from app.config import Settings
from app.providers.base import LLMProvider, STTProvider, TTSProvider
from app.providers.stub_provider import StubLLMProvider, StubSTTProvider, StubTTSProvider

logger = logging.getLogger(__name__)


def build_stt_provider(settings: Settings) -> tuple[STTProvider, str]:
    if settings.gemini_api_key:
        try:
            from app.providers.gemini_provider import GeminiSTTProvider

            return GeminiSTTProvider(settings.gemini_api_key, settings.gemini_stt_model), "gemini"
        except Exception as exc:  # noqa: BLE001 - wiring must never crash startup; stub keeps the app up
            logger.warning("Gemini STT unavailable (%s); using stub", exc)
    return StubSTTProvider(), "stub"


def build_tts_provider(settings: Settings) -> tuple[TTSProvider, str]:
    if settings.gemini_api_key:
        try:
            from app.providers.gemini_provider import GeminiTTSProvider

            return (
                GeminiTTSProvider(settings.gemini_api_key, settings.gemini_tts_model, settings.gemini_tts_voice),
                "gemini",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini TTS unavailable (%s); using stub", exc)
    return StubTTSProvider(), "stub"


def build_llm_provider(settings: Settings) -> tuple[LLMProvider, str]:
    if settings.gemini_api_key:
        try:
            from app.providers.gemini_provider import GeminiLLMProvider

            return GeminiLLMProvider(settings.gemini_api_key, settings.gemini_llm_model), "gemini"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini LLM unavailable (%s); using stub", exc)
    return StubLLMProvider(), "stub"


class SafeLLM:
    """Wraps a raw LLMProvider so a dead/misbehaving provider can never crash a turn.

    Every method returns (result, error): error is None on success, or a string on exception —
    in which case result is the same stub-shaped fallback state_machine.py already treats as "no answer".
    """

    def __init__(self, provider: LLMProvider, name: str) -> None:
        self._provider = provider
        self.name = name

    def classify_intent(self, text: str, candidate_intents: list[str]) -> tuple[tuple[str, float], str | None]:
        try:
            return self._provider.classify_intent(text, candidate_intents), None
        except Exception as exc:  # noqa: BLE001 - must never raise into the turn handler
            return ("UNKNOWN", 0.3), str(exc)

    def choose_candidate(self, text: str, options: list[dict]) -> tuple[str | None, str | None]:
        try:
            return self._provider.choose_candidate(text, options), None
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)

    def explain(self, facts: list[str], question: str) -> tuple[str | None, str | None]:
        try:
            return self._provider.explain(facts, question), None
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)


def build_safe_llm(settings: Settings) -> SafeLLM:
    provider, name = build_llm_provider(settings)
    return SafeLLM(provider, name)
