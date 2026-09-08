"""POST /ai/session/{session_id}/summary — reuses app.core.state_machine.create_summary (same code
path as the GO_COUNTER turn) and adds the spoken audio on top.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.session_store import store
from app.core.state_machine import TurnContext, create_summary
from app.services import audio_cache

router = APIRouter()


@router.post("/ai/session/{session_id}/summary")
def session_summary(session_id: str, request: Request) -> dict:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    settings = request.app.state.settings
    ctx = TurnContext(settings=settings, backend=request.app.state.backend, llm=request.app.state.llm)
    result = create_summary(session, ctx)

    audio_url, _cached = audio_cache.audio_url_for(
        result["spoken_text"], result["tone"], settings.tts_model, request.app.state.tts.synthesize
    )

    return {
        "summary_id": result["summary_id"],
        "code": result["code"],
        "ticket_no": result["ticket_no"],
        "branch_name": result["branch_name"],
        "spoken_text": result["spoken_text"],
        "audio_url": audio_url,
        "tone": result["tone"],
    }
