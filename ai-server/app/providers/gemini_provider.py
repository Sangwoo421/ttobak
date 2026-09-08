"""Google Gemini implementations of the three provider Protocols (app/providers/base.py).

Selected by app/providers/factory.py when settings.gemini_api_key is set; falls back to the
stub providers otherwise, and — because the TTS/STT models here are previews that rate-limit —
degrades to stub output on any per-call failure instead of taking a demo turn down.

STT  : gemini-3.5-transcribe via the Interactions REST API (google-genai 1.47 has no
       client.interactions yet). Audio goes up inline as base64; nothing touches disk.
       Recognition hints ride in generation_config.transcription_config.custom_vocabulary.
TTS  : gemini-3.1-flash-tts-preview via generate_content; response is 24 kHz mono PCM which
       we wrap with the stdlib wave module. Per-tone style comes from senior-mode-policy.md §3.
LLM  : a Gemini text model, answering as JSON for classify_intent / choose_candidate / explain.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import wave
from typing import Any

import httpx
from google import genai
from google.genai import types

from app.providers.stub_provider import StubTTSProvider

logger = logging.getLogger(__name__)

# --- STT -------------------------------------------------------------------
_INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
_MAX_CUSTOM_VOCAB = 1000  # Interactions API cap on custom_vocabulary phrases
_STT_LANGUAGE = "ko-KR"   # language is auto-detected; naming it makes custom_vocabulary bite harder

_MIME_BY_EXT = {
    "webm": "audio/webm", "wav": "audio/wav", "mp3": "audio/mp3", "m4a": "audio/mp4",
    "mp4": "audio/mp4", "ogg": "audio/ogg", "oga": "audio/ogg", "opus": "audio/ogg",
    "flac": "audio/flac", "aac": "audio/aac", "3gp": "audio/3gpp",
}
_DEFAULT_MIME = "audio/webm"  # the frontend records WebM/Opus

# --- TTS -------------------------------------------------------------------
_TTS_SAMPLE_RATE = 24000
_TTS_CHANNELS = 1
_TTS_SAMPWIDTH = 2  # 16-bit little-endian PCM

# senior-mode-policy.md §3 톤 표 — instructions column, verbatim.
_TONE_STYLE = {
    "friendly": "노인에게 말하듯 천천히, 또렷하게, 따뜻하게. 문장 사이에 짧게 쉰다.",
    "confirm": "은행 창구 직원이 중요한 내용을 확인하듯 또박또박, 단어 사이를 띄어 읽는다.",
}


def _mime_for(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _MIME_BY_EXT.get(ext, _DEFAULT_MIME)


def _extract_transcript(payload: dict) -> str:
    """Pull the transcript out of an Interactions response.

    Newer responses expose output_text; the current one nests it in
    steps[type=model_output].content[type=text].text.
    """
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    chunks: list[str] = []
    for step in payload.get("steps") or []:
        if step.get("type") not in (None, "model_output"):
            continue
        for part in step.get("content") or []:
            if part.get("type") in (None, "text") and part.get("text"):
                chunks.append(str(part["text"]))
    return " ".join(c.strip() for c in chunks).strip()


class GeminiSTTProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._http = httpx.Client(timeout=60.0)

    def transcribe(self, audio_bytes: bytes, filename: str, hints: list[str] | None = None,
                   stub_text: str | None = None) -> str:
        if stub_text is not None:  # mic-less demo override, same contract as the stub provider
            return stub_text

        vocab = [h.strip() for h in (hints or []) if h and h.strip()][:_MAX_CUSTOM_VOCAB]
        transcription_config: dict[str, Any] = {"language_codes": [_STT_LANGUAGE]}
        if vocab:
            transcription_config["custom_vocabulary"] = vocab

        body = {
            "model": self._model,
            "input": [{
                "type": "audio",
                "data": base64.b64encode(audio_bytes).decode("ascii"),  # in-memory only, never written
                "mime_type": _mime_for(filename),
            }],
            "generation_config": {"transcription_config": transcription_config},
        }
        resp = self._http.post(
            _INTERACTIONS_URL,
            headers={"x-goog-api-key": self._api_key, "Content-Type": "application/json"},
            json=body,
        )
        resp.raise_for_status()
        return _extract_transcript(resp.json())


def _pcm_from_response(resp: Any) -> bytes:
    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            data = inline.data
            return base64.b64decode(data) if isinstance(data, str) else bytes(data)
    raise RuntimeError("Gemini TTS response carried no audio part")


def _wrap_pcm_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(_TTS_CHANNELS)
        wf.setsampwidth(_TTS_SAMPWIDTH)
        wf.setframerate(_TTS_SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


class GeminiTTSProvider:
    def __init__(self, api_key: str, model: str, voice: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._voice = voice
        self._fallback = StubTTSProvider()

    def synthesize(self, text: str, tone: str = "friendly") -> tuple[bytes, str, bool]:
        try:
            return self._synthesize(text, tone), "wav", False
        except Exception as exc:  # noqa: BLE001 - a preview-model rate limit must not cost the demo its voice
            logger.warning("Gemini TTS failed (%s); returning silent stub audio (not cached, retried next call)", exc)
            return self._fallback.synthesize(text, tone)  # (silence, "wav", True) — audio_cache won't persist it

    def _synthesize(self, text: str, tone: str) -> bytes:
        style = _TONE_STYLE.get(tone, _TONE_STYLE["friendly"])
        prompt = f"다음 문장을 이렇게 읽어 주세요 — {style}\n\n{text}"
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=self._voice)
                    )
                ),
            ),
        )
        return _wrap_pcm_wav(_pcm_from_response(resp))


class GeminiLLMProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _json(self, system: str, user: str) -> dict:
        resp = self._client.models.generate_content(
            model=self._model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        return json.loads(resp.text or "{}")

    def classify_intent(self, text: str, candidate_intents: list[str]) -> tuple[str, float]:
        system = (
            "너는 은행 앱 어르신 모드 음성비서의 의도 분류기다. "
            "사용자 발화를 아래 후보 목록 중 정확히 하나로 분류한다. "
            "후보에 맞는 것이 없으면 intent 는 \"UNKNOWN\". "
            '출력은 JSON 하나뿐: {"intent": string, "confidence": number}. confidence 는 0~1.'
        )
        user = f'발화: "{text}"\n후보: {json.dumps(candidate_intents, ensure_ascii=False)}'
        data = self._json(system, user)
        intent = str(data.get("intent", "UNKNOWN"))
        if intent not in candidate_intents:
            intent = "UNKNOWN"
        try:
            conf = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        return intent, max(0.0, min(1.0, conf))

    def choose_candidate(self, text: str, options: list[dict]) -> str | None:
        system = (
            "사용자가 말한 대상을 보기 중에서 고른다. 보기의 id 값 하나를 고르되, "
            "확신이 없으면 null 로 답한다. "
            '출력은 JSON 하나뿐: {"id": string|null}.'
        )
        user = f'발화: "{text}"\n보기: {json.dumps(options, ensure_ascii=False)}'
        data = self._json(system, user)
        chosen = data.get("id")
        valid = {o.get("id") for o in options}
        return chosen if chosen in valid else None

    def explain(self, facts: list[str], question: str) -> str:
        system = (
            "너는 은행 앱의 안내 음성이다. 아래 facts 에 있는 내용만 말한다. "
            "facts 에 없는 이유·기관·금액·날짜를 지어내지 않는다. "
            "두 문장 이내, 한 문장에 한 가지 정보, 존댓말 종결은 \"-요\". "
            "생활어를 쓴다(출금=나간 돈, 입금=들어온 돈, 이체=보내기, 잔액=남은 돈). "
            "모르는 것은 \"제가 알 수 없어요\"라고 말하고 창구 안내로 잇는다. "
            '출력은 JSON 하나뿐: {"text": string, "used_facts": [string]}.'
        )
        user = f'facts: {json.dumps(facts, ensure_ascii=False)}\n질문: "{question}"'
        data = self._json(system, user)
        return str(data.get("text", "")).strip()
