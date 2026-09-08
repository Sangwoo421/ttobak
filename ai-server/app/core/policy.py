"""senior-mode-policy.md section 2 (생활어 치환) and section 3 (tone -> TTS params)."""
from __future__ import annotations

TONES: dict[str, dict] = {
    "friendly": {
        "speed": 0.85,
        "instructions": "노인에게 말하듯 천천히, 또렷하게, 따뜻하게. 문장 사이에 짧게 쉰다.",
    },
    "confirm": {
        "speed": 0.8,
        "instructions": "은행 창구 직원이 중요한 내용을 확인하듯 또박또박, 단어 사이를 띄어 읽는다.",
    },
}

# 금융 용어 -> 생활어 (templates and LLM system prompt share this)
PLAIN_WORDS: dict[str, str] = {
    "출금": "나간 돈",
    "입금": "들어온 돈",
    "이체": "보내기",
    "송금": "보낸 돈",
    "수취인": "받는 사람",
    "잔액": "남은 돈",
    "적요": "통장에 적힌 이름",
    "자동이체": "매달 자동으로 나가는 돈",
    "거래내역": "들어오고 나간 돈",
    "계좌": "통장",
    "영업점": "은행",
    "본인 확인": "신분증 확인",
}


def tts_params(tone: str) -> tuple[str, float]:
    """tone -> (instructions, speed)."""
    t = TONES.get(tone, TONES["friendly"])
    return t["instructions"], t["speed"]


def normalize_tone(tone: str | None) -> str:
    return tone if tone in TONES else "friendly"


def plain_words_table() -> str:
    return "\n".join(f"- {k} -> {v}" for k, v in PLAIN_WORDS.items())
