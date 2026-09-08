"""sha1(text+tone+model) -> audio_cache/<hash>.<ext>. Same text+tone+model reuses the file."""
from __future__ import annotations

import hashlib
from typing import Callable

from app.config import AUDIO_CACHE_DIR

Synthesize = Callable[[str, str], tuple[bytes, str]]


def audio_url_for(text: str, tone: str, model: str, synthesize: Synthesize) -> tuple[str, bool]:
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = f"{text}\x1f{tone}\x1f{model}".encode("utf-8")
    digest = hashlib.sha1(key).hexdigest()

    existing = next(AUDIO_CACHE_DIR.glob(f"{digest}.*"), None)
    if existing is not None:
        return f"/ai/audio/{existing.name}", True

    audio_bytes, ext = synthesize(text, tone)
    path = AUDIO_CACHE_DIR / f"{digest}.{ext}"
    path.write_bytes(audio_bytes)
    return f"/ai/audio/{path.name}", False
