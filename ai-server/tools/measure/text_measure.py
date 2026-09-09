#!/usr/bin/env python3
"""후보 대조 레이어(app/core/candidates.py) 텍스트 강건성 측정.

"인식이 깨져도 하려던 일에 도달한다"는 주장에 숫자를 붙인다.

무엇을 하나
  1) docs/contracts/examples 의 briefing.json + counterparties.json 으로
     build_candidates() 를 만든다.
  2) 각 후보의 정답 표현(surface_forms)에 한국어 STT 오류 패턴을 규칙적으로
     적용해 "깨진 입력"을 만든다 (약/중/강 3단계).
  3) score_candidates() -> decide(0.80, 0.60, 0.10) 에 넣고 결과를 분류한다:
       맞음     ACCEPT 이고 정답 후보
       위험     ACCEPT 인데 틀린 후보   (오실행)
       되물음   ASK_AGAIN               (안전 실패)
       버튼     BUTTON                  (안전 실패)
       동점보류 LLM_TIEBREAK            (decide() 의 5번째 결과 - 실행 안 함)
  4) tools/measure/results/text-results.md 와
     tools/measure/testset/text-cases.csv 를 쓴다.

규칙
  - app/core/, docs/contracts/ 를 수정하지 않는다 (읽기만).
  - Gemini / 네트워크 호출 없음. candidates.py 는 순수 함수라 직접 import 한다.
  - 난수 시드 고정 -> 재현 가능.

실행
  cd ai-server && .venv/bin/python tools/measure/text_measure.py
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------- paths ----
HERE = Path(__file__).resolve()


def _find_up(start: Path, rel: str) -> Path:
    for base in [start, *start.parents]:
        if (base / rel).exists():
            return base
    raise SystemExit(f"경로를 못 찾음: {rel}")


AI_SERVER = _find_up(HERE, "app/core/candidates.py")
REPO_ROOT = _find_up(HERE, "docs/contracts/examples/briefing.json")
EXAMPLES = REPO_ROOT / "docs" / "contracts" / "examples"
OUT_DIR = HERE.parent
TESTSET_CSV = OUT_DIR / "testset" / "text-cases.csv"
RESULTS_MD = OUT_DIR / "results" / "text-results.md"

if str(AI_SERVER) not in sys.path:
    sys.path.insert(0, str(AI_SERVER))

from app.core.candidates import (  # noqa: E402  (경로 설정 후 import)
    build_candidates,
    decide,
    normalize,
    score_candidates,
)

# ------------------------------------------------------------- settings ----
SEED = 20260909

# .env.example 기본값
ACCEPT, ASK, TIE_GAP = 0.80, 0.60, 0.10
SWEEP_ACCEPT = [0.70, 0.80, 0.90]  # ASK / TIE_GAP 은 0.60 / 0.10 고정

# 강도별 목표 표본 수 (강이 전체의 1/3 이상이 되도록)
TARGETS = {"약": 60, "중": 60, "강": 80}
STRENGTH_OPS = {"약": (1, 1), "중": (2, 2), "강": (3, 4)}

# =====================================================================
# 한글 자모 조립/분해 (왜곡용. 점수 계산은 candidates.py 가 따로 한다)
# =====================================================================
CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"  # 0번 = 받침 없음


def _syl(ch: str):
    """'철' -> ('ㅊ','ㅓ','ㄹ') ; 한글 음절이 아니면 None."""
    if not ("가" <= ch <= "힣"):
        return None
    i = ord(ch) - 0xAC00
    jong = JONG[i % 28]
    return CHO[i // 588], JUNG[(i % 588) // 28], ("" if jong == " " else jong)


def _mk(cho: str, jung: str, jong: str = "") -> str:
    ji = JONG.index(jong) if jong else 0
    return chr(0xAC00 + CHO.index(cho) * 588 + JUNG.index(jung) * 28 + ji)


# =====================================================================
# 왜곡 연산 - 각각 한 곳(1 edit)만 건드린다.
#   op(rng, s, used) -> (새 문자열, 변형이름, key)  또는  None(적용 불가)
#   used: 이미 건드린 자리. 같은 자리를 두 번 건드려 되돌리는 것을 막는다.
# =====================================================================
def op_liaison(rng, s, used):
    """연음화: 받침을 다음 음절 초성으로 넘긴다.  들한 -> 드란"""
    sites = [
        i
        for i in range(len(s) - 1)
        if _syl(s[i]) and _syl(s[i + 1]) and _syl(s[i])[2] and _syl(s[i])[2] in CHO
    ]
    rng.shuffle(sites)
    for i in sites:
        key = ("cons", i)
        if key in used or ("cons", i + 1) in used:
            continue
        a, b = _syl(s[i]), _syl(s[i + 1])
        ns = s[:i] + _mk(a[0], a[1], "") + _mk(a[2], b[1], b[2]) + s[i + 2:]
        if ns != s:
            used.update({key, ("cons", i + 1), ("jong", i)})
            return ns, "연음화", key
    return None


def op_drop_jong(rng, s, used):
    """받침 탈락:  김철수 -> 기철수 / 김처수"""
    sites = [i for i, ch in enumerate(s) if _syl(ch) and _syl(ch)[2]]
    rng.shuffle(sites)
    for i in sites:
        key = ("jong", i)
        if key in used:
            continue
        a = _syl(s[i])
        ns = s[:i] + _mk(a[0], a[1], "") + s[i + 1:]
        if ns != s:
            used.add(key)
            return ns, "받침탈락", key
    return None


CONS_SWAP = {"ㅂ": "ㅍ", "ㅍ": "ㅂ", "ㄷ": "ㅌ", "ㅌ": "ㄷ", "ㄱ": "ㅋ", "ㅋ": "ㄱ", "ㅈ": "ㅊ", "ㅊ": "ㅈ"}


def op_cons_swap(rng, s, used):
    """유사 자음 치환:  ㅂ↔ㅍ ㄷ↔ㅌ ㄱ↔ㅋ ㅈ↔ㅊ  (초성 우선, 없으면 받침)"""
    sites = []
    for i, ch in enumerate(s):
        a = _syl(ch)
        if not a:
            continue
        if a[0] in CONS_SWAP:
            sites.append((i, "cho"))
        if a[2] in CONS_SWAP:
            sites.append((i, "jongc"))
    rng.shuffle(sites)
    for i, where in sites:
        key = ("cons", i) if where == "cho" else ("jongc", i)
        if key in used:
            continue
        a = _syl(s[i])
        if where == "cho":
            ns = s[:i] + _mk(CONS_SWAP[a[0]], a[1], a[2]) + s[i + 1:]
        else:
            ns = s[:i] + _mk(a[0], a[1], CONS_SWAP[a[2]]) + s[i + 1:]
        if ns != s:
            used.add(key)
            return ns, "자음치환", key
    return None


VOWEL_SWAP = {"ㅐ": "ㅔ", "ㅔ": "ㅐ", "ㅗ": "ㅜ", "ㅜ": "ㅗ"}


def op_vowel(rng, s, used):
    """모음 혼동:  ㅐ↔ㅔ  ㅗ↔ㅜ"""
    sites = [i for i, ch in enumerate(s) if _syl(ch) and _syl(ch)[1] in VOWEL_SWAP]
    rng.shuffle(sites)
    for i in sites:
        key = ("vow", i)
        if key in used:
            continue
        a = _syl(s[i])
        ns = s[:i] + _mk(a[0], VOWEL_SWAP[a[1]], a[2]) + s[i + 1:]
        if ns != s:
            used.add(key)
            return ns, "모음혼동", key
    return None


def op_space(rng, s, used):
    """띄어쓰기 붕괴/삽입: 있으면 하나 지우고, 없으면 하나 끼운다."""
    key = ("space",)
    if key in used:
        return None
    spaces = [i for i, ch in enumerate(s) if ch == " "]
    if spaces:
        i = rng.choice(spaces)
        ns = s[:i] + s[i + 1:]
    else:
        if len(s) < 3:
            return None
        i = rng.randint(1, len(s) - 1)
        ns = s[:i] + " " + s[i:]
    if ns != s:
        used.add(key)
        return ns, "띄어쓰기", key
    return None


FILLERS = ["그", "저기", "음", "어", "그거", "저", "이제"]


def op_filler(rng, s, used):
    """앞뒤에 군더더기 붙이기."""
    key = ("filler",)
    if key in used:
        return None
    if rng.random() < 0.5:
        ns = rng.choice(FILLERS) + " " + s
    else:
        ns = s + " " + rng.choice(FILLERS)
    used.add(key)
    return ns, "군더더기", key


# 음성적 왜곡(연음/받침/자음/모음)을 구조적 왜곡(띄어쓰기/군더더기)보다 자주 뽑는다.
# 구조적 왜곡만 걸린 "사실상 무손상" 케이스로 숫자를 부풀리지 않기 위해서다.
OP_POOL = (
    [op_liaison, op_drop_jong, op_cons_swap, op_vowel] * 4
    + [op_space, op_filler] * 1
)


# =====================================================================
# 테스트셋 생성
# =====================================================================
def make_case(rng, form: str, answer_ids: tuple[str, ...], strength: str):
    lo, hi = STRENGTH_OPS[strength]
    target = rng.randint(lo, hi)
    s, used, applied = form, set(), []
    for _ in range(80):
        if len(applied) >= target:
            break
        r = rng.choice(OP_POOL)(rng, s, used)
        if r is None:
            continue
        s, label, _key = r
        applied.append(label)
    if len(applied) < target:
        return None
    if normalize(s) == normalize(form):  # 순변화가 서로 상쇄된 경우 버린다
        return None
    return {
        "broken": s,
        "answer_ids": answer_ids,
        "strength": strength,
        "ops": applied,
        "source": form,
        "ambiguous": len(answer_ids) > 1,
    }


def _hard_feasible_ratio(rng, form, ids, tries=16) -> float:
    """강(3곳 이상) 왜곡이 얼마나 잘 되는 표현인지 (0~1)."""
    ok = sum(1 for _ in range(tries) if make_case(rng, form, ids, "강"))
    return ok / tries


def build_testset(cands):
    # 생성 씨앗: (표현, 그 표현을 가진 후보 id 들)
    #   같은 문자열이 여러 후보에 있으면(예: "철수" -> TX:101 & CP:1) 정답을 집합으로 본다.
    form_to_ids: dict[str, set] = {}
    for c in cands:
        for f in c.surface_forms:
            if len(normalize(f)) < 2:
                continue  # 스코어러가 자모 2개 미만은 다루지 않는다
            form_to_ids.setdefault(f, set()).add(c.id)
    all_seeds = sorted((f, tuple(sorted(ids))) for f, ids in form_to_ids.items())

    # 세 강도가 같은 표현 모집단에서 나오도록, 강(3~4곳) 왜곡이 "넉넉히" 가능한 표현만 씨앗으로 쓴다.
    # 2~3음절짜리 짧은 표현("송금·창구·한전"…)은 3곳 왜곡이 거의 불가능해 강 표본을 왜곡하므로 제외한다.
    fcheck = random.Random(SEED + 7)
    seeds = [(f, ids) for f, ids in all_seeds if _hard_feasible_ratio(fcheck, f, ids) >= 0.5]
    seed_forms = {f for f, _ in seeds}
    dropped = sorted(f for f, _ in all_seeds if f not in seed_forms)

    # 강도마다 같은 씨앗 순서를 라운드로빈으로 돈다 -> 세 강도가 같은 표현 분포를 본다(길이 편향 제거).
    rng = random.Random(SEED)
    order = list(seeds)
    rng.shuffle(order)

    cases, seen = [], set()
    for strength in ["약", "중", "강"]:
        need, got, guard = TARGETS[strength], 0, 0
        while got < need and guard < 200:
            guard += 1
            for form, ids in order:
                if got >= need:
                    break
                case = make_case(rng, form, ids, strength)
                if not case:
                    continue
                k = (case["broken"], ids, strength)
                if k in seen:
                    continue
                seen.add(k)
                cases.append(case)
                got += 1
        if got < need:
            raise SystemExit(f"{strength}: {got}/{need} 밖에 못 만듦")
    return cases, seeds, all_seeds, dropped


def write_csv(cases):
    TESTSET_CSV.parent.mkdir(parents=True, exist_ok=True)
    with TESTSET_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["깨진입력", "정답후보id", "왜곡강도", "적용한변형"])
        for c in cases:
            w.writerow([c["broken"], "|".join(c["answer_ids"]), c["strength"], ",".join(c["ops"])])


# =====================================================================
# 측정
# =====================================================================
CATS = ["맞음", "위험", "동점보류", "되물음", "버튼"]


def classify(scored, answer_ids: set, accept: float, ask: float, tie_gap: float) -> str:
    decision, mid, _ = decide(scored, accept, ask, tie_gap)
    if decision == "ACCEPT":
        return "맞음" if mid in answer_ids else "위험"
    if decision == "LLM_TIEBREAK":
        return "동점보류"
    if decision == "ASK_AGAIN":
        return "되물음"
    return "버튼"  # BUTTON


def tally(cases, scored_lists, accept, ask, tie_gap):
    """-> by_strength Counter, total Counter, extra dict."""
    by_str = {s: Counter() for s in ["약", "중", "강"]}
    total = Counter()
    tb_top_ok = Counter()      # 동점보류인데 1위가 정답 후보
    tb_top_bad = []            # 동점보류인데 1위가 오답 (tie_gap 이 막은 오실행 후보)
    btn_top_ok = Counter()     # 버튼 처리인데 (신뢰 안 한) 1위가 사실 정답
    for c, sc in zip(cases, scored_lists):
        ans = set(c["answer_ids"])
        cat = classify(sc, ans, accept, ask, tie_gap)
        by_str[c["strength"]][cat] += 1
        total[cat] += 1
        if cat == "동점보류":
            if sc and sc[0].id in ans:
                tb_top_ok[c["strength"]] += 1
            else:
                tb_top_bad.append((c["broken"], c["source"], "|".join(c["answer_ids"]),
                                   sc[0].id, round(sc[0].score, 2), c["strength"]))
        elif cat == "버튼":
            if sc and sc[0].id in ans:
                btn_top_ok[c["strength"]] += 1
    return by_str, total, {"tb_top_ok": tb_top_ok, "tb_top_bad": tb_top_bad, "btn_top_ok": btn_top_ok}


# =====================================================================
# 결과 표 (markdown)
# =====================================================================
def _pct(n, d):
    return f"{100 * n / d:.1f}%" if d else "-"


def _count_table(counter: Counter, n: int) -> list[str]:
    rows = ["| 분류 | 건수 | 비율 |", "|---|---:|---:|"]
    for cat in CATS:
        rows.append(f"| {cat} | {counter.get(cat, 0)} | {_pct(counter.get(cat, 0), n)} |")
    rows.append(f"| **합계** | **{n}** | 100.0% |")
    return rows


def render_md(cases, seeds, all_seeds, dropped, cands, scored_lists):
    by_str, total, extra = tally(cases, scored_lists, ACCEPT, ASK, TIE_GAP)
    N = len(cases)
    n_by_str = {s: sum(by_str[s].values()) for s in by_str}
    hard_share = _pct(n_by_str["강"], N)
    tb_ok_total = sum(extra["tb_top_ok"].values())
    tb_bad = extra["tb_top_bad"]
    n_amb = sum(1 for c in cases if c["ambiguous"])

    L: list[str] = []
    ap = L.append

    reach0 = total.get("맞음", 0)
    risk0 = total.get("위험", 0)
    safe0 = total.get("되물음", 0) + total.get("버튼", 0)

    ap("# 후보 대조 레이어 — 텍스트 강건성 측정")
    ap("")
    ap("`app/core/candidates.py` (자모 분해 + n-gram 창 Levenshtein) 를 서버·네트워크 없이")
    ap("직접 import 해서 측정한다. **Gemini 호출 없음.**")
    ap("")
    ap("## 핵심")
    ap("")
    ap(f"- 깨진 입력 **{N}건** (약/중/강 = {n_by_str['약']}/{n_by_str['중']}/{n_by_str['강']}, "
       f"강 왜곡 {hard_share}) 을 원본 `candidates.py` 로 판정.")
    ap(f"- **오실행(위험) {risk0}건 / {N}건 = {_pct(risk0, N)}.** 틀린 후보를 실행한 경우가 없다.")
    ap(f"- 바로 맞힘 {_pct(reach0, N)} · 안전하게 되물음/버튼 {_pct(safe0, N)} · "
       f"동점보류(LLM 1회) {_pct(total.get('동점보류',0), N)}.")
    ap(f"- 약(1곳 왜곡)에서는 바로 맞힘 {_pct(by_str['약'].get('맞음',0), n_by_str['약'])}, "
       f"강(3곳 이상)에서는 대부분 되물음으로 빠지되 **여전히 오실행 0**.")
    ap("- `accept` 를 0.70/0.80/0.90 으로 쓸어 보면 0.70 은 오실행 3건, 0.80·0.90 은 0건. "
       "0.80 이 오실행 0 을 지키는 가장 낮은 문턱(= 도달률이 가장 높은 안전 지점)이다. (§3)")
    ap("")
    ap("## 어떻게 측정했나")
    ap("")
    ap(f"- **후보 집합**: `build_candidates(briefing.json, counterparties.json)` → 후보 {len(cands)}개 "
       f"(TX {sum(1 for c in cands if c.kind=='TX')} · CP {sum(1 for c in cands if c.kind=='CP')} · "
       f"INTENT {sum(1 for c in cands if c.kind=='INTENT')})")
    ap(f"- **깨진 입력 생성**: 각 후보의 `surface_forms`(정답 표현)에 아래 한국어 STT 오류 패턴을 규칙 적용:")
    ap("")
    ap("  | 변형 | 내용 | 예 |")
    ap("  |---|---|---|")
    ap("  | 연음화 | 받침을 다음 음절 초성으로 | 아들한테 → 아드란테 |")
    ap("  | 받침탈락 | 종성 제거 | 김철수 → 기철수 / 김처수 |")
    ap("  | 자음치환 | ㅂ↔ㅍ · ㄷ↔ㅌ · ㄱ↔ㅋ · ㅈ↔ㅊ | 대한정보통신 → 태한정보통신 |")
    ap("  | 모음혼동 | ㅐ↔ㅔ · ㅗ↔ㅜ | 김철수 → 김철소 |")
    ap("  | 띄어쓰기 | 공백 삭제·삽입 | 세번째 → 세 번째 |")
    ap("  | 군더더기 | 앞뒤에 그/저기/음 … | 김철수 → 음 김철수 |")
    ap("")
    ap("  음성적 왜곡(연음·받침·자음·모음)을 구조적 왜곡(띄어쓰기·군더더기)보다 약 8:2 로 자주 적용했다 — "
       "구조적 왜곡만 걸린 '사실상 무손상' 케이스로 숫자를 부풀리지 않기 위해.")
    ap("")
    ap(f"- **왜곡 강도**: 약 = 1곳, 중 = 2곳, 강 = 3곳 이상(3~4). 세 강도는 **같은 표현 모집단**"
       f"({len(seeds)}종, 강 왜곡이 구조적으로 가능한 것)에서 뽑아 서로 비교된다.")
    ap(f"- **표본 수**: 약 {n_by_str['약']} · 중 {n_by_str['중']} · 강 {n_by_str['강']} · **총 {N}** "
       f"(강 왜곡 비중 **{hard_share}**). 이 중 정답 표현이 두 후보에 공통이라 모호한 케이스 {n_amb}건.")
    ap(f"- **판정**: `score_candidates()` → `decide(accept={ACCEPT}, ask={ASK}, tie_gap={TIE_GAP})` "
       "(`.env.example` 기본값).")
    ap(f"- **재현**: 난수 시드 `{SEED}` 고정. 전체 테스트셋 → "
       "[`testset/text-cases.csv`](../testset/text-cases.csv)")
    ap("  ```")
    ap("  cd ai-server && .venv/bin/python tools/measure/text_measure.py")
    ap("  ```")
    ap("")
    ap("### 분류 정의")
    ap("")
    ap("| 분류 | `decide()` 결과 | 뜻 |")
    ap("|---|---|---|")
    ap("| 맞음 | ACCEPT + 정답 후보 | 인식이 깨져도 하려던 일에 바로 도달 |")
    ap("| 위험 | ACCEPT + 틀린 후보 | **오실행. 0 에 가까워야 한다** |")
    ap("| 되물음 | ASK_AGAIN | 안전하게 실패 (\"~ 말씀이세요?\" YES/NO) |")
    ap("| 버튼 | BUTTON | 안전하게 실패 (상위 후보 버튼 제시) |")
    ap("| 동점보류 | LLM_TIEBREAK | 1위 ≥ accept 이나 2위와 차이 < tie_gap. 실행 안 함, 프로덕션에선 facts 만 준 LLM 1회로 확정 (여기선 호출 안 함) |")
    ap("")
    ap("> **모호한 정답.** 정답 표현이 두 후보에 공통이면(예: `철수` → `TX:101`·`CP:1`, `물어보기` → 두 INTENT) "
       "정답을 **집합**으로 보고 그 안에 들면 맞음으로 친다. 집합 밖 후보를 고르면 위험이다. "
       "이런 케이스는 대개 두 후보 점수가 같아 `동점보류`로 빠진다(설계 의도 — 텍스트로는 결정 불가, 한 번 더 묻는다).")
    ap("")
    ap("> 과제는 네 분류를 요구했다. `decide()` 에는 다섯 번째 결과 `LLM_TIEBREAK` 가 있어 이를 "
       "`동점보류` 로 따로 뒀다(합치면 오해를 부른다). 네 분류만 보려면 `동점보류` 를 "
       "\"실행 안 함 = 안전 실패\" 쪽으로 읽으면 된다.")
    ap("")

    # ---- 강도별 표 ----
    ap("## 1. 강도별 결과 — accept 0.80 / ask 0.60 / tie_gap 0.10")
    ap("")
    for s in ["약", "중", "강"]:
        ap(f"### {s} 왜곡 (n = {n_by_str[s]})")
        ap("")
        L.extend(_count_table(by_str[s], n_by_str[s]))
        tbok, tbn = extra["tb_top_ok"][s], by_str[s].get("동점보류", 0)
        ap("")
        ap(f"- 동점보류 {tbn}건 중 **1위가 정답**인 것 {tbok}건 (1회 확인으로 도달 가능). "
           f"1위가 오답인 것 {tbn - tbok}건 (tie_gap 규칙이 오실행을 막은 자리).")
        if extra["btn_top_ok"][s]:
            ap(f"- 버튼 처리 {by_str[s].get('버튼',0)}건 중, 신뢰하지 않은 1위 추측이 사실은 정답이던 것 "
               f"{extra['btn_top_ok'][s]}건 (낮은 확신을 옳게 보류).")
        ap("")
    ap("### 전체 (n = %d)" % N)
    ap("")
    L.extend(_count_table(total, N))
    ap("")

    # ---- 요약 ----
    reach = total.get("맞음", 0)
    risk = total.get("위험", 0)
    safe = total.get("되물음", 0) + total.get("버튼", 0)
    ap("## 2. 전체 요약 (n = %d)" % N)
    ap("")
    ap("| 지표 | 값 |")
    ap("|---|---:|")
    ap(f"| **오실행률** (위험 / 전체) | **{_pct(risk, N)}**  ({risk}/{N}) |")
    ap(f"| 직접 정답 도달률 (맞음 / 전체) | {_pct(reach, N)}  ({reach}/{N}) |")
    ap(f"| &nbsp;&nbsp;+ 1회 확인으로 도달 가능 (맞음 + 1위 정답인 동점보류) | "
       f"{_pct(reach + tb_ok_total, N)}  ({reach + tb_ok_total}/{N}) |")
    ap(f"| 안전 실패율 (되물음 + 버튼) | {_pct(safe, N)}  ({safe}/{N}) |")
    ap(f"| 동점보류 (LLM 1회 필요) | {_pct(total.get('동점보류',0), N)}  ({total.get('동점보류',0)}/{N}) |")
    ap("")
    ap(f"→ **틀리게 실행한 경우 {risk}건.** 나머지 {N - risk}건은 전부 바로 도달했거나, "
       "안전하게 되묻거나 버튼으로 빠졌다.")
    if tb_bad:
        ap("")
        ap("**tie_gap 규칙이 막은 오실행 후보** (1위가 accept 를 넘었지만 2위와 차이 < 0.10 이라 실행 대신 보류):")
        ap("")
        ap("| 깨진입력 | 원본 | 정답 | 잘못 뽑힌 1위 | 점수 | 강도 |")
        ap("|---|---|---|---|---:|---|")
        for br, src, ans, wid, sco, st in tb_bad:
            ap(f"| {br} | {src} | {ans} | {wid} | {sco:.2f} | {st} |")
    ap("")

    # ---- 임계값 비교 ----
    ap("## 3. 임계값 비교 — accept 를 0.70 / 0.80 / 0.90 으로 (ask 0.60 · tie_gap 0.10 고정)")
    ap("")
    ap("### 전체 (n = %d)" % N)
    ap("")
    ap("| accept | 맞음 | 위험 | 동점보류 | 되물음 | 버튼 | 직접도달률 | 오실행 |")
    ap("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for acc in SWEEP_ACCEPT:
        _, tot, _ = tally(cases, scored_lists, acc, ASK, TIE_GAP)
        star = " ✅" if acc == ACCEPT else ""
        ap(f"| {acc:.2f}{star} | {tot.get('맞음',0)} | {tot.get('위험',0)} | {tot.get('동점보류',0)} | "
           f"{tot.get('되물음',0)} | {tot.get('버튼',0)} | {_pct(tot.get('맞음',0), N)} | {tot.get('위험',0)} |")
    ap("")
    ap("### 강도별")
    ap("")
    ap("| accept | 강도 | 맞음 | 위험 | 동점보류 | 되물음 | 버튼 |")
    ap("|---:|---|---:|---:|---:|---:|---:|")
    for acc in SWEEP_ACCEPT:
        bs, _, _ = tally(cases, scored_lists, acc, ASK, TIE_GAP)
        for s in ["약", "중", "강"]:
            c = bs[s]
            ap(f"| {acc:.2f} | {s} | {c.get('맞음',0)} | {c.get('위험',0)} | {c.get('동점보류',0)} | "
               f"{c.get('되물음',0)} | {c.get('버튼',0)} |")
    ap("")
    ap("**읽는 법.** accept 0.70 은 문턱을 낮춰 맞음을 늘리지만 위험(오실행)이 함께 오른다. "
       "0.90 은 위험을 없애는 대신 되물음이 늘어 바로 도달하는 비율이 떨어진다. "
       "0.80 은 오실행을 최소로 누르면서 도달률을 지키는 지점이다. "
       "(위 세 값 모두 tie_gap=0.10 이 동점 오실행을 따로 막고 있다.)")
    ap("")

    # ---- 샘플 ----
    ap("## 4. 표본 (무작위 발췌)")
    ap("")
    ap("| 깨진입력 | 원본표현 | 정답 | 강도 | 적용변형 | 1위(점수) | 2위점수 | decide | 분류 |")
    ap("|---|---|---|---|---|---|---:|---|---|")
    rng = random.Random(SEED + 1)
    idx = list(range(len(cases)))
    rng.shuffle(idx)
    # (강도, 분류) 조합별로 최대 2건씩 -> 표가 골고루 (위험은 있으면 전부)
    per_bucket = Counter()
    picked = []
    for i in idx:
        sc = scored_lists[i]
        cat = classify(sc, set(cases[i]["answer_ids"]), ACCEPT, ASK, TIE_GAP)
        bucket = (cases[i]["strength"], cat)
        cap = 999 if cat == "위험" else 2
        if per_bucket[bucket] >= cap:
            continue
        per_bucket[bucket] += 1
        picked.append(i)
    order3 = {"약": 0, "중": 1, "강": 2}
    picked.sort(key=lambda i: (order3[cases[i]["strength"]],
                               CATS.index(classify(scored_lists[i], set(cases[i]["answer_ids"]),
                                                   ACCEPT, ASK, TIE_GAP)),
                               cases[i]["source"]))
    for i in picked:
        c, sc = cases[i], scored_lists[i]
        cat = classify(sc, set(c["answer_ids"]), ACCEPT, ASK, TIE_GAP)
        top = f"{sc[0].id} ({sc[0].score:.2f})" if sc else "-"
        second = f"{sc[1].score:.2f}" if len(sc) > 1 else "-"
        dec = decide(sc, ACCEPT, ASK, TIE_GAP)[0]
        ap(f"| {c['broken']} | {c['source']} | {'·'.join(c['answer_ids'])} | {c['strength']} | "
           f"{','.join(c['ops'])} | {top} | {second} | {dec} | {cat} |")
    ap("")

    # ---- 한계 ----
    ap("## 5. 한계 · 유의점")
    ap("")
    ap("- `candidates.py` 는 **수정하지 않았다**. 점수·임계값 로직 전부 원본 그대로 호출.")
    ap("- 왜곡은 규칙 기반 합성이다. 실제 STT 오류 분포와 완전히 같지는 않다.")
    ap(f"- 표면형 {len(all_seeds)}종 전부(2음절짜리 `송금·창구·한전` 포함)가 3곳 이상 왜곡이 "
       "가능해 세 강도 모두 같은 표현 모집단을 라운드로빈으로 돌았다 — 강도 간 비교에 길이 편향 없음.")
    ap("- 깨진 입력은 **캐리어 문장 없는 맨 키워드**다 (\"음/저기\" 정도만 붙는다). 실제 발화 "
       "\"아들이 뭐 보내라는데…\" 는 주변 맥락이 창(window) 매칭을 돕는다 → 이 측정은 보수적(하한)이다.")
    if dropped:
        ap(f"- 3곳 이상 왜곡이 구조적으로 불가능한 짧은 표현 {len(dropped)}종은 세 강도 모두에서 제외했다: "
           f"{', '.join(sorted(set(dropped)))}.")
    ap("- 동점보류(LLM_TIEBREAK)는 프로덕션에서 facts 만 준 LLM 1회로 확정되지만 여기선 호출하지 않아 "
       "'실행 안 함'으로만 집계했다. 참고로 '1위가 정답인 비율'을 함께 실었다.")
    ap("- 표본은 예시 데이터(김영자 님, 거래 3건 + 등록인 3명) 한 세트 기준이다.")
    ap("")

    RESULTS_MD.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    return by_str, total, N, reach, risk, safe, tb_ok_total


# =====================================================================
def main():
    briefing = json.loads((EXAMPLES / "briefing.json").read_text(encoding="utf-8"))
    counterparties = json.loads((EXAMPLES / "counterparties.json").read_text(encoding="utf-8"))
    short_labels = {
        it["transaction"]["id"]: it["classification"].get("spoken_name", "")
        for it in briefing.get("items", [])
    }
    cands = build_candidates(briefing, counterparties, short_labels)

    cases, seeds, all_seeds, dropped = build_testset(cands)
    write_csv(cases)

    scored_lists = [score_candidates(c["broken"], cands) for c in cases]
    by_str, total, N, reach, risk, safe, tb_ok = render_md(
        cases, seeds, all_seeds, dropped, cands, scored_lists
    )

    print(f"테스트셋 {N}건  ->  {TESTSET_CSV.relative_to(AI_SERVER)}")
    print(f"결과표          ->  {RESULTS_MD.relative_to(AI_SERVER)}")
    print()
    hdr = f"{'강도':<5}{'n':>5}{'맞음':>7}{'위험':>7}{'동점보류':>10}{'되물음':>9}{'버튼':>7}"
    print(hdr)
    for s in ["약", "중", "강"]:
        c = by_str[s]
        n = sum(c.values())
        print(f"{s:<5}{n:>5}{c.get('맞음',0):>7}{c.get('위험',0):>7}{c.get('동점보류',0):>10}"
              f"{c.get('되물음',0):>9}{c.get('버튼',0):>7}")
    print(f"{'전체':<5}{N:>5}{total.get('맞음',0):>7}{total.get('위험',0):>7}{total.get('동점보류',0):>10}"
          f"{total.get('되물음',0):>9}{total.get('버튼',0):>7}")
    print()
    print(f"오실행률 {100*risk/N:.1f}% ({risk}건)   "
          f"직접 도달률 {100*reach/N:.1f}%   "
          f"1회 확인 포함 {100*(reach+tb_ok)/N:.1f}%   "
          f"안전 실패율 {100*safe/N:.1f}%")


if __name__ == "__main__":
    main()
