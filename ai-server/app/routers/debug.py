"""GET /ai/session/{session_id}/debug — session internals for the dev panel and measurement tooling."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.session_store import store

router = APIRouter()


@router.get("/ai/session/{session_id}/debug")
def session_debug(session_id: str) -> dict:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    return {
        "session_id": session.session_id,
        "state": session.state,
        "mode": session.mode,
        "candidates": [c.to_public() for c in session.candidates],
        "pending_request": session.pending_request,
        "requests": session.requests,
        "questions": session.questions,
        "turns": session.turns,
    }
