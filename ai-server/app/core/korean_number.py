"""int -> Korean reading for TTS (Sino-Korean numerals).

300000 -> "삼십만 원", 42000 -> "사만 이천 원", 19000 -> "만 구천 원", 3500 -> "삼천오백 원", 12 -> "십이"
"""
from __future__ import annotations

import re

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
    """화면에 보이는 금액 표기. 삼십만 원 대신 300,000원처럼 숫자로 쓴다
    (한글 수사보다 읽고 스캔하기 쉽다).

    소리로 나가는 문자열에는 이 표기를 그대로 쓰지 않는다: 제미나이 TTS 는 콤마를
    영어식 3자리로 끊어 읽어 7자리 이상 금액을 잘못 읽는다
    (1,234,560원 -> "천이백삼십사만..."). TTS 입력은 spell_amounts_for_tts() 가
    합성 직전에 한글 수사로 바꾼다.

    후보 매칭용 한글 숫자(candidates.py)와도 별개다 - 거기는 어르신이 음성으로
    "삼십만원"이라고 말할 걸 매칭해야 하므로 to_korean() 을 그대로 쓴다."""
    if amount is None:
        return "금액 미정"
    return f"{amount:,}원"


def native_count(n: int) -> str:
    return NATIVE_COUNT.get(n, to_korean(n))


def ordinal_word(n: int) -> str:
    return ORDINAL_WORDS.get(n, f"{to_korean(n)}번째")


_AMOUNT_RE = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+)\s*원")


def spell_amounts_for_tts(text: str) -> str:
    """TTS 입력 전용. 화면 표기(300,000원)를 소리 나는 대로(삼십만 원) 바꾼다.

    제미나이 TTS 는 콤마를 영어식 3자리로 끊어 읽는다. 한국어는 만 단위(4자리)라
    1,234,560원 을 '천이백삼십사만...' 으로 잘못 읽는다. 화면 표기는 그대로 두고
    소리로 나가는 문자열만 여기서 한글 수사로 바꾼다.
    '원' 이 붙은 숫자만 바꾸므로 계좌번호·시각·날짜는 건드리지 않는다.
    """
    return _AMOUNT_RE.sub(
        lambda m: to_korean(int(m.group(1).replace(",", ""))) + " 원", text
    )
