"""app/core/intents.py — 1st-pass intent classification.

Signatures under test:
  classify(text, state, tx_forms=None) -> (intent, confidence, path)
  llm_candidate_intents(state) -> list[str]
  YES_NO_STATES: set[str]

Rules are checked top to bottom, first match wins. Table/order mirror
docs/contracts/dialog-state-machine.md.
"""
from __future__ import annotations

import pytest

from app.core.intents import YES_NO_STATES, classify, llm_candidate_intents


@pytest.mark.parametrize(
    "text, expected",
    [
        ("다시 들려줘", "REPEAT"),
        ("못 들었어요", "REPEAT"),
        ("한 번 더", "REPEAT"),
        ("그만할래", "STOP"),
        ("이제 됐어", "STOP"),
        ("창구 갈래", "GO_COUNTER"),
        ("은행 가서 할게", "GO_COUNTER"),
        ("정리해줘", "GO_COUNTER"),
        ("아들한테 보내야 해", "REQUEST_TRANSFER"),
        ("계좌로 부쳐줘", "REQUEST_TRANSFER"),
        ("송금할래", "REQUEST_TRANSFER"),
        ("누가 보낸 거야", "ASK_WHO"),
        ("누구한테 간 돈이야", "ASK_WHO"),
        ("얼마야", "ASK_AMOUNT"),
        ("얼마 나갔어", "ASK_AMOUNT"),
        ("이거 뭐야", "ASK_ABOUT_TX"),
        ("무슨 돈이야", "ASK_ABOUT_TX"),
        ("이건 매번 안 들어도 돼", "MUTE_ITEM"),
        ("그건 빼줘", "MUTE_ITEM"),
    ],
)
def test_keyword_rules_in_listening(text, expected):
    intent, conf, path = classify(text, "LISTENING")
    assert intent == expected
    assert conf == 1.0
    assert path == ["rule"]


def test_unknown_when_no_rule_matches():
    assert classify("으음 그 저기", "LISTENING") == ("UNKNOWN", 0.0, ["rule"])
    assert classify("", "LISTENING") == ("UNKNOWN", 0.0, ["rule"])


def test_first_match_wins_in_table_order():
    # REPEAT("다시") 가 GO_COUNTER("정리") 보다 윗줄
    assert classify("다시 정리해줘", "LISTENING")[0] == "REPEAT"
    # STOP("그만") 이 REQUEST_TRANSFER("보내") 보다 윗줄
    assert classify("그만 보내", "LISTENING")[0] == "STOP"


@pytest.mark.parametrize("state", sorted(YES_NO_STATES))
def test_yes_no_recognized_in_yes_no_states(state):
    assert classify("응", state)[0] == "YES"
    assert classify("맞아요", state)[0] == "YES"
    assert classify("아니요", state)[0] == "NO"


def test_yes_no_are_unknown_in_listening():
    # dialog-state-machine.md: LISTENING 에서 "응"은 UNKNOWN
    assert classify("응", "LISTENING")[0] == "UNKNOWN"
    assert classify("아니", "LISTENING")[0] == "UNKNOWN"


@pytest.mark.parametrize("text", ["첫 번째 거", "두번째", "세 번째", "1번", "2 번", "셋째"])
def test_ordinal_words_trigger_ask_about_tx(text):
    assert classify(text, "LISTENING")[0] == "ASK_ABOUT_TX"


def test_transaction_name_mention_triggers_ask_about_tx():
    assert classify("김철수 그건", "LISTENING", ["김철수"])[0] == "ASK_ABOUT_TX"
    # 표면형이 주어지지 않으면 그냥 UNKNOWN
    assert classify("김철수 그건", "LISTENING", None)[0] == "UNKNOWN"


def test_llm_candidate_intents_gates_yes_no_by_state():
    assert "YES" in llm_candidate_intents("CONFIRM")
    assert "NO" in llm_candidate_intents("CONFIRM")
    assert "YES" not in llm_candidate_intents("LISTENING")
    assert llm_candidate_intents("LISTENING")[-1] == "UNKNOWN"
