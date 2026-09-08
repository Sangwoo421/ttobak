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
    transaction_id: int | None = None  # 어르신 모드 내역에서 한 건만 눌러 들어온 경우
    mode: str = "layered"


def _find(items: list[dict], transaction_id: int) -> dict | None:
    for item in items:
        if item.get("transaction", {}).get("id") == transaction_id:
            return item
    return None


def _focus_one(backend, briefing: dict, user_id: int, transaction_id: int) -> dict | None:
    """내역에서 거래 한 건을 눌러 들어온 경우 그 항목을 찾는다.

    브리핑(미청취 3건)에 없으면 거래 목록에서 찾는다. 이미 들은 거래도 내역에서는 다시 눌러
    들을 수 있어야 하기 때문이다.
    """
    found = _find(briefing.get("items", []), transaction_id)
    if found:
        return found
    try:
        return _find(backend.get_transactions(user_id, limit=50), transaction_id)
    except Exception:  # noqa: BLE001 - 못 찾으면 일반 브리핑으로 떨어진다
        return None


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

    # 거래 한 건만 눌러 들어왔으면 세 건을 다 읽지 않는다. 그 건만 읽고 바로 설명한다.
    focused = _focus_one(backend, briefing, body.user_id, body.transaction_id) if body.transaction_id else None
    heard_items = [focused] if focused else briefing.get("items", [])
    if focused:
        tx, cls = focused["transaction"], focused["classification"]
        when = T.relative_time(tx.get("occurred_at", ""), datetime.now())
        text = T.focused(focused, when)
        # 브리핑에 없던 거래(이미 들은 건)여도 후보로 잡히도록 한 건짜리 브리핑을 합쳐 둔다.
        merged = {**briefing, "items": [focused]}
        _, focused_items = T.build_briefing(merged, datetime.now())
        session.items = focused_items
        session.candidates = build_candidates(
            {"items": list(briefing.get("items", [])) + ([focused] if not _find(briefing.get("items", []), tx["id"]) else [])},
            counterparties,
            {**short_labels, **{s["transaction_id"]: s["short_label"] for s in focused_items}},
        )
        # 확인 불가는 설명으로 끝내지 않고 창구 목록에 담을지 물어본 상태로 둔다.
        if cls.get("level") == "UNKNOWN":
            session.pending_question = {
                "transaction_id": tx["id"],
                "text": cls.get("counter_hint") or T.default_question(tx),
            }
            session.state = "OFFER_ADD_QUESTION"
        session.briefing_text = text

    for item in heard_items:
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
            "items": session.items,
            "remaining_count": session.remaining_count,
        },
        "ui": {
            "buttons": [dict(b) for b in BUTTONS.get(session.state, [])],
            "silence_ms": silence_ms,
            # 읽어준 뒤 바로 듣기 시작한다. 버튼을 눌러야 말할 수 있게 하면 이 사용자층에는
            # 탭이 한 번 더 늘어난다. 시끄러운 곳에서는 프론트 개발자 패널에서 끌 수 있다.
            "listen": True,
        },
    }
