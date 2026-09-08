"""app/core/korean_number.py — int -> Korean reading for TTS.

Signatures under test:
  to_korean(n: int) -> str
  to_korean_won(amount: int | None) -> str
  native_count(n: int) -> str
  ordinal_word(n: int) -> str
"""
from __future__ import annotations

import pytest

from app.core.amount_parser import parse_amount
from app.core.korean_number import native_count, ordinal_word, to_korean, to_korean_won


@pytest.mark.parametrize(
    "n, expected",
    [
        (0, "영"),
        (12, "십이"),
        (3_500, "삼천오백"),
        (19_000, "만 구천"),          # 1만 -> "만" (일만 아님)
        (42_000, "사만 이천"),
        (200_000, "이십만"),
        (300_000, "삼십만"),
        (1_234_567, "백이십삼만 사천오백육십칠"),
    ],
)
def test_to_korean_reading(n, expected):
    assert to_korean(n) == expected


def test_to_korean_negative():
    assert to_korean(-100) == "마이너스 " + to_korean(100)


@pytest.mark.parametrize(
    "amount, expected",
    [
        (300_000, "삼십만 원"),
        (42_000, "사만 이천 원"),
        (19_000, "만 구천 원"),
        (None, "금액 미정"),
    ],
)
def test_to_korean_won(amount, expected):
    assert to_korean_won(amount) == expected


def test_native_count():
    assert native_count(1) == "한"
    assert native_count(3) == "세"
    assert native_count(10) == "열"
    assert native_count(11) == to_korean(11)   # 표를 벗어나면 사이노 수사로 폴백


def test_ordinal_word():
    assert ordinal_word(1) == "첫째"
    assert ordinal_word(3) == "셋째"
    assert ordinal_word(6) == "육번째"          # 표를 벗어나면 "{수사}번째"


@pytest.mark.parametrize("amount", [5_000, 19_000, 42_000, 200_000, 300_000])
def test_reader_and_parser_roundtrip(amount):
    # to_korean_won 이 만든 발화를 amount_parser 가 다시 정수로 되돌린다
    assert parse_amount(to_korean_won(amount)) == amount
