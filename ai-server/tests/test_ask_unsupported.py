"""앱이 답할 수 없는 은행 질문 -> 창구 목록으로.

문제였던 것: "적금 안내해줘"에 "잘 못 들었어요"라고 답했다. 인식은 됐고 우리가 모르는 것뿐인데
인식 실패로 처리하니, 어르신 입장에서는 말이 통했는데도 대화가 막다른 길이 됐다.

지켜야 할 구분:
  - 인식이 깨졌다  -> CLARIFY (후보 버튼)
  - 알아들었지만 답할 수 없다 -> 모른다고 밝히고 창구 목록에 담을지 물어본다
"""
from __future__ import annotations

import pytest

from app.clients.mock_backend import MockBackend
from app.config import DEFAULT_EXAMPLES_DIR, Settings
from app.core import templates as T
from app.core.candidates import build_candidates
from app.core.intents import classify
from app.core.session_store import Session
from app.core.state_machine import TurnContext, handle_turn
from app.providers.factory import SafeLLM
from app.providers.stub_provider import StubLLMProvider


@pytest.fixture
def ctx() -> TurnContext:
    settings = Settings(_env_file=None, backend_mode="mock", llm_provider="stub")
    return TurnContext(settings=settings, backend=MockBackend(settings), llm=SafeLLM(StubLLMProvider(), "stub"))


@pytest.fixture
def session(ctx) -> Session:
    briefing = ctx.backend.get_briefing(1)
    counterparties = ctx.backend.get_counterparties(1)
    s = Session(session_id="t", user_id=1)
    _, items = T.build_briefing(briefing)
    s.briefing, s.items = briefing, items
    s.counterparties = counterparties
    s.candidates = build_candidates(briefing, counterparties,
                                    {i["transaction_id"]: i["short_label"] for i in items})
    s.state = "LISTENING"
    return s


# ---------------------------------------------------------------- 의도 분류

@pytest.mark.parametrize("text", [
    "적금 안내해줘", "예금 금리 얼마나 되나요", "대출 받고 싶어", "카드 재발급 어떻게 해",
    "통장 비밀번호 바꾸고 싶은데", "공과금 자동이체 신청", "잔액증명서 발급", "환전 하려면",
])
def test_banking_topics_are_unsupported_not_unrecognised(text):
    assert classify(text, "LISTENING")[0] == "ASK_UNSUPPORTED"


@pytest.mark.parametrize("text", ["으음 그 저기", "어어 음"])
def test_garbled_speech_is_still_unknown(text):
    """진짜 못 알아들은 것까지 창구로 보내면 음성 레이어가 하는 일이 없어진다."""
    assert classify(text, "LISTENING")[0] == "UNKNOWN"


@pytest.mark.parametrize("text, expected", [
    ("첫 번째 거 그게 뭐야", "ASK_ABOUT_TX"),
    ("아들한테 이십만 원 보내줘", "REQUEST_TRANSFER"),
    ("창구 갈래", "GO_COUNTER"),
    ("그만", "STOP"),
])
def test_existing_intents_still_win(text, expected):
    """새 규칙은 맨 뒤에 있어야 한다. 기존 의도를 가로채면 안 된다."""
    assert classify(text, "LISTENING")[0] == expected


# ---------------------------------------------------------------- 대화 흐름

def test_unsupported_question_offers_the_counter_list(session, ctx):
    r = handle_turn(session, ctx, text="적금 안내해줘")
    assert r.intent == "ASK_UNSUPPORTED"
    assert r.state == "OFFER_ADD_QUESTION"
    assert "창구에서 여쭤볼 목록에 적어둘까요?" in r.assistant_text
    assert "못 들었" not in r.assistant_text  # 인식 실패가 아니다


def test_yes_puts_the_customers_own_words_on_the_list(session, ctx):
    handle_turn(session, ctx, text="적금 안내해줘")
    r = handle_turn(session, ctx, button_id="YES")
    assert [a["type"] for a in r.actions] == ["ADD_QUESTION"]
    assert "적금 안내해줘" in session.questions[0]["text"]


def test_no_leaves_the_list_untouched(session, ctx):
    handle_turn(session, ctx, text="대출 받고 싶어")
    r = handle_turn(session, ctx, button_id="NO")
    assert r.actions == []
    assert session.questions == []


# ---------------------------------------------------------------- 막다른 길 없음

def test_clarify_offers_a_way_to_the_counter(session, ctx):
    """못 알아들었을 때도 창구로 나가는 길이 선택지에 있어야 한다."""
    r = handle_turn(session, ctx, text="으음 그 저기")
    assert r.state == "CLARIFY"
    assert "INTENT:ASK_UNSUPPORTED" in [c["id"] for c in r.choices]


def test_clarify_escape_asks_what_to_write_down(session, ctx):
    """선택지로 들어오면 담을 내용이 없다. 빈 문구를 넣지 말고 직접 받는다."""
    handle_turn(session, ctx, text="으음 그 저기")
    r = handle_turn(session, ctx, choice_id="INTENT:ASK_UNSUPPORTED")
    assert r.state == "ASK_FREE"
    assert session.questions == []  # 아직 담지 않았다

    r = handle_turn(session, ctx, text="손자 등록금 어떻게 보내는지")
    assert [a["type"] for a in r.actions] == ["ADD_QUESTION"]
    assert "손자 등록금 어떻게 보내는지" in session.questions[0]["text"]
    assert r.state == "LISTENING"


def test_ask_free_can_be_cancelled(session, ctx):
    handle_turn(session, ctx, text="으음 그 저기")
    handle_turn(session, ctx, choice_id="INTENT:ASK_UNSUPPORTED")
    r = handle_turn(session, ctx, button_id="NO")
    assert r.state == "LISTENING"
    assert session.questions == []


# ---------------------------------------------------------------- 문구

def test_question_text_is_the_customers_words_verbatim():
    """말을 고쳐 쓰지 않는다. 다듬는 것도 작은 의미의 지어내기이고, 직원에게도 원문이 낫다."""
    assert '"대출 받고 싶어"' in T.counter_question_from("대출 받고 싶어")


def test_cannot_answer_does_not_repeat_what_was_heard():
    """무엇을 들었는지는 화면 말풍선이 보여준다. 음성은 한 번에 한 가지만 말한다."""
    text = T.cannot_answer()
    assert "알려드리기 어려워요" in text
    assert text.count(".") <= 1 or "적어둘까요?" in text
