"""POST /ai/turn — one dialog turn. All judgment (intent/entity/state) lives in app.core.state_machine;
this router only feeds it, turns the assistant text into audio, and records TurnDebug for the debug panel.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.session_store import store
from app.core.state_machine import TurnContext, handle_turn
from app.services import audio_cache

router = APIRouter()


class TurnRequest(BaseModel):
    session_id: str
    text: str | None = None
    button_id: str | None = None
    choice_id: str | None = None


@router.post("/ai/turn")
def turn(body: TurnRequest, request: Request) -> dict:
    session = store.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    if not (body.text or "").strip() and not body.button_id and not body.choice_id:
        raise HTTPException(status_code=400, detail="text, button_id, choice_id 중 하나가 필요합니다")

    settings = request.app.state.settings
    backend = request.app.state.backend
    llm = request.app.state.llm
    tts = request.app.state.tts

    state_before = session.state
    input_kind = "text" if body.text else ("button" if body.button_id else "choice")

    ctx = TurnContext(settings=settings, backend=backend, llm=llm)
    r = handle_turn(session, ctx, text=body.text, button_id=body.button_id, choice_id=body.choice_id)

    audio_url, _cached = audio_cache.audio_url_for(r.assistant_text, r.tone, settings.tts_model, tts.synthesize)

    debug = {
        "turn_no": len(session.turns) + 1,
        "input_kind": input_kind,
        "user_text": body.text,
        "intent": r.intent,
        "intent_confidence": r.intent_confidence,
        "candidates": r.candidates,
        "matched_candidate": r.matched_candidate,
        "match_score": r.match_score,
        "decision": r.decision,
        "path": r.path,
        "llm_used": r.llm_used,
        "llm_rejected": r.llm_rejected,
        "provider_error": r.provider_error,
        "state_before": state_before,
        "state_after": r.state,
    }
    session.turns.append(debug)

    return {
        "assistant_text": r.assistant_text,
        "audio_url": audio_url,
        "tone": r.tone,
        "state": r.state,
        "ui": {
            "buttons": r.buttons,
            "choices": r.choices,
            "listen": r.listen,
        },
        "actions": r.actions,
        "debug": debug,
    }
