"""Korean amount expression -> int. Rule-based, no LLM.

"이십만 원", "20만원", "삼십만", "사만 이천 원", "오천원", "300000원", "삼십만원인가" -> int
Returns None when no amount is present.
"""
from __future__ import annotations

import re

KOR_DIGITS = {"영": 0, "공": 0, "일": 1, "이": 2, "삼": 3, "사": 4, "오": 5, "육": 6, "륙": 6, "칠": 7, "팔": 8, "구": 9}
SMALL_UNITS = {"십": 10, "백": 100, "천": 1000}
BIG_UNITS = {"만": 10_000, "억": 100_000_000}
UNIT_CHARS = "십백천만억"

_CHUNK_RE = re.compile(r"[0-9일이삼사오육륙칠팔구십백천만억]+")


def _value(chunk: str) -> int:
    total = 0
    section = 0
    current = 0
    num_buf = ""
    for ch in chunk:
        if ch.isdigit():
            num_buf += ch
            continue
        if num_buf:
            current = int(num_buf)
            num_buf = ""
        if ch in KOR_DIGITS:
            current = KOR_DIGITS[ch]
        elif ch in SMALL_UNITS:
            section += (current if current else 1) * SMALL_UNITS[ch]
            current = 0
        elif ch in BIG_UNITS:
            section += current
            current = 0
            if section == 0:
                section = 1  # "만 구천" -> 1만
            total += section * BIG_UNITS[ch]
            section = 0
    if num_buf:
        current = int(num_buf)
    return total + section + current


def parse_amount(text: str | None) -> int | None:
    if not text:
        return None
    s = re.sub(r"[\s,]", "", text)
    for m in _CHUNK_RE.finditer(s):
        chunk = m.group()
        followed_by_won = s[m.end(): m.end() + 1] == "원"
        has_unit = any(c in chunk for c in UNIT_CHARS)
        digits_only = chunk.isdigit()
        # Bare Korean digits ("이거", "일번") are not amounts unless followed by 원 or carrying a unit.
        if not (followed_by_won or has_unit or (digits_only and len(chunk) >= 4)):
            continue
        value = _value(chunk)
        if value > 0:
            return value
    return None
