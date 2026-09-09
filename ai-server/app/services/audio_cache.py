"""sha1(text+tone+model) -> audio_cache/<hash>.<ext>. Same text+tone+model reuses the file.

A synthesize() result is written to the cache only when it is a real synthesis: the provider must
report is_fallback=False AND the audio must be at least _MIN_CACHE_BYTES. A fallback (silent stub
after a rate limit) or a suspiciously tiny clip is NOT written anywhere — the caller gets
FALLBACK_AUDIO_URL (served from memory by GET /ai/audio-fallback) and the phrase is re-synthesized
on the next call. One rehearsal 429 can no longer leave a sentence permanently silent.

The same _MIN_CACHE_BYTES floor is applied on *read*: a previously cached file that is now under the
floor (e.g. a ~16 KB silent stub written by an older build, or before the provider was switched to a
real TTS) is deleted and re-synthesized instead of being served. A teammate swapping providers does
not have to remember to wipe audio_cache/ by hand — it heals itself on the next call.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Callable

from app.config import AUDIO_CACHE_DIR

logger = logging.getLogger(__name__)

# (audio_bytes, ext, is_fallback)
Synthesize = Callable[[str, str], tuple[bytes, str, bool]]

# Real senior-mode sentences at 24 kHz are ~300 KB+; the silent stub is ~16-24 KB. Anything under
# this is treated as "not a real synthesis" and is not cached.
_MIN_CACHE_BYTES = 40_000

# Not a file under audio_cache/ — GET /ai/audio-fallback streams silence from memory (app/routers/tts.py).
FALLBACK_AUDIO_URL = "/ai/audio-fallback"

# 대체 음성(예: Gemini 429 → Windows 내장 음성)은 디스크 캐시에 넣지 않는다 — 다음 호출에서 Gemini 를
# 다시 시도해야 하니까. 대신 메모리에 잠깐 들고 있다가 GET /ai/audio-tmp/<digest>.wav 로 한 번 내준다.
# 무음 대체본과 달리 실제 소리이므로 폰에는 목소리가 나간다. 크기 제한: 최근 32개만.
_TEMP_AUDIO: dict[str, tuple[bytes, str]] = {}
_TEMP_AUDIO_MAX = 32
TEMP_AUDIO_PREFIX = "/ai/audio-tmp/"


def temp_audio(name: str) -> tuple[bytes, str] | None:
    return _TEMP_AUDIO.get(name)


def audio_url_for(text: str, tone: str, model: str, synthesize: Synthesize) -> tuple[str, bool]:
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = f"{text}\x1f{tone}\x1f{model}".encode("utf-8")
    digest = hashlib.sha1(key).hexdigest()

    for existing in sorted(AUDIO_CACHE_DIR.glob(f"{digest}.*")):
        size = existing.stat().st_size
        if size >= _MIN_CACHE_BYTES:
            return f"/ai/audio/{existing.name}", True
        # Stale undersized clip (usually a pre-switch silent stub). Don't serve it — drop it and
        # fall through to re-synthesize, so a provider swap recovers without a manual cache wipe.
        logger.warning("Evicting undersized TTS cache file %s (%d bytes < %d min); re-synthesizing",
                       existing.name, size, _MIN_CACHE_BYTES)
        existing.unlink(missing_ok=True)

    audio_bytes, ext, is_fallback = synthesize(text, tone)

    too_small = len(audio_bytes) < _MIN_CACHE_BYTES
    if is_fallback or too_small:
        reason = "provider fallback" if is_fallback else f"{len(audio_bytes)} bytes < {_MIN_CACHE_BYTES} min"
        logger.warning("TTS not cached (%s) for tone=%s text=%r; will retry next call", reason, tone, text[:60])
        if is_fallback and not too_small:
            # 실제 소리가 있는 대체 음성: 메모리에서 한 번 내준다.
            name = f"{digest}.{ext}"
            if len(_TEMP_AUDIO) >= _TEMP_AUDIO_MAX:
                _TEMP_AUDIO.pop(next(iter(_TEMP_AUDIO)))
            _TEMP_AUDIO[name] = (audio_bytes, ext)
            return f"{TEMP_AUDIO_PREFIX}{name}", False
        return FALLBACK_AUDIO_URL, False

    path = AUDIO_CACHE_DIR / f"{digest}.{ext}"
    path.write_bytes(audio_bytes)
    return f"/ai/audio/{path.name}", False
