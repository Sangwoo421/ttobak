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
    ("REQUEST_TRANSFER", re.compile(r"보내|부쳐|이체|송금|넣어")),
    ("ASK_WHO", re.compile(r"누가|누구")),
    ("ASK_AMOUNT", re.compile(r"얼마")),
    ("ASK_ABOUT_TX", re.compile(r"뭐야|뭐지|무슨|뭔|어디")),
    ("MUTE_ITEM", re.compile(r"안 ?들어도|끄|빼줘")),
    ("YES", re.compile(r"^(응|어|네|예|맞|그래|좋아|해줘)")),
    ("NO", re.compile(r"^(아니|아냐|틀|안 ?해)")),
]

# ASK_ABOUT_TX alternative trigger: ordinal words / transaction names
ORDINAL_RE = re.compile(r"첫|두 ?번째|둘째|세 ?번째|셋째|[123] ?번")

ALL_INTENTS = ["REPEAT", "STOP", "GO_COUNTER", "REQUEST_TRANSFER", "ASK_WHO", "ASK_AMOUNT",
               "ASK_ABOUT_TX", "MUTE_ITEM", "YES", "NO", "UNKNOWN"]

_WS = re.compile(r"\s+")


def _mentions_tx(text: str, tx_forms: list[str] | None) -> bool:
    if not tx_forms:
        return False
    compact = _WS.sub("", text)
    return any(f and _WS.sub("", f) in compact for f in tx_forms)


def classify(text: str, state: str, tx_forms: list[str] | None = None) -> tuple[str, float, list[str]]:
    """-> (intent, confidence, path). Rule hit = confidence 1.0; miss = ("UNKNOWN", 0.0)."""
    t = (text or "").strip()
    for name, rx in RULES:
        if name in ("YES", "NO") and state not in YES_NO_STATES:
            continue
        if rx.search(t):
            return name, 1.0, ["rule"]
        if name == "ASK_ABOUT_TX" and (ORDINAL_RE.search(t) or _mentions_tx(t, tx_forms)):
            return name, 1.0, ["rule"]
    return "UNKNOWN", 0.0, ["rule"]


def llm_candidate_intents(state: str) -> list[str]:
    base = ["ASK_ABOUT_TX", "ASK_WHO", "ASK_AMOUNT", "REQUEST_TRANSFER", "GO_COUNTER", "REPEAT", "STOP", "MUTE_ITEM"]
    if state in YES_NO_STATES:
        base += ["YES", "NO"]
    return base + ["UNKNOWN"]
