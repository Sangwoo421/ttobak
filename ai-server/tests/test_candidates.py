"""app/core/candidates.py — jamo decomposition, window similarity, decide() gating.

Signatures under test:
  decompose(text) -> str
  normalize(text) -> str
  similarity(a, b) -> float
  best_window_score(utterance, surface, min_n=2, max_n=6) -> float
  score_candidates(utterance, candidates: list[Candidate]) -> list[Scored]
  decide(scored, accept, ask, tie_gap) -> (decision, matched_id, score)
  build_candidates(briefing, counterparties, short_labels=None) -> list[Candidate]
"""
from __future__ import annotations

import pytest

from app.core.candidates import (
    Scored,
    best_window_score,
    build_candidates,
    decide,
    decompose,
    normalize,
    score_candidates,
    similarity,
)


# ----------------------------------------------------------------- jamo ----
def test_decompose_splits_syllable_into_jamo():
    assert len(decompose("가")) == 2   # 초성 + 중성
    assert len(decompose("각")) == 3   # 초성 + 중성 + 종성
    assert len(decompose("김철수")) == 3 + 3 + 2


def test_decompose_passes_non_hangul_through_lowercased():
    assert decompose("A1!") == "a1!"
    assert decompose("") == ""


def test_decompose_is_deterministic():
    assert decompose("아들") == decompose("아들")
    assert decompose("김철수") != decompose("김영희")


def test_normalize_strips_punctuation_and_whitespace():
    assert normalize("'대한정보통신'이라는 곳!") == "대한정보통신이라는곳"
    assert normalize(None) == ""


# --------------------------------------------------------- similarity ----
def test_similarity_is_bounded_0_to_1():
    assert similarity("아들", "아들") == 1.0
    assert similarity("", "아들") == 0.0
    assert 0.0 <= similarity("아들", "딸") < 1.0


def test_best_window_score_matches_an_inner_ngram_window():
    # 표면형이 발화의 2~6음절 창과 그대로 겹치면 1.0
    assert best_window_score("아들이 뭐 보내라는데", "아들") == 1.0
    assert best_window_score("첫 번째 거 그게 뭐야", "첫 번째") == 1.0


def test_best_window_score_low_for_unrelated_text():
    assert best_window_score("오늘 날씨 참 좋네요", "한국전력공사") < 0.6


# ------------------------------------------------------- decide() gating ----
def _scored(*pairs: tuple[str, float]) -> list[Scored]:
    return [Scored(id=i, label=i.upper(), score=s) for i, s in pairs]


def test_decide_accept_high_score_clear_gap():
    # s >= 0.80 이고 1·2위 차 >= 0.10 -> ACCEPT
    decision, matched, score = decide(_scored(("a", 0.95), ("b", 0.50)), 0.80, 0.60, 0.10)
    assert (decision, matched) == ("ACCEPT", "a")
    assert score == 0.95


def test_decide_llm_tiebreak_high_score_tight_gap():
    # s >= 0.80 인데 1·2위 차 < 0.10 -> LLM_TIEBREAK
    decision, matched, _ = decide(_scored(("a", 0.95), ("b", 0.90)), 0.80, 0.60, 0.10)
    assert decision == "LLM_TIEBREAK"
    assert matched == "a"


def test_decide_ask_again_middle_band():
    # 0.60 <= s < 0.80 -> ASK_AGAIN (되묻기)
    decision, matched, score = decide(_scored(("a", 0.70), ("b", 0.20)), 0.80, 0.60, 0.10)
    assert (decision, matched, score) == ("ASK_AGAIN", "a", 0.70)


def test_decide_button_below_ask_threshold():
    # s < 0.60 -> BUTTON (CLARIFY 로), matched_id 없음
    decision, matched, score = decide(_scored(("a", 0.40), ("b", 0.10)), 0.80, 0.60, 0.10)
    assert (decision, matched) == ("BUTTON", None)
    assert score == 0.40


def test_decide_button_on_empty_list():
    assert decide([], 0.80, 0.60, 0.10) == ("BUTTON", None, None)


def test_decide_single_candidate_uses_zero_as_runner_up():
    # 후보가 하나뿐이면 2위 점수는 0 으로 봐서 gap 이 커진다
    decision, matched, _ = decide(_scored(("a", 0.85)), 0.80, 0.60, 0.10)
    assert (decision, matched) == ("ACCEPT", "a")


# ---------------------------------------- end-to-end over the real fixture ----
def test_score_and_decide_on_real_briefing(load_example):
    briefing = load_example("briefing.json")
    counterparties = load_example("counterparties.json")
    cands = build_candidates(briefing, counterparties)

    tx = [c for c in cands if c.kind == "TX"]
    assert {c.id for c in tx} == {"TX:101", "TX:102", "TX:103"}

    scored = score_candidates("첫 번째 거 그게 뭐야", tx)
    assert [s.score for s in scored] == sorted((s.score for s in scored), reverse=True)

    decision, matched, _ = decide(scored, 0.80, 0.60, 0.10)
    assert decision == "ACCEPT"
    assert matched == "TX:101"


def test_build_candidates_includes_person_cp_and_intent_labels(load_example):
    briefing = load_example("briefing.json")
    counterparties = load_example("counterparties.json")
    cands = build_candidates(briefing, counterparties)

    kinds = {c.kind for c in cands}
    assert kinds == {"TX", "CP", "INTENT"}

    # 등록 수취인 중 PERSON 만 CP 후보로 (기관 4·5 제외)
    cp_ids = {c.id for c in cands if c.kind == "CP"}
    assert cp_ids == {"CP:1", "CP:2", "CP:3"}

    scored = score_candidates("아들한테 보내줘", [c for c in cands if c.kind == "CP"])
    decision, matched, _ = decide(scored, 0.80, 0.60, 0.10)
    assert (decision, matched) == ("ACCEPT", "CP:1")
