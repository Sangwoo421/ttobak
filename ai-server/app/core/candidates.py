"""Entity resolution: jamo decomposition + normalized Levenshtein over n-gram windows.

score = max over utterance windows (2..6 syllables) of normalized similarity(jamo(window), jamo(surface_form)).
Decision thresholds come from Settings (MATCH_ACCEPT / MATCH_ASK / MATCH_TIE_GAP).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from rapidfuzz.distance import Levenshtein

from app.core.korean_number import to_korean

_CHO_BASE, _JUNG_BASE, _JONG_BASE = 0x1100, 0x1161, 0x11A7
_KEEP = re.compile(r"[^0-9A-Za-z가-힣ㄱ-ㆎ]")

ORDINAL_FORMS = {
    1: ["첫째", "첫 번째", "첫번째", "하나", "1번", "일번"],
    2: ["둘째", "두 번째", "두번째", "2번"],
    3: ["셋째", "세 번째", "세번째", "3번"],
}
_NAME_PREFIXES = ("주식회사", "(주)", "대한", "한국", "국민")
_NAME_SUFFIXES = ("주식회사", "(주)", "공사", "공단", "은행")

INTENT_CHOICES = [
    ("INTENT:ASK_ABOUT_TX", "방금 읽어준 돈이 뭔지 물어보기", ["뭐야", "무슨 돈", "물어보기"]),
    ("INTENT:REQUEST_TRANSFER", "누구에게 돈 보내기 준비", ["보내기", "이체", "송금"]),
    ("INTENT:GO_COUNTER", "창구 갈 일 정리하기", ["창구", "정리"]),
    # 못 알아들었을 때도 막다른 길을 만들지 않는다. 어떤 이야기든 창구로 가져갈 수 있다.
    ("INTENT:ASK_UNSUPPORTED", "그 밖의 것 창구에서 물어보기", ["다른", "그 밖", "물어보기"]),
]


# ---------------------------------------------------------------- jamo ----
def decompose(text: str) -> str:
    """Hangul syllables -> 초성/중성/종성 code points (U+1100 block). Others pass through lowercased."""
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            idx = code - 0xAC00
            cho, jung, jong = idx // 588, (idx % 588) // 28, idx % 28
            out.append(chr(_CHO_BASE + cho))
            out.append(chr(_JUNG_BASE + jung))
            if jong:
                out.append(chr(_JONG_BASE + jong))
        else:
            out.append(ch.lower())
    return "".join(out)


def normalize(text: str) -> str:
    return _KEEP.sub("", text or "")


def similarity(a: str, b: str) -> float:
    ja, jb = decompose(normalize(a)), decompose(normalize(b))
    if not ja or not jb:
        return 0.0
    return float(Levenshtein.normalized_similarity(ja, jb))


def best_window_score(utterance: str, surface: str, min_n: int = 2, max_n: int = 6) -> float:
    u, s = normalize(utterance), normalize(surface)
    if not u or not s:
        return 0.0
    sj = decompose(s)
    lo = 1 if len(s) == 1 else min_n
    best = 0.0
    for n in range(lo, max_n + 1):
        if n > len(u):
            break
        for i in range(len(u) - n + 1):
            sc = Levenshtein.normalized_similarity(decompose(u[i:i + n]), sj)
            if sc > best:
                best = float(sc)
    if len(u) < lo:
        best = max(best, float(Levenshtein.normalized_similarity(decompose(u), sj)))
    return best


# ---------------------------------------------------------- candidates ----
@dataclass
class Candidate:
    id: str
    kind: str  # TX | CP | INTENT
    label: str
    surface_forms: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict, repr=False)

    def to_public(self) -> dict:
        return {"id": self.id, "kind": self.kind, "label": self.label, "surface_forms": list(self.surface_forms)}


@dataclass
class Scored:
    id: str
    label: str
    score: float

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "score": round(self.score, 2)}


def score_candidates(utterance: str, candidates: list[Candidate]) -> list[Scored]:
    scored = [
        Scored(c.id, c.label, max((best_window_score(utterance, f) for f in c.surface_forms), default=0.0))
        for c in candidates
    ]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def decide(scored: list[Scored], accept: float, ask: float, tie_gap: float) -> tuple[str, str | None, float | None]:
    """-> (decision, matched_id, score). decision in ACCEPT | LLM_TIEBREAK | ASK_AGAIN | BUTTON."""
    if not scored:
        return "BUTTON", None, None
    top = scored[0]
    second = scored[1].score if len(scored) > 1 else 0.0
    if top.score >= accept:
        if top.score - second >= tie_gap:
            return "ACCEPT", top.id, top.score
        return "LLM_TIEBREAK", top.id, top.score
    if top.score >= ask:
        return "ASK_AGAIN", top.id, top.score
    return "BUTTON", None, top.score


# ------------------------------------------------------- surface forms ----
def name_tokens(name: str) -> list[str]:
    """'대한정보통신' -> ['정보통신'], '한국전력공사' -> ['전력공사', '한국전력', '전력'] (+ whitespace tokens)."""
    name = (name or "").strip()
    out: list[str] = []
    for tok in name.split():
        if tok != name and len(tok) >= 2:
            out.append(tok)
    compact = name.replace(" ", "")
    stripped = {compact}
    for p in _NAME_PREFIXES:
        if compact.startswith(p) and len(compact) - len(p) >= 2:
            stripped.add(compact[len(p):])
    for s in _NAME_SUFFIXES:
        for base in list(stripped):
            if base.endswith(s) and len(base) - len(s) >= 2:
                stripped.add(base[:-len(s)])
    for t in stripped:
        if t != compact and len(t) >= 2 and t not in out:
            out.append(t)
    return out


def clean_spoken_name(spoken_name: str) -> str:
    """\"'대한정보통신'이라는 곳\" -> 대한정보통신 ; keeps others as-is."""
    s = (spoken_name or "").strip()
    s = re.sub(r"이라는 곳$", "", s).strip()
    return s.strip("'\"")


