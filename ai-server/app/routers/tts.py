"""POST /ai/tts — text (+tone) -> cached audio URL. Same text+tone+model reuses the cached file.

GET /ai/audio-fallback — 0.5 s of silence, straight from memory. audio_cache.audio_url_for points
callers here when synthesis fell back (rate limit) or returned a suspiciously tiny clip, so the app
always has *some* audio_url without a bad result ever landing in the on-disk cache.
"""
from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.providers.stub_provider import StubTTSProvider
from app.services import audio_cache

router = APIRouter()

_SILENCE_WAV = StubTTSProvider().synthesize("", "friendly")[0]


class TTSRequest(BaseModel):
    text: str
    tone: str = "friendly"


@router.post("/ai/tts")
def tts(body: TTSRequest, request: Request) -> dict:
    settings = request.app.state.settings
    tts_provider = request.app.state.tts
    audio_url, cached = audio_cache.audio_url_for(body.text, body.tone, settings.tts_model, tts_provider.synthesize)
    return {"audio_url": audio_url, "cached": cached}


@router.get("/ai/audio-fallback")
def audio_fallback() -> Response:
    return Response(content=_SILENCE_WAV, media_type="audio/wav")
