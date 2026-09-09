"""어르신 모드 내역에서 거래 한 건을 눌러 들어온 경우 (POST /ai/session/start + transaction_id).

오프라인: MockBackend + Stub provider, 네트워크 없음.

핵심은 두 가지다.
  1. 한 건을 눌렀으면 세 건을 다 읽지 않는다. 한 번에 한 가지만 말한다(senior-mode-policy §1).
  2. 확인 불가 거래는 설명으로 끝내지 않고 OFFER_ADD_QUESTION 으로 둔다. 그래야 이어지는
     "네"가 창구 목록 담기로 이어진다. LISTENING 이면 YES 가 의도로 인정되지 않는다.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.clients.mock_backend import MockBackend
from app.config import Settings
from app.core import templates as T


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("BACKEND_MODE", "mock")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    import app.config as config
    config.get_settings.cache_clear()
    import importlib
    import app.main as main
    importlib.reload(main)
    return TestClient(main.app)


def _start(client: TestClient, **body) -> dict:
    response = client.post("/ai/session/start", json={"user_id": 1, **body})
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------- 한 건만 읽는다

def test_full_briefing_reads_all_three():
    """비교 기준: transaction_id 없이 시작하면 세 건을 다 읽는다."""
    briefing = MockBackend(Settings(_env_file=None, backend_mode="mock")).get_briefing(1)
    text, items = T.build_briefing(briefing)
    assert len(items) == 3
    assert "세 가지" in text


def test_focused_start_reads_only_that_transaction(client):
    data = _start(client, transaction_id=101)
    text = data["briefing"]["text"]

    assert len(data["briefing"]["items"]) == 1
    assert data["briefing"]["items"][0]["transaction_id"] == 101
    assert "김철수" in text
    # 나머지 두 건은 입에 담지 않는다
    assert "한국전력" not in text
    assert "대한정보통신" not in text
    assert "세 가지" not in text


def test_focused_confirmed_does_not_repeat_itself(client):
    """브리핑 문구가 이미 '누가 얼마'를 말하므로 설명이 같은 말을 반복하면 안 된다."""
    text = _start(client, transaction_id=101)["briefing"]["text"]
    assert text.count("300,000원") == 1
    assert text.count("김철수") == 1


# ---------------------------------------------------------------- 확인 불가는 물어본 상태로

def test_focused_unknown_offers_the_counter_list(client):
    data = _start(client, transaction_id=103)
    assert data["state"] == "OFFER_ADD_QUESTION"
    assert [b["id"] for b in data["ui"]["buttons"]] == ["YES", "NO"]
    assert "창구에서 여쭤볼 목록에 적어둘까요?" in data["briefing"]["text"]


def test_focused_confirmed_just_listens(client):
    data = _start(client, transaction_id=101)
    assert data["state"] == "LISTENING"
    assert "GO_COUNTER" in [b["id"] for b in data["ui"]["buttons"]]


# ---------------------------------------------------------------- 읽어준 뒤 바로 듣는다

def test_listen_is_on_so_the_user_need_not_tap_twice(client):
    """버튼을 눌러야 말할 수 있으면 이 사용자층에는 탭이 한 번 더 늘어난다."""
    assert _start(client)["ui"]["listen"] is True
    assert _start(client, transaction_id=101)["ui"]["listen"] is True


# ---------------------------------------------------------------- 없는 거래

def test_unknown_transaction_id_falls_back_to_the_normal_briefing(client):
    """내역에 없는 id 로 들어와도 죽지 않고 평소 브리핑을 읽는다."""
    data = _start(client, transaction_id=999999)
    assert data["state"] == "LISTENING"
    assert len(data["briefing"]["items"]) >= 1


# ---------------------------------------------------------------- 조사

@pytest.mark.parametrize(
    "name, expected",
    [("대한정보통신", "'대한정보통신'이라고만"), ("수수료", "'수수료'라고만")],
)
def test_irago_josa_follows_the_final_consonant(name, expected):
    assert expected in T.explain_unknown(name)
