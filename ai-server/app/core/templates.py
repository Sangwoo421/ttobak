"""Deterministic sentence templates — senior-mode-policy.md section 4. No LLM here."""
from __future__ import annotations

import re
from datetime import datetime

from app.core.candidates import clean_spoken_name
from app.core.korean_number import native_count, ordinal_word, to_korean, to_korean_won
from app.core.relative_time import relative_time


# ------------------------------------------------------------------ josa ----
def _last_hangul(word: str) -> str | None:
    for ch in reversed(word or ""):
        if "가" <= ch <= "힣":
            return ch
    return None


def josa(word: str, with_batchim: str, without_batchim: str) -> str:
    ch = _last_hangul(word)
    if ch is None:
        return without_batchim
    jong = (ord(ch) - 0xAC00) % 28
    if jong == 0:
        return without_batchim
    if with_batchim == "으로" and jong == 8:  # ㄹ 받침 -> 로
        return without_batchim
    return with_batchim


def i_ga(w: str) -> str:
    return josa(w, "이", "가")


def eun_neun(w: str) -> str:
    return josa(w, "은", "는")


def euro(w: str) -> str:
    return josa(w, "으로", "로")


def ieyo(w: str) -> str:
    return josa(w, "이에요", "예요")


def irago(w: str) -> str:
    return josa(w, "이라고", "라고")


# -------------------------------------------------------------- briefing ----
def _kind(cls: dict) -> str:
    cp = cls.get("counterparty") or {}
    return cp.get("kind") or ("UNKNOWN" if cls.get("level") == "UNKNOWN" else "INSTITUTION")


def briefing_clause(tx: dict, cls: dict) -> str:
    sn = cls.get("spoken_name") or tx.get("counterparty_name", "")
    amt = to_korean_won(tx["amount"])
    if tx.get("type") == "IN":
        if _kind(cls) == "PERSON":
            return f"{sn}{i_ga(sn)} {amt} 보내셨어요."
        return f"{sn}에서 {amt} 들어왔어요."
    return f"{sn}{euro(sn)} {amt} 나갔어요."


def short_label(tx: dict, cls: dict) -> str:
    name = tx.get("counterparty_name", "") if cls.get("level") == "UNKNOWN" else cls.get("spoken_name", "")
    return f"{clean_spoken_name(name)} {to_korean_won(tx['amount'])}"


def build_briefing(briefing: dict, now: datetime | None = None) -> tuple[str, list[dict]]:
    """-> (full text, BriefingItemSpoken list)."""
    name = briefing.get("user_name") or "고객"
    items = briefing.get("items") or []
    spoken: list[dict] = []
    for idx, it in enumerate(items, start=1):
        tx, cls = it["transaction"], it["classification"]
        ordinal = it.get("ordinal") or idx
        sentence = f"{ordinal_word(ordinal)}, {relative_time(tx.get('occurred_at', ''), now)}에 {briefing_clause(tx, cls)}"
        spoken.append({
            "ordinal": ordinal,
            "notification_id": it.get("notification_id"),
            "transaction_id": tx["id"],
            "level": cls.get("level"),
            "short_label": short_label(tx, cls),
            "spoken_sentence": sentence,
        })
    if not spoken:
        return f"{name} 님, 새로 들어오고 나간 돈이 없어요. 더 궁금한 게 있으면 말씀하세요.", spoken
    head = f"{name} 님, 들어오고 나간 돈 {native_count(len(spoken))} 가지를 읽어드릴게요."
    return " ".join([head, *(s["spoken_sentence"] for s in spoken), "더 궁금한 게 있으면 말씀하세요."]), spoken


