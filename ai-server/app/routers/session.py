"""POST /ai/session/start — backend briefing/counterparties -> Session + spoken briefing + candidates."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core import templates as T
from app.core.candidates import build_candidates
from app.core.session_store import store
from app.core.state_machine import BUTTONS
from app.services import audio_cache

router = APIRouter()


class SessionStartRequest(BaseModel):
    user_id: int
    notification_id: int | None = None
    mode: str = "layered"


@router.post("/ai/session/start")
def session_start(body: SessionStartRequest, request: Request) -> dict:
    settings = request.app.state.settings
    backend = request.app.state.backend
    tts = request.app.state.tts

    briefing = backend.get_briefing(body.user_id)
    counterparties = backend.get_counterparties(body.user_id)

    session = store.create(body.user_id, mode=body.mode)
    session.briefing = briefing
    session.user_name = briefing.get("user_name", "")
    session.remaining_count = briefing.get("remaining_count", 0)
    session.counterparties = counterparties

    text, items = T.build_briefing(briefing, datetime.now())
    session.briefing_text = text
    session.items = items

    short_labels = {it["transaction_id"]: it["short_label"] for it in items}
    session.candidates = build_candidates(briefing, counterparties, short_labels)
    session.state = "LISTENING"

    for item in briefing.get("items", []):
        notification_id = item.get("notification_id")
        if notification_id is None:
            continue
        try:
            backend.mark_heard(notification_id)
        except Exception:  # noqa: BLE001 - briefing already read out; a logging failure must not break it
            pass

    audio_url, cached = audio_cache.audio_url_for(text, "friendly", settings.tts_model, tts.synthesize)

    silence_ms = settings.senior_silence_ms if body.mode == "layered" else settings.baseline_silence_ms

    return {
        "session_id": session.session_id,
        "state": session.state,
        "tone": "friendly",
        "briefing": {
            "text": text,
            "audio_url": audio_url,
            "items": items,
            "remaining_count": session.remaining_count,
        },
        "ui": {
            "buttons": [dict(b) for b in BUTTONS.get("LISTENING", [])],
            "silence_ms": silence_ms,
        },
    }
