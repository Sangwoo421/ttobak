"""1st-pass intent rules. Table and order are exactly dialog-state-machine.md.

Rules are checked top to bottom, first match wins. YES/NO are only recognized in
OFFER_ADD_QUESTION / CONFIRM / SLOT_RECIPIENT / SLOT_AMOUNT (in LISTENING "응" is UNKNOWN).
"""
from __future__ import annotations

import re

YES_NO_STATES = {"OFFER_ADD_QUESTION", "CONFIRM", "SLOT_RECIPIENT", "SLOT_AMOUNT"}

RULES: list[tuple[str, re.Pattern]] = [
    ("REPEAT", re.compile(r"다시|한 ?번 ?더|못 ?들")),
    ("STOP", re.compile(r"그만|됐어|끝|종료")),
    ("GO_COUNTER", re.compile(r"창구|은행 ?가|정리")),
    # 은행 상품·업무 이야기. 앱이 답할 수 없다. "적금 안내해줘", "공과금 자동이체 신청".
    # 이체·금액 규칙보다 먼저 본다. "공과금 자동이체 신청"이 REQUEST_TRANSFER 로 잡혀
    # 이체 슬롯 채우기로 들어가면 안 되기 때문이다.
    # 단 화면에 떠 있는 거래를 가리키면 건너뛴다(classify 참고) - 그건 답할 수 있다.
    ("ASK_UNSUPPORTED", re.compile(
        r"적금|예금|정기|청약|펀드|주식|보험|연금|대출|이자|금리|만기|해지|"
        r"카드|체크카드|신용카드|재발급|분실|정지|한도|"
        r"통장|비밀번호|공인인증|인증서|보안카드|OTP|"
        r"환전|외화|송금한도|공과금|세금|납부|"
        r"증명서|잔액증명|거래내역서|발급|신규|가입|상품"
    )),
    ("REQUEST_TRANSFER", re.compile(r"보내|부쳐|이체|송금|넣어")),
    ("ASK_WHO", re.compile(r"누가|누구")),
    ("ASK_AMOUNT", re.compile(r"얼마")),
    # MUTE 는 ASK_ABOUT_TX 보다 앞에 둔다. "전기세는 매번 안 들어도 돼"처럼 뮤트 문장은 거의 항상
    # 거래 상대명을 부르는데, ASK_ABOUT_TX 의 보조 트리거(상대명 언급)가 먼저 잡아 버리면 뮤트가 영영 안 잡힌다.
    ("MUTE_ITEM", re.compile(r"안 ?들어도|안 ?읽어|읽지 ?마|끄|빼줘")),
    ("ASK_ABOUT_TX", re.compile(r"뭐야|뭐지|무슨|뭔|어디")),
    ("YES", re.compile(r"^(응|어|네|예|맞|그래|좋아|해줘)")),
    ("NO", re.compile(r"^(아니|아냐|틀|안 ?해)")),
]

# ASK_ABOUT_TX alternative trigger: ordinal words / transaction names
ORDINAL_RE = re.compile(r"첫|두 ?번째|둘째|세 ?번째|셋째|[123] ?번")

ALL_INTENTS = ["REPEAT", "STOP", "GO_COUNTER", "REQUEST_TRANSFER", "ASK_WHO", "ASK_AMOUNT",
               "ASK_ABOUT_TX", "MUTE_ITEM", "ASK_UNSUPPORTED", "YES", "NO", "UNKNOWN"]

_WS = re.compile(r"\s+")


def _mentions_tx(text: str, tx_forms: list[str] | None) -> bool:
    if not tx_forms:
        return False
    compact = _WS.sub("", text)
    return any(f and _WS.sub("", f) in compact for f in tx_forms)


def classify(text: str, state: str, tx_forms: list[str] | None = None) -> tuple[str, float, list[str]]:
    """-> (intent, confidence, path). Rule hit = confidence 1.0; miss = ("UNKNOWN", 0.0)."""
    t = (text or "").strip()
    # 화면에 떠 있는 거래를 가리키는 말이면 앱이 답할 수 있다. 상품 규칙보다 우선한다.
    points_at_known_tx = bool(ORDINAL_RE.search(t)) or _mentions_tx(t, tx_forms)
    for name, rx in RULES:
        if name in ("YES", "NO") and state not in YES_NO_STATES:
            continue
        if name == "ASK_UNSUPPORTED" and points_at_known_tx:
            continue
        if rx.search(t):
            return name, 1.0, ["rule"]
        if name == "ASK_ABOUT_TX" and (ORDINAL_RE.search(t) or _mentions_tx(t, tx_forms)):
            return name, 1.0, ["rule"]
    return "UNKNOWN", 0.0, ["rule"]


def llm_candidate_intents(state: str) -> list[str]:
    base = ["ASK_ABOUT_TX", "ASK_WHO", "ASK_AMOUNT", "REQUEST_TRANSFER", "GO_COUNTER", "REPEAT", "STOP",
            "MUTE_ITEM", "ASK_UNSUPPORTED"]
    if state in YES_NO_STATES:
        base += ["YES", "NO"]
    return base + ["UNKNOWN"]
