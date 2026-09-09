"""app/core/korean_number.py :: spell_amounts_for_tts()

TTS 입력 전용. 화면 표기(300,000원)를 소리 나는 대로(삼십만 원) 바꾼다.
제미나이 TTS 가 콤마를 영어식 3자리로 끊어 읽어 7자리 이상 금액을 오독하는 버그를 막는다.

순수 함수만 검증한다 - 네트워크·TTS API 호출 없음.
"""
from __future__ import annotations

import pytest

from app.core.korean_number import spell_amounts_for_tts


@pytest.mark.parametrize(
    "text, expected",
    [
        # 7자리 - 콤마를 영어식으로 끊어 읽던 바로 그 케이스
        ("지금 잔액은 1,234,560원입니다.", "지금 잔액은 백이십삼만 사천오백육십 원입니다."),
        # 6자리 - 우연히 맞게 읽히던 것도 이제 한글 수사로
        ("김철수가 300,000원 보내셨어요.", "김철수가 삼십만 원 보내셨어요."),
        ("한국전력공사에서 42,000원 나갔어요.", "한국전력공사에서 사만 이천 원 나갔어요."),
        ("대한정보통신은 19,000원 나갔어요.", "대한정보통신은 만 구천 원 나갔어요."),
        ("수수료 3,500원 나갔어요.", "수수료 삼천오백 원 나갔어요."),
        # 확인 톤 문장 - 문장부호가 붙어 있어도 '원' 앞의 숫자만 바꾼다
        ("금액, 3,000,000원. 맞습니까?", "금액, 삼백만 원. 맞습니까?"),
    ],
)
def test_amounts_are_spelled_out(text, expected):
    assert spell_amounts_for_tts(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        # 계좌번호 - '원' 이 안 붙으므로 손대지 않는다
        "계좌번호 123-45-****67 확인했어요.",
        # 시각 - 마찬가지
        "어제 15시 12분에 들어온 돈이에요.",
    ],
)
def test_non_amount_digits_are_left_alone(text):
    assert spell_amounts_for_tts(text) == text


def test_multiple_amounts_in_one_sentence():
    """브리핑 한 문장에 금액이 여러 개 들어오는 경우 모두 바꾼다."""
    text = "첫째 300,000원, 둘째 42,000원, 셋째 19,000원 나갔어요."
    expected = "첫째 삼십만 원, 둘째 사만 이천 원, 셋째 만 구천 원 나갔어요."
    assert spell_amounts_for_tts(text) == expected


def test_idempotent():
    """이미 한글 수사로 바뀐 문자열을 다시 넣어도 그대로다 (캐시 경계에서 두 번 불려도 안전)."""
    once = spell_amounts_for_tts("금액, 3,000,000원. 맞습니까?")
    assert spell_amounts_for_tts(once) == once


def test_no_amount_text_unchanged():
    text = "누구에게 보내실까요? 이 중에 있나요?"
    assert spell_amounts_for_tts(text) == text
