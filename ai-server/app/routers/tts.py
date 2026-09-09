"""POST /ai/tts — text (+tone) -> cached audio URL. Same text+tone+model reuses the cached file.

GET /ai/audio-fallback — 0.5 s of silence, straight from memory. audio_cache.audio_url_for points
callers here when synthesis fell back (rate limit) or returned a suspiciously tiny clip, so the app
always has *some* audio_url without a bad result ever landing in the on-disk cache.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
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


@router.get("/ai/audio-tmp/{name}")
def audio_tmp(name: str) -> Response:
    """디스크에 캐시하지 않은 대체 음성(오프라인 TTS). audio_cache.audio_url_for 가 이 경로를 준다."""
    hit = audio_cache.temp_audio(name)
    if hit is None:
        raise HTTPException(status_code=404, detail="temp audio expired")
    audio, ext = hit
    return Response(content=audio, media_type="audio/wav" if ext == "wav" else f"audio/{ext}")