# --------------------------------------------------------------- explain ----
def explain(item: dict) -> str:
    tx, cls = item["transaction"], item["classification"]
    level = cls.get("level")
    sn = cls.get("spoken_name") or tx.get("counterparty_name", "")
    cp = cls.get("counterparty") or {}
    if level == "CONFIRMED":
        rel = cp.get("relation") or "가족"
        if tx.get("type") == "IN":
            return f"{sn}{i_ga(sn)} 보내신 돈이에요. 등록된 {rel} 통장에서 왔어요."
        return f"{sn}에게 보낸 돈이에요. 등록된 {rel} 통장으로 갔어요."
    if level == "PARTIAL":
        cat = cp.get("category") or "돈"
        verb = "나간" if tx.get("type") == "OUT" else "들어온"
        return f"{sn}에서 {verb} {cat}{ieyo(cat)}. 자세한 내역은 제가 볼 수 없어요."
    return explain_unknown(tx.get("counterparty_name", ""))


def explain_unknown(counterparty_name: str) -> str:
    return (f"통장에는 '{counterparty_name}'{irago(counterparty_name)}만 적혀 있어서, "
            f"무슨 돈인지는 제가 알 수 없어요. 창구에서 여쭤볼 목록에 적어둘까요?")


def focused(item: dict, when: str) -> str:
    """내역에서 거래 한 건을 눌렀을 때: 그 건을 읽고, 설명에서 새로 더할 것만 잇는다.

    브리핑 문구가 이미 '누가 얼마'를 말하므로 explain() 을 그대로 붙이면 같은 말을 두 번 한다.
    한 번에 한 가지만 말한다는 정책(senior-mode-policy §1)에도 어긋난다.
    """
    tx, cls = item["transaction"], item["classification"]
    head = f"{when}에 {briefing_clause(tx, cls)}"
    level = cls.get("level")
    cp = cls.get("counterparty") or {}
    if level == "CONFIRMED":
        rel = cp.get("relation") or "가족"
        return f"{head} 등록된 {rel} 통장이에요."
    if level == "PARTIAL":
        return f"{head} 자세한 내역은 제가 볼 수 없어요."
    return f"{head} {explain_unknown(tx.get('counterparty_name', ''))}"


def counter_question_from(asked: str) -> str:
    """창구 목록에 담을 문장. 어르신이 한 말을 그대로 옮긴다.

    주제만 뽑아 "적금에 대해 문의" 처럼 다듬어 봤지만, "대출 받고 싶어"가 "대출 받고에 대해
    문의"가 되는 식으로 계속 어긋났다. 말을 고쳐 쓰는 것 자체가 작은 의미의 지어내기이기도 하다.
    직원에게도 고객이 실제로 한 말이 더 쓸모 있다.
    """
    text = (asked or "").strip()
    return f'"{text}" (고객 말씀 그대로)' if text else "창구에서 여쭤볼 내용"


def ask_free() -> str:
    """무엇을 창구에 물어볼지 직접 받는다. 목록에 빈 문구를 넣으면 직원에게 쓸모가 없다."""
    return "무엇이 궁금하신지 말씀해 주세요. 들은 그대로 창구 목록에 적어드릴게요."


def cannot_answer() -> str:
    """앱이 답할 수 없는 은행 질문. 모른다고 밝히고 창구로 잇는다.

    무엇을 들었는지는 화면의 말풍선이 이미 보여주므로 음성에서 되풀이하지 않는다
    (한 번에 한 가지만 말한다, senior-mode-policy §1).
    """
    return "그건 제가 알려드리기 어려워요. 창구에서 여쭤볼 목록에 적어둘까요?"


def default_question(tx: dict) -> str:
    verb = "출금" if tx.get("type") == "OUT" else "입금"
    return f"'{tx.get('counterparty_name', '')}' {tx['amount']:,}원 {verb}이 무엇인지"


def who(item: dict) -> str:
    tx, cls = item["transaction"], item["classification"]
    sn = cls.get("spoken_name") or tx.get("counterparty_name", "")
    if tx.get("type") == "IN":
        return f"{sn}{i_ga(sn)} 보내신 돈이에요."
    return f"{sn}{euro(sn)} 나간 돈이에요."