def _dedupe(forms: list[str]) -> list[str]:
    seen, out = set(), []
    for f in forms:
        f = (f or "").strip()
        if f and f not in seen:
            seen.add(f)
            out.append(f)
    return out


def tx_candidate(item: dict, short_label: str) -> Candidate:
    tx, cls = item["transaction"], item["classification"]
    cp = cls.get("counterparty") or {}
    forms = list(ORDINAL_FORMS.get(item.get("ordinal", 0), []))
    forms.append(clean_spoken_name(cls.get("spoken_name", "")))
    forms.append(tx.get("counterparty_name", ""))
    forms += name_tokens(tx.get("counterparty_name", ""))
    forms += list(cp.get("aliases") or [])
    forms.append(to_korean(tx["amount"]))  # 금액 표현
    return Candidate(id=f"TX:{tx['id']}", kind="TX", label=short_label, surface_forms=_dedupe(forms),
                     meta={"transaction_id": tx["id"], "ordinal": item.get("ordinal")})


def cp_candidate(cp: dict) -> Candidate:
    label = f"{cp.get('relation')} {cp['name']}".strip() if cp.get("relation") else cp["name"]
    forms = [cp["name"], *(cp.get("aliases") or []), cp.get("relation") or ""]
    return Candidate(id=f"CP:{cp['id']}", kind="CP", label=label, surface_forms=_dedupe(forms),
                     meta={"counterparty_id": cp["id"]})


def intent_candidates() -> list[Candidate]:
    return [Candidate(id=i, kind="INTENT", label=l, surface_forms=list(f)) for i, l, f in INTENT_CHOICES]


def build_candidates(briefing: dict, counterparties: list[dict], short_labels: dict[int, str] | None = None) -> list[Candidate]:
    """TX (briefed transactions) + CP (registered PERSON recipients) + INTENT labels."""
    short_labels = short_labels or {}
    cands: list[Candidate] = []
    for item in briefing.get("items", []):
        tx_id = item["transaction"]["id"]
        cands.append(tx_candidate(item, short_labels.get(tx_id, item["classification"].get("spoken_name", ""))))
    for cp in counterparties:
        if (cp.get("kind") or "PERSON") == "PERSON":
            cands.append(cp_candidate(cp))
    cands += intent_candidates()
    return cands
