"""POST /ai/tts — text (+tone) -> cached audio URL. Same text+tone+model reuses the cached file."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services import audio_cache

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    tone: str = "friendly"


@router.post("/ai/tts")
def tts(body: TTSRequest, request: Request) -> dict:
    settings = request.app.state.settings
    tts_provider = request.app.state.tts
    audio_url, cached = audio_cache.audio_url_for(body.text, body.tone, settings.tts_model, tts_provider.synthesize)
    return {"audio_url": audio_url, "cached": cached}