def amount(item: dict) -> str:
    tx, cls = item["transaction"], item["classification"]
    sn = cls.get("spoken_name") or tx.get("counterparty_name", "")
    amt = to_korean_won(tx["amount"])
    verb = "들어왔어요" if tx.get("type") == "IN" else "나갔어요"
    return f"{sn} 건은 {amt} {verb}."


def mute(item: dict) -> str:
    tx = item["transaction"]
    name = tx.get("counterparty_name", "")
    return f"네, {name}{eun_neun(name)} 앞으로 읽어드리지 않을게요."


# --------------------------------------------------------------- confirm ----
def confirm(req: dict) -> str:
    rel = req.get("recipient_relation") or ""
    name = req.get("recipient_name") or ""
    who_ = f"{rel} {name}".strip()
    amt = req.get("amount")
    if amt is None:
        return f"확인하겠습니다. 받는 사람, {who_}. 금액은 창구에서 말씀하십니다. 맞습니까?"
    return f"확인하겠습니다. 받는 사람, {who_}. 금액, {to_korean_won(amt)}. 맞습니까?"


def confirm_reprompt(req: dict) -> str:
    return "맞으면 맞아요, 아니면 아니에요라고 말씀해 주세요. " + confirm(req)


def after_request() -> str:
    return "이체는 창구에서 직원이 도와드려요. 요약서에 적어둘게요."


def confirm_no_restart() -> str:
    return "알겠어요. 처음부터 다시 할게요. 누구에게 보내실까요?"


def ask_again(label: str) -> str:
    return f"{label} 말씀이세요?"


def ask_recipient() -> str:
    return "누구에게 보내실까요? 이 중에 있나요?"


def ask_recipient_retry() -> str:
    return "그럼 누구에게 보내실까요?"


def ask_amount() -> str:
    return "얼마를 보내실까요?"


def ask_amount_again() -> str:
    return "금액을 잘 못 들었어요. 이십만 원처럼 말씀해 주세요."


def amount_at_counter() -> str:
    return "금액은 창구에서 말씀하셔도 돼요."


# -------------------------------------------------------- misc responses ----
def clarify() -> str:
    return "잘 못 들었어요. 이 중에 있나요?"


def which_tx() -> str:
    return "어느 것이 궁금하세요? 이 중에서 골라 주세요."


def question_added() -> str:
    return "적어뒀어요. 더 물어보실 것 있으세요?"


def question_skipped() -> str:
    return "네, 알겠어요. 더 물어보실 것 있으세요?"


def ask_more() -> str:
    return "네, 말씀하세요."


def stop() -> str:
    return "네, 다음에 또 불러 주세요."


def cancelled() -> str:
    return "알겠어요. 취소했어요. 더 물어보실 것 있으세요?"


def after_done() -> str:
    return "요약서가 준비됐어요. 창구에서 이 화면을 보여주세요."


def counter_done() -> str:
    return "창구에서 처리됐어요. 수고하셨어요."


# --------------------------------------------------------------- summary ----
def prep_sentence(prep_items: list[dict]) -> str:
    required = [p.get("item", "") for p in prep_items if p.get("required")]
    has_id = any("신분증" in r for r in required)
    has_book = any(("통장" in r or "카드" in r) for r in required)
    if has_id and has_book:
        return "신분증하고 통장을 가져가세요"
    if has_id:
        return "신분증만 가져가세요"
    if required:
        return f"{', '.join(required)}을 가져가세요"
    return "따로 가져갈 것은 없어요"


def summary_text(prep_items: list[dict], ticket_no: int | None) -> str:
    ticket = f"번호표 {to_korean(ticket_no)} 번이에요. " if ticket_no is not None else ""
    return f"창구 갈 준비가 됐어요. {prep_sentence(prep_items)}. {ticket}창구에서 이 화면을 보여주세요."


def summary_empty() -> str:
    return "아직 창구에서 정리할 내용이 없어요. 하려던 일이나 여쭤볼 것을 먼저 말씀해 주세요."
