"""app/core/amount_parser.py — parse_amount(text: str | None) -> int | None.

Korean amount speech -> integer, rule-based, no LLM.
"""
from __future__ import annotations

import pytest

from app.core.amount_parser import parse_amount


@pytest.mark.parametrize(
    "text, expected",
    [
        ("이십만 원", 200_000),
        ("이십만원", 200_000),
        ("삼만", 30_000),
        ("삼만 원", 30_000),
        ("십만원", 100_000),
        ("십만 원", 100_000),
        ("삼십만원인가", 300_000),
        ("사만 이천 원", 42_000),
        ("오천원", 5_000),
        ("만 구천 원", 19_000),
        ("20만원", 200_000),
        ("300000원", 300_000),
        ("300,000원", 300_000),
        ("이십만 원만 보내줘", 200_000),
    ],
)
def test_spoken_amount_to_int(text, expected):
    assert parse_amount(text) == expected


@pytest.mark.parametrize(
    "text",
    [None, "", "그냥 보내줘", "이거 얼마야", "첫 번째 거", "일번", "이거"],
)
def test_returns_none_when_no_amount_present(text):
    assert parse_amount(text) is None


def test_bare_korean_digits_are_not_amounts():
    # "이거", "일번" 처럼 원/단위 없는 맨 한글 숫자는 금액이 아니다
    assert parse_amount("이거 뭐야") is None
    assert parse_amount("이십만") == 200_000        # 단위(만) 를 달고 있으면 금액


def test_bare_arabic_digits_need_length_or_won():
    assert parse_amount("3") is None
    assert parse_amount("300") is None               # 4자리 미만, 원/단위 없음
    assert parse_amount("3000") == 3_000             # 4자리 이상이면 금액
    assert parse_amount("300원") == 300              # 원이 붙으면 짧아도 금액
