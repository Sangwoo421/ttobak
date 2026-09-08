"""Network-free fallback providers. Lets the app run (and demo survive) with no API keys."""
from __future__ import annotations

import io
import wave

_DEFAULT_STT_TEXT = "테스트 음성입니다"
_SILENCE_FRAMERATE = 16000
_SILENCE_SECONDS = 0.5


class StubSTTProvider:
    def transcribe(self, audio_bytes: bytes, filename: str, hints: list[str] | None = None,
                    stub_text: str | None = None) -> str:
        return stub_text or _DEFAULT_STT_TEXT


class StubTTSProvider:
    def synthesize(self, text: str, tone: str = "friendly") -> tuple[bytes, str]:
        n_frames = int(_SILENCE_FRAMERATE * _SILENCE_SECONDS)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(_SILENCE_FRAMERATE)
            wf.writeframes(b"\x00\x00" * n_frames)
        return buf.getvalue(), "wav"


class StubLLMProvider:
    def classify_intent(self, text: str, candidate_intents: list[str]) -> tuple[str, float]:
        return "UNKNOWN", 0.3

    def choose_candidate(self, text: str, options: list[dict]) -> str | None:
        return None

    def explain(self, facts: list[str], question: str) -> str:
        return ""
