from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/ai/health")
def health(request: Request) -> dict:
    settings = request.app.state.settings
    names = request.app.state.provider_names
    return {
        "status": "ok",
        "stt": names["stt"],
        "tts": names["tts"],
        "llm": names["llm"],
        "backend_mode": settings.backend_mode,
    }
