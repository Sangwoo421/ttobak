"""Provider selection (by Settings) + SafeLLM, the try/except wrapper app/core/state_machine.py calls as ctx.llm.

Only the stub providers exist right now (openai_provider.py / anthropic_llm.py land later without
changing this module's callers): the build_* functions already branch on settings so wiring a real
provider in later is a matter of adding a branch, not touching main.py or the routers.
"""
from __future__ import annotations

from app.config import Settings
from app.providers.base import LLMProvider, STTProvider, TTSProvider
from app.providers.stub_provider import StubLLMProvider, StubSTTProvider, StubTTSProvider


def build_stt_provider(settings: Settings) -> tuple[STTProvider, str]:
    # TODO: settings.openai_api_key -> OpenAI STT (not implemented in this pass)
    return StubSTTProvider(), "stub"


def build_tts_provider(settings: Settings) -> tuple[TTSProvider, str]:
    # TODO: settings.openai_api_key -> OpenAI TTS (not implemented in this pass)
    return StubTTSProvider(), "stub"


def build_llm_provider(settings: Settings) -> tuple[LLMProvider, str]:
    # TODO: settings.llm_provider == "openai" | "anthropic" -> real provider (not implemented in this pass)
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
