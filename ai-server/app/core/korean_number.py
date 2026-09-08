"""int -> Korean reading for TTS (Sino-Korean numerals).

300000 -> "삼십만 원", 42000 -> "사만 이천 원", 19000 -> "만 구천 원", 3500 -> "삼천오백 원", 12 -> "십이"
"""
from __future__ import annotations

DIGITS = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
SMALL_UNITS = ((3, "천"), (2, "백"), (1, "십"), (0, ""))
BIG_UNITS = ["", "만", "억", "조"]

NATIVE_COUNT = {1: "한", 2: "두", 3: "세", 4: "네", 5: "다섯", 6: "여섯", 7: "일곱", 8: "여덟", 9: "아홉", 10: "열"}
ORDINAL_WORDS = {1: "첫째", 2: "둘째", 3: "셋째", 4: "넷째", 5: "다섯째"}


def _group(n: int) -> str:
    """0..9999 -> e.g. 3500 -> 삼천오백 (no spaces inside a group, 일 omitted before units)."""
    out = []
    for power, unit in SMALL_UNITS:
        d = (n // 10**power) % 10
        if d == 0:
            continue
        if d == 1 and power > 0:
            out.append(unit)
        else:
            out.append(DIGITS[d] + unit)
    return "".join(out)


def to_korean(n: int) -> str:
    if n < 0:
        return "마이너스 " + to_korean(-n)
    if n == 0:
        return "영"
    groups = []
    while n > 0:
        groups.append(n % 10000)
        n //= 10000
    parts = []
    for idx in range(len(groups) - 1, -1, -1):
        g = groups[idx]
        if g == 0:
            continue
        if idx == 1 and g == 1:
            parts.append("만")  # 1만 -> "만" (not 일만)
        else:
            parts.append(_group(g) + BIG_UNITS[idx])
    return " ".join(parts)


def to_korean_won(amount: int | None) -> str:
    if amount is None:
        return "금액 미정"
    return f"{to_korean(amount)} 원"


def native_count(n: int) -> str:
    return NATIVE_COUNT.get(n, to_korean(n))


def ordinal_word(n: int) -> str:
    return ORDINAL_WORDS.get(n, f"{to_korean(n)}번째")
