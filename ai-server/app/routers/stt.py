"""POST /ai/stt — audio -> text. Audio lives in memory only for the duration of the request;
nothing is ever written to disk, so there is nothing to clean up afterwards.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from app.core.session_store import store

router = APIRouter()


@router.post("/ai/stt")
async def stt(
    request: Request,
    audio: UploadFile,
    session_id: str = Form(...),
    stub_text: str | None = Form(None),
) -> dict:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    hints: list[str] = [] if session.mode == "baseline" else session.stt_hints()
    audio_bytes = await audio.read()

    stt_provider = request.app.state.stt
    start = time.perf_counter()
    try:
        if stub_text is not None:
            text = stt_provider.transcribe(audio_bytes, audio.filename or "audio", hints, stub_text=stub_text)
        else:
            text = stt_provider.transcribe(audio_bytes, audio.filename or "audio", hints)
    except Exception:  # noqa: BLE001 - a dead STT provider must not take the demo down
        text = stub_text or ""
    duration_ms = int((time.perf_counter() - start) * 1000)

    return {
        "text": text,
        "hints_used": hints,
        "duration_ms": duration_ms,
        "provider": request.app.state.provider_names["stt"],
    }
