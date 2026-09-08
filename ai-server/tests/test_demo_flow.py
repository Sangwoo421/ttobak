"""End-to-end dialog: the 7-turn demo scenario at the bottom of
docs/contracts/dialog-state-machine.md, driven through app.core.state_machine.handle_turn.

Runs fully offline: MockBackend reads docs/contracts/examples/*.json, StubLLMProvider
always returns ("UNKNOWN", 0.3) / no choice / "" — no network, no API keys.

The load-bearing assertion for the presentation Q&A lives in
`test_add_request_never_emitted_before_confirm_yes`:

    "CONFIRM 상태에서 YES 를 받기 전에는 ADD_REQUEST 액션이 절대 생성되지 않는다."
"""
from __future__ import annotations

import json
from datetime import datetime

import pytest

from app.clients.mock_backend import MockBackend
from app.config import DEFAULT_EXAMPLES_DIR
from app.core import templates as T
from app.core.candidates import build_candidates
from app.core.session_store import Session
from app.core.state_machine import TurnContext, handle_turn
from app.providers.factory import SafeLLM
from app.providers.stub_provider import StubLLMProvider


def _load(name: str):
    return json.loads((DEFAULT_EXAMPLES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture
def ctx(settings) -> TurnContext:
    return TurnContext(
        settings=settings,
        backend=MockBackend(settings),
        llm=SafeLLM(StubLLMProvider(), "stub"),
    )


@pytest.fixture
def session() -> Session:
    """A session parked at LISTENING, wired exactly like POST /ai/session/start."""
    briefing = _load("briefing.json")
    counterparties = _load("counterparties.json")

    s = Session(session_id="sess_test", user_id=briefing["user_id"])
    s.briefing = briefing
    s.counterparties = counterparties
    text, items = T.build_briefing(briefing, datetime(2026, 9, 8, 10, 0, 0))
    s.briefing_text = text
    s.items = items
    short_labels = {it["transaction_id"]: it["short_label"] for it in items}
    s.candidates = build_candidates(briefing, counterparties, short_labels)
    s.state = "LISTENING"
    return s


def _add_requests(session: Session) -> list[dict]:
    return [a for a in session.actions if a["type"] == "ADD_REQUEST"]


# ============================================================ full scenario ====
def test_demo_scenario_seven_turns(session, ctx):
    # 턴 1 | "첫 번째 거 그게 뭐야" | ASK_ABOUT_TX / TX:101 | ACCEPT | EXPLAIN -> LISTENING
    r1 = handle_turn(session, ctx, text="첫 번째 거 그게 뭐야")
    assert r1.intent == "ASK_ABOUT_TX"
    assert r1.decision == "ACCEPT"
    assert r1.matched_candidate == "TX:101"
    assert r1.state == "LISTENING"

    # 턴 2 | "세 번째 그 정보통신인가 그건 뭐야" | ASK_ABOUT_TX / TX:103 | ACCEPT, level=UNKNOWN | OFFER_ADD_QUESTION
    r2 = handle_turn(session, ctx, text="세 번째 그 정보통신인가 그건 뭐야")
    assert r2.intent == "ASK_ABOUT_TX"
    assert r2.decision == "ACCEPT"
    assert r2.matched_candidate == "TX:103"
    assert r2.state == "OFFER_ADD_QUESTION"

    # 턴 3 | YES 버튼 | YES | ADD_QUESTION | LISTENING
    r3 = handle_turn(session, ctx, button_id="YES")
    assert r3.intent == "YES"
    assert [a["type"] for a in r3.actions] == ["ADD_QUESTION"]
    assert r3.state == "LISTENING"

    # 턴 4 | "아들이 뭐 보내라는데 이십만 원인가" | REQUEST_TRANSFER / CP:1, amount=200000 | ACCEPT | CONFIRM
    r4 = handle_turn(session, ctx, text="아들이 뭐 보내라는데 이십만 원인가")
    assert r4.intent == "REQUEST_TRANSFER"
    assert r4.decision == "ACCEPT"
    assert r4.matched_candidate == "CP:1"
    assert r4.state == "CONFIRM"
    assert r4.tone == "confirm"
    assert session.pending_request["amount"] == 200_000
    assert session.pending_request["recipient_name"] == "김철수"
    # CONFIRM 에 도달했을 뿐 — 아직 ADD_REQUEST 는 없다
    assert _add_requests(session) == []

    # 턴 5 | "맞아" | YES | ADD_REQUEST | LISTENING
    r5 = handle_turn(session, ctx, text="맞아")
    assert r5.intent == "YES"
    assert [a["type"] for a in r5.actions] == ["ADD_REQUEST"]
    assert r5.actions[0]["payload"]["confirmed_by_user"] is True
    assert r5.actions[0]["payload"]["amount"] == 200_000
    assert r5.state == "LISTENING"

    # 턴 6 | (웅얼) "으음 그 저기" | UNKNOWN (LLM stub conf 0.3) | BUTTON | CLARIFY
    r6 = handle_turn(session, ctx, text="으음 그 저기")
    assert r6.intent == "UNKNOWN"
    assert r6.decision == "BUTTON"
    assert r6.state == "CLARIFY"
    assert len(r6.choices) == 3

    # 턴 7 | choice INTENT:GO_COUNTER | GO_COUNTER | SUMMARY -> DONE
    r7 = handle_turn(session, ctx, choice_id="INTENT:GO_COUNTER")
    assert r7.intent == "GO_COUNTER"
    assert r7.state == "DONE"
    assert any(a["type"] == "OPEN_SUMMARY" for a in r7.actions)

    # 시나리오 전체에서 ADD_REQUEST 는 정확히 한 번 (턴 5) 만
    assert len(_add_requests(session)) == 1


# ================================================= the Q&A-quotable guarantee ====
def test_add_request_never_emitted_before_confirm_yes(session, ctx):
    """CONFIRM 상태에서 YES 를 받기 전에는 ADD_REQUEST 액션이 절대 생성되지 않는다."""

    def run(**kw):
        return handle_turn(session, ctx, **kw)

    # 이체 요청을 CONFIRM 까지 몰고 간다
    r = run(text="아들한테 이십만 원 보내줘")
    assert r.state == "CONFIRM"
    assert session.pending_request is not None
    assert _add_requests(session) == []          # CONFIRM 진입만으로는 안 생김

    # CONFIRM 에서 YES 가 아닌 입력을 여러 개 던진다 — 무엇을 줘도 ADD_REQUEST 는 없다
    run(button_id="REPEAT")
    assert session.state == "CONFIRM"
    assert _add_requests(session) == []

    run(text="다시 말해줘")
    assert _add_requests(session) == []

    r = run(text="아니에요")                      # NO -> 처음부터 (SLOT_RECIPIENT), 요청 폐기
    assert r.state == "SLOT_RECIPIENT"
    assert session.pending_request is None
    assert _add_requests(session) == []

    # 다시 CONFIRM 까지 몰고 가도 여전히 없음
    run(text="아들한테 이십만 원 보내줘")
    assert session.state == "CONFIRM"
    assert _add_requests(session) == []

    # 이제서야 YES — 정확히 여기서만 ADD_REQUEST 가 딱 한 개 생긴다
    r = run(text="네 맞아요")
    assert r.state == "LISTENING"
    assert [a["type"] for a in r.actions] == ["ADD_REQUEST"]
    assert r.actions[0]["payload"]["confirmed_by_user"] is True
    assert len(_add_requests(session)) == 1


def test_confirm_no_restarts_without_any_request(session, ctx):
    handle_turn(session, ctx, text="아들한테 이십만 원 보내줘")
    r = handle_turn(session, ctx, button_id="NO")
    assert r.state == "SLOT_RECIPIENT"
    assert session.pending_request is None
    assert _add_requests(session) == []


def test_go_counter_summary_has_no_confirmed_requests_when_none_confirmed(session, ctx):
    # 이체를 한 번도 확정하지 않고 창구로 가면 요약서 REQUEST 는 비어 있다
    handle_turn(session, ctx, text="첫 번째 거 뭐야")
    r = handle_turn(session, ctx, button_id="GO_COUNTER")
    assert r.state == "DONE"
    assert _add_requests(session) == []
    assert not any(q.get("confirmed_by_user") for q in session.requests)
