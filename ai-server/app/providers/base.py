"""Provider interfaces. Real implementations (openai_provider.py, anthropic_llm.py) plug in later.

LLMProvider is the raw provider contract — no error handling. SafeLLM (app/providers/factory.py)
wraps it into the (result, error) shape app/core/state_machine.py calls.
"""
from __future__ import annotations

from typing import Protocol


class STTProvider(Protocol):
    def transcribe(self, audio_bytes: bytes, filename: str, hints: list[str] | None = None) -> str:
        """오디오 -> 텍스트."""
        ...


class TTSProvider(Protocol):
    def synthesize(self, text: str, tone: str = "friendly") -> tuple[bytes, str]:
        """텍스트 -> (오디오 바이트, 확장자)."""
        ...


class LLMProvider(Protocol):
    def classify_intent(self, text: str, candidate_intents: list[str]) -> tuple[str, float]:
        """-> (intent, confidence)."""
        ...

    def choose_candidate(self, text: str, options: list[dict]) -> str | None:
        """options 의 id 중 하나(또는 확신 없으면 None)."""
        ...

    def explain(self, facts: list[str], question: str) -> str:
        """facts 만 근거로 자유 질문에 답하는 문장."""
        ...
