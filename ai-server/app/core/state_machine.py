"""Dialog state machine — transitions exactly as dialog-state-machine.md.

Absolute rules enforced here:
1. ADD_REQUEST is emitted only in `_confirm_answer` when state == CONFIRM and the answer is YES.
2. No money-moving API is ever called (there is none; requests only go into the counter summary).
3. (P1) LLM explanation text is post-validated against facts; numbers not in facts -> template.
4. One question per turn.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.config import Settings
from app.core import templates as T
from app.core.amount_parser import parse_amount
from app.core.candidates import Candidate, Scored, decide, score_candidates
from app.core.intents import YES_NO_STATES, classify as classify_rule, llm_candidate_intents
from app.core.session_store import Session

LISTEN_STATES = {"LISTENING", "OFFER_ADD_QUESTION", "SLOT_RECIPIENT", "SLOT_AMOUNT", "CONFIRM", "ASK_FREE"}
TX_INTENTS = {"ASK_ABOUT_TX", "ASK_WHO", "ASK_AMOUNT", "MUTE_ITEM"}


def _b(id_: str, label: str, kind: str = "secondary") -> dict:
    return {"id": id_, "label": label, "kind": kind}


BUTTONS: dict[str, list[dict]] = {
    "LISTENING": [_b("ASK_MORE", "더 물어보기", "primary"), _b("GO_COUNTER", "창구 갈 일 정리"), _b("STOP", "대화 종료", "danger")],
    "EXPLAIN": [_b("REPEAT", "다시 들려주세요"), _b("GO_COUNTER", "창구 갈 일 정리"), _b("STOP", "대화 종료", "danger")],
    "OFFER_ADD_QUESTION": [_b("YES", "네, 적어주세요", "primary"), _b("NO", "아니요")],
    "SLOT_RECIPIENT": [_b("NO", "아니에요")],
    "ASK_FREE": [_b("NO", "아니요, 괜찮아요")],
    "SLOT_AMOUNT": [_b("NO", "아니에요")],
    "CONFIRM": [_b("YES", "맞아요", "primary"), _b("NO", "아니에요", "danger")],
    "CLARIFY": [_b("REPEAT", "다시 들려주세요"), _b("STOP", "대화 종료", "danger")],
    "SUMMARY": [],
    "DONE": [],
    "END": [],
}


@dataclass
class TurnResult:
    assistant_text: str = ""
    tone: str = "friendly"
    state: str = "LISTENING"
    buttons: list[dict] | None = None
    choices: list[dict] = field(default_factory=list)
    listen: bool | None = None
    actions: list[dict] = field(default_factory=list)
    intent: str | None = None
    intent_confidence: float | None = None
    candidates: list[dict] = field(default_factory=list)
    matched_candidate: str | None = None
    match_score: float | None = None
    decision: str = "NA"
    path: list[str] = field(default_factory=list)
    llm_used: bool = False
    llm_rejected: bool = False
    provider_error: str | None = None


@dataclass
class TurnContext:
    settings: Settings
    backend: Any          # backend client (http or mock)
    llm: Any              # SafeLLM: classify_intent / choose_candidate / explain -> (result, error)


class EmptySummaryError(ValueError):
    """Raised when neither a confirmed request nor a counter question exists."""


# ================================================================ entry ====
def handle_turn(session: Session, ctx: TurnContext, *, text: str | None = None,
                button_id: str | None = None, choice_id: str | None = None) -> TurnResult:
    r = TurnResult()
    if button_id:
        _on_button(session, ctx, button_id.strip().upper(), r)
    elif choice_id:
        _on_choice(session, ctx, choice_id.strip(), r)
    else:
        _on_text(session, ctx, (text or "").strip(), r)
    _finish(session, r)
    return r


def _finish(session: Session, r: TurnResult) -> None:
    if r.buttons is None:
        r.buttons = [dict(b) for b in BUTTONS.get(r.state, [])]
    if r.listen is None:
        r.listen = r.state in LISTEN_STATES
    if r.state != "CLARIFY" and r.state != "SLOT_RECIPIENT":
        session.clarify_intent = None
    session.state = r.state
    session.last_assistant_text = r.assistant_text
    session.last_tone = r.tone
    session.last_choices = list(r.choices)
    session.actions.extend(r.actions)


# ============================================================== inputs ====
def _on_button(session: Session, ctx: TurnContext, b: str, r: TurnResult) -> None:
    r.path = ["button"]
    r.intent = b
    r.intent_confidence = 1.0
    if b == "ASK_MORE":
        r.assistant_text, r.state = T.ask_more(), "LISTENING"
    elif b == "REPEAT":
        _do_repeat(session, r)
    elif b == "STOP":
        _do_stop(session, r)
    elif b == "GO_COUNTER":
        _do_summary(session, ctx, r)
    elif b in ("YES", "NO"):
        if session.state == "ASK_FREE":
            r.assistant_text, r.state = T.question_skipped(), "LISTENING"
        elif session.state in YES_NO_STATES:
            _dispatch_intent(session, ctx, b, None, r)
        else:
            r.intent = "UNKNOWN"
            r.assistant_text, r.state = T.ask_more(), "LISTENING"
    else:
        r.intent = "UNKNOWN"
        r.assistant_text, r.state = T.ask_more(), "LISTENING"


def _on_choice(session: Session, ctx: TurnContext, choice_id: str, r: TurnResult) -> None:
    kind, _, ident = choice_id.partition(":")
    r.path = ["choice"]
    r.matched_candidate, r.match_score, r.decision = choice_id, 1.0, "ACCEPT"
    if kind == "TX" and ident.isdigit():
        item = session.item_by_tx(int(ident))
        if item is None:
            _clarify_intents(session, r)
            return
        intent = session.clarify_intent or "ASK_ABOUT_TX"
        r.intent, r.intent_confidence = intent, 1.0
        _apply_tx_intent(session, ctx, intent, item, None, r)
    elif kind == "CP" and ident.isdigit():
        cp = session.counterparty_by_id(int(ident))
        r.intent, r.intent_confidence = "REQUEST_TRANSFER", 1.0
        if cp is None:
            _slot_recipient_buttons(session, r, T.ask_recipient())
            return
        pending = session.pending_request or {}
        _accept_recipient(session, cp, pending.get("amount"), pending.get("note"), r)
    elif kind == "INTENT":
        r.intent, r.intent_confidence = ident, 1.0
        r.matched_candidate, r.match_score, r.decision = choice_id, None, "NA"
        if ident == "ASK_ABOUT_TX":
            items = session.raw_items()
            if len(items) == 1:
                _apply_tx_intent(session, ctx, "ASK_ABOUT_TX", items[0], None, r)
            else:
                _clarify_tx(session, r, "ASK_ABOUT_TX", T.which_tx())
        else:
            _dispatch_intent(session, ctx, ident, None, r)
    else:
        _clarify_intents(session, r)


def _on_text(session: Session, ctx: TurnContext, text: str, r: TurnResult) -> None:
    if not text:
        r.intent, r.intent_confidence = "UNKNOWN", 0.0
        r.path = ["rule"]
        _clarify_intents(session, r)
        return

    # ASK_FREE: 무엇을 물어볼지 받는 중. "그만/아니요"가 아니면 들은 말을 그대로 담는다.
    if session.state == "ASK_FREE":
        intent, conf, path = classify_rule(text, session.state, session.tx_name_forms())
        r.path = list(path)
        if intent in ("STOP", "NO"):
            r.intent, r.intent_confidence = intent, conf
            r.assistant_text, r.state = T.question_skipped(), "LISTENING"
            return
        r.intent, r.intent_confidence = "ASK_FREE", 1.0
        _ask_free_answer(session, text, r)
        return

    # SLOT_AMOUNT: any utterance is first tried as an amount.
    if session.state == "SLOT_AMOUNT" and parse_amount(text) is not None:
        r.intent, r.intent_confidence, r.path = "AMOUNT", 1.0, ["rule", "amount_parser"]
        _slot_amount_text(session, text, r)
        return

    intent, conf, path = classify_rule(text, session.state, session.tx_name_forms())
    r.path = list(path)
    free_question = False

    if intent == "UNKNOWN":
        # SLOT_RECIPIENT: a bare name/alias is a recipient answer, not an unknown intent.
        if session.state == "SLOT_RECIPIENT":
            r.intent, r.intent_confidence = "REQUEST_TRANSFER", 1.0
            _request_transfer(session, ctx, text, r)
            return
        if session.state == "SLOT_AMOUNT":
            r.intent, r.intent_confidence = "AMOUNT", 0.0
            r.path.append("amount_parser")
            _slot_amount_text(session, text, r)
            return
        (intent, conf), err = ctx.llm.classify_intent(text, llm_candidate_intents(session.state))
        r.llm_used = True
        r.path.append("llm")
        if err:
            r.provider_error = err
        intent = intent if intent in llm_candidate_intents(session.state) else "UNKNOWN"
        if intent == "UNKNOWN" or conf < ctx.settings.intent_min_conf:
            r.intent, r.intent_confidence = "UNKNOWN", round(float(conf), 2)
            _clarify_intents(session, r)
            return
        free_question = intent in TX_INTENTS

    r.intent, r.intent_confidence = intent, round(float(conf), 2)
    _dispatch_intent(session, ctx, intent, text, r, free_question=free_question)


# ============================================================ dispatch ====
def _dispatch_intent(session: Session, ctx: TurnContext, intent: str, text: str | None, r: TurnResult,
                     free_question: bool = False) -> None:
    state = session.state
    if intent == "REPEAT":
        _do_repeat(session, r)
    elif intent == "STOP":
        _do_stop(session, r)
    elif intent == "GO_COUNTER":
        _do_summary(session, ctx, r)
    elif state == "OFFER_ADD_QUESTION" and intent in ("YES", "NO"):
        _offer_answer(session, intent, r)
    elif state == "CONFIRM" and intent in ("YES", "NO"):
        _confirm_answer(session, intent, r)
    elif state == "SLOT_RECIPIENT" and intent in ("YES", "NO"):
        _slot_recipient_answer(session, intent, r)
    elif state == "SLOT_AMOUNT" and intent in ("YES", "NO"):
        if intent == "NO":
            session.pending_request = None
            r.assistant_text, r.state = T.cancelled(), "LISTENING"
        else:
            r.assistant_text, r.state = T.ask_amount(), "SLOT_AMOUNT"
    elif state == "CONFIRM":
        # Something else while confirming: ask again, one question only.
        r.assistant_text, r.tone, r.state = T.confirm_reprompt(session.pending_request or {}), "confirm", "CONFIRM"
    elif state in ("DONE", "END", "SUMMARY") and intent not in TX_INTENTS and intent != "REQUEST_TRANSFER":
        r.assistant_text, r.state = T.after_done(), state
    elif intent in TX_INTENTS:
        _tx_intent(session, ctx, intent, text, r, free_question)
    elif intent == "REQUEST_TRANSFER":
        _request_transfer(session, ctx, text, r)
    elif intent == "ASK_UNSUPPORTED":
        _ask_unsupported(session, text, r)
    else:
        r.intent = "UNKNOWN"
        _clarify_intents(session, r)


def _ask_unsupported(session: Session, text: str | None, r: TurnResult) -> None:
    """앱이 답할 수 없는 은행 질문. 지어내지 않고 창구로 넘긴다.

    "잘 못 들었어요"로 처리하면 안 된다. 인식은 됐고, 우리가 모르는 것뿐이다. 어르신 입장에서
    말은 통했는데 앱이 못 알아들었다고 하면 다시 물어볼 방법이 없어 대화가 막다른 길이 된다.
    확인 불가 거래를 다루는 방식과 같다: 모른다고 밝히고 창구 목록에 담을지 물어본다.
    """
    asked = (text or "").strip()
    if not asked:
        # CLARIFY 선택지로 들어온 경우. 담을 내용이 없으니 무엇을 물어볼지 먼저 듣는다.
        r.assistant_text, r.state = T.ask_free(), "ASK_FREE"
        return
    session.pending_question = {"transaction_id": None, "text": T.counter_question_from(asked)}
    r.assistant_text = T.cannot_answer()
    r.state = "OFFER_ADD_QUESTION"


def _ask_free_answer(session: Session, text: str, r: TurnResult) -> None:
    """ASK_FREE: 들은 말을 그대로 창구 목록에 담는다. 이미 담겠다고 한 상태라 다시 묻지 않는다."""
    q = {"transaction_id": None, "text": T.counter_question_from(text)}
    session.questions.append(q)
    r.actions.append({"type": "ADD_QUESTION", "payload": q})
    r.assistant_text, r.state = T.question_added(), "LISTENING"


# ============================================================= globals ====
def _do_repeat(session: Session, r: TurnResult) -> None:
    r.assistant_text = session.last_assistant_text or session.briefing_text
    r.tone = session.last_tone
    r.state = session.state
    r.choices = list(session.last_choices)


def _do_stop(session: Session, r: TurnResult) -> None:
    r.assistant_text, r.state = T.stop(), "END"
    r.actions.append({"type": "END", "payload": {"session_id": session.session_id}})
    r.listen = False


def _do_summary(session: Session, ctx: TurnContext, r: TurnResult) -> None:
    requests, questions = _summary_content(session)
    if not requests and not questions:
        r.assistant_text, r.state = T.summary_empty(), "LISTENING"
        return

    result = create_summary(session, ctx)
    r.assistant_text, r.tone, r.state = result["spoken_text"], "confirm", "DONE"
    r.actions.append({"type": "OPEN_SUMMARY", "payload": {
        "summary_id": result["summary_id"], "code": result["code"],
        "ticket_no": result["ticket_no"], "branch_name": result["branch_name"]}})
    r.listen = False


def create_summary(session: Session, ctx: TurnContext) -> dict:
    """Shared by GO_COUNTER and POST /ai/session/{id}/summary. Only confirmed requests are sent."""
    requests, questions = _summary_content(session)
    if not requests and not questions:
        raise EmptySummaryError("requests and questions must not both be empty")

    fingerprint = (len(requests), len(questions))
    if session.summary is None or session.summary_fingerprint != fingerprint:
        payload = {
            "user_id": session.user_id,
            "session_id": session.session_id,
            "branch_name": None,
            "requests": requests,
            "questions": questions,
        }
        session.summary = ctx.backend.create_summary(payload)
        session.summary_fingerprint = fingerprint
    s = session.summary
    prep = [it.get("payload", {}) for it in s.get("items", []) if it.get("section") == "PREP"]
    spoken = T.summary_text(prep, s.get("ticket_no"))
    session.state = "DONE"
    return {
        "summary_id": s.get("id"), "code": s.get("code"), "ticket_no": s.get("ticket_no"),
        "branch_name": s.get("branch_name"), "spoken_text": spoken, "tone": "confirm",
    }


def _summary_content(session: Session) -> tuple[list[dict], list[dict]]:
    requests = [dict(q) for q in session.requests if q.get("confirmed_by_user")]
    questions = [dict(q) for q in session.questions]
    return requests, questions


# ======================================================= clarify helpers ====
def _clarify_intents(session: Session, r: TurnResult) -> None:
    r.assistant_text, r.state = T.clarify(), "CLARIFY"
    r.choices = [{"id": c.id, "label": c.label} for c in session.intent_candidates()]
    r.decision = "BUTTON"
    r.listen = False
    session.clarify_intent = None


def _clarify_tx(session: Session, r: TurnResult, intent: str, text: str, scored: list[Scored] | None = None) -> None:
    order = [s.id for s in scored] if scored and any(s.score > 0 for s in scored) else [c.id for c in session.tx_candidates()]
    r.assistant_text, r.state = text, "CLARIFY"
    r.choices = [{"id": cid, "label": session.label_for(cid)} for cid in order[:3]]
    r.listen = False
    session.clarify_intent = intent


def _tx_choices(session: Session) -> list[dict]:
    return [{"id": c.id, "label": c.label} for c in session.tx_candidates()[:3]]


def _cp_choices(session: Session, scored: list[Scored] | None = None) -> list[dict]:
    if scored and any(s.score > 0 for s in scored):
        return [{"id": s.id, "label": s.label} for s in scored[:3]]
    return [{"id": c.id, "label": c.label} for c in session.cp_candidates()[:3]]


# ===================================================== transaction asks ====
def _resolve(session: Session, ctx: TurnContext, text: str | None, cands: list[Candidate], r: TurnResult
             ) -> tuple[str, str | None, float | None, list[Scored]]:
    if not text or not cands:
        return "BUTTON", None, None, []
    scored = score_candidates(text, cands)
    r.candidates = [s.to_dict() for s in scored]
    r.path.append("jamo")
    decision, mid, score = decide(scored, ctx.settings.match_accept, ctx.settings.match_ask, ctx.settings.match_tie_gap)
    if decision == "LLM_TIEBREAK":
        tied = [s for s in scored[:3] if s.score >= ctx.settings.match_accept] or scored[:2]
        chosen, err = ctx.llm.choose_candidate(text, [{"id": s.id, "label": s.label} for s in tied])
        r.llm_used = True
        r.path.append("llm")
        if err:
            r.provider_error = err
        mid = chosen if chosen in {s.id for s in tied} else scored[0].id
    r.decision, r.matched_candidate, r.match_score = decision, mid, (round(score, 2) if score is not None else None)
    return decision, mid, score, scored


def _tx_intent(session: Session, ctx: TurnContext, intent: str, text: str | None, r: TurnResult,
               free_question: bool) -> None:
    decision, mid, _, scored = _resolve(session, ctx, text, session.tx_candidates(), r)
    item = None
    if decision in ("ACCEPT", "LLM_TIEBREAK") and mid:
        item = session.item_by_tx(int(mid.split(":")[1]))
    elif decision == "ASK_AGAIN" and scored:
        _clarify_tx(session, r, intent, T.ask_again(scored[0].label), scored)
        return
    elif intent == "ASK_ABOUT_TX":
        _clarify_tx(session, r, intent, T.clarify(), scored)
        return
    if item is None:
        # ASK_WHO / ASK_AMOUNT / MUTE_ITEM without an explicit target: use the item in context.
        items = session.raw_items()
        fallback = session.item_by_tx(session.last_tx_id) if session.last_tx_id else None
        item = fallback or (items[0] if items else None)
        if item is None:
            _clarify_intents(session, r)
            return
        r.decision, r.matched_candidate, r.match_score = "NA", f"TX:{item['transaction']['id']}", None
        r.path.append("context")
    _apply_tx_intent(session, ctx, intent, item, text if free_question else None, r)


def _apply_tx_intent(session: Session, ctx: TurnContext, intent: str, item: dict, free_question: str | None,
                     r: TurnResult) -> None:
    session.last_tx_id = item["transaction"]["id"]
    if intent == "ASK_WHO":
        r.assistant_text, r.state = T.who(item), "LISTENING"
    elif intent == "ASK_AMOUNT":
        r.assistant_text, r.state = T.amount(item), "LISTENING"
    elif intent == "MUTE_ITEM":
        tx = item["transaction"]
        r.assistant_text, r.state = T.mute(item), "LISTENING"
        r.actions.append({"type": "MUTE", "payload": {"user_id": session.user_id, "transaction_id": tx["id"],
                                                      "counterparty_name": tx.get("counterparty_name")}})
    else:
        _explain(session, ctx, item, free_question, r)


_NUM_RE = re.compile(r"\d[\d,]*")


def _facts_check(text: str, facts: list[str]) -> bool:
    """P1 post-validation (partial): every number in the LLM text must appear in facts.
    TODO(고현준): also check proper nouns (names/institutions) against facts."""
    facts_str = " ".join(facts).replace(",", "")
    return all(n.replace(",", "") in facts_str for n in _NUM_RE.findall(text))


def _explain(session: Session, ctx: TurnContext, item: dict, free_question: str | None, r: TurnResult) -> None:
    tx, cls = item["transaction"], item["classification"]
    if not cls.get("facts"):
        try:
            cls = ctx.backend.get_classification(tx["id"]) or cls
        except Exception:  # noqa: BLE001 - fall back to the embedded classification
            pass
    if cls.get("level") == "UNKNOWN":
        r.assistant_text, r.state = T.explain_unknown(tx.get("counterparty_name", "")), "OFFER_ADD_QUESTION"
        session.pending_question = {"transaction_id": tx["id"], "text": cls.get("counter_hint") or T.default_question(tx)}
        return
    text = T.explain({"transaction": tx, "classification": cls})
    if free_question:
        llm_text, err = ctx.llm.explain(list(cls.get("facts") or []), free_question)
        r.llm_used = True
        r.path.append("llm")
        if err:
            r.provider_error = err
        if llm_text and _facts_check(llm_text, cls.get("facts") or []):
            text = llm_text.strip()
        else:
            r.llm_rejected = True
    r.assistant_text, r.state = text, "LISTENING"


# ==================================================== question offering ====
def _offer_answer(session: Session, intent: str, r: TurnResult) -> None:
    if intent == "YES" and session.pending_question:
        q = dict(session.pending_question)
        session.questions.append(q)
        r.actions.append({"type": "ADD_QUESTION", "payload": q})
        r.assistant_text = T.question_added()
    else:
        r.assistant_text = T.question_skipped()
    session.pending_question = None
    r.state = "LISTENING"


# ===================================================== transfer request ====
def _new_pending(amount: int | None, note: str | None) -> dict:
    return {"type": "TRANSFER", "recipient_counterparty_id": None, "recipient_name": None,
            "recipient_relation": None, "recipient_bank": None, "recipient_account_masked": None,
            "amount": amount, "note": note, "confirmed_by_user": False}


def _slot_recipient_buttons(session: Session, r: TurnResult, text: str, scored: list[Scored] | None = None) -> None:
    r.assistant_text, r.state = text, "SLOT_RECIPIENT"
    r.choices = _cp_choices(session, scored)


def _request_transfer(session: Session, ctx: TurnContext, text: str | None, r: TurnResult) -> None:
    prev = session.pending_request or {}
    amount = parse_amount(text) if text else None
    if amount is None:
        amount = prev.get("amount")
    if text:
        r.path.append("amount_parser")
    decision, mid, _, scored = _resolve(session, ctx, text, session.cp_candidates(), r)
    note = text or prev.get("note")
    if decision in ("ACCEPT", "LLM_TIEBREAK") and mid:
        cp = session.counterparty_by_id(int(mid.split(":")[1]))
        if cp:
            _accept_recipient(session, cp, amount, note, r)
            return
    if decision == "ASK_AGAIN" and mid:
        cp = session.counterparty_by_id(int(mid.split(":")[1]))
        session.pending_recipient = cp
        session.pending_request = _new_pending(amount, note)
        r.assistant_text, r.state = T.ask_again(scored[0].label), "SLOT_RECIPIENT"
        r.buttons = [_b("YES", "맞아요", "primary"), _b("NO", "아니에요")]
        r.choices = _cp_choices(session, scored)
        return
    session.pending_request = _new_pending(amount, note)
    session.pending_recipient = None
    _slot_recipient_buttons(session, r, T.ask_recipient(), scored)


def _accept_recipient(session: Session, cp: dict, amount: int | None, note: str | None, r: TurnResult) -> None:
    session.pending_request = {
        "type": "TRANSFER",
        "recipient_counterparty_id": cp.get("id"),
        "recipient_name": cp.get("name"),
        "recipient_relation": cp.get("relation"),
        "recipient_bank": cp.get("bank_name"),
        "recipient_account_masked": cp.get("account_number_masked"),
        "amount": amount,
        "note": note,
        "confirmed_by_user": False,
    }
    session.pending_recipient = None
    session.recipient_no_count = 0
    session.amount_fail_count = 0
    if amount is None:
        r.assistant_text, r.state = T.ask_amount(), "SLOT_AMOUNT"
    else:
        _go_confirm(session, r)


def _go_confirm(session: Session, r: TurnResult) -> None:
    r.assistant_text = T.confirm(session.pending_request or {})
    r.tone, r.state = "confirm", "CONFIRM"


def _slot_recipient_answer(session: Session, intent: str, r: TurnResult) -> None:
    pending = session.pending_request or {}
    if intent == "YES":
        if session.pending_recipient:
            _accept_recipient(session, session.pending_recipient, pending.get("amount"), pending.get("note"), r)
        else:
            _slot_recipient_buttons(session, r, T.ask_recipient())
        return
    session.recipient_no_count += 1
    session.pending_recipient = None
    if session.recipient_no_count >= 2:
        _slot_recipient_buttons(session, r, T.ask_recipient())
    else:
        r.assistant_text, r.state = T.ask_recipient_retry(), "SLOT_RECIPIENT"


def _slot_amount_text(session: Session, text: str, r: TurnResult) -> None:
    pending = session.pending_request
    if pending is None or not pending.get("recipient_name"):
        r.intent = "REQUEST_TRANSFER"
        _slot_recipient_buttons(session, r, T.ask_recipient())
        return
    amount = parse_amount(text)
    if amount is not None:
        pending["amount"] = amount
        session.amount_fail_count = 0
        _go_confirm(session, r)
        return
    session.amount_fail_count += 1
    if session.amount_fail_count >= 2:
        pending["amount"] = None
        r.assistant_text = T.amount_at_counter() + " " + T.confirm(pending)
        r.tone, r.state = "confirm", "CONFIRM"
    else:
        r.assistant_text, r.state = T.ask_amount_again(), "SLOT_AMOUNT"


def _confirm_answer(session: Session, intent: str, r: TurnResult) -> None:
    # ABSOLUTE RULE 1: the only place ADD_REQUEST is created — state CONFIRM, answer YES.
    assert session.state == "CONFIRM"
    if intent == "YES" and session.pending_request:
        req = dict(session.pending_request)
        req["confirmed_by_user"] = True
        session.requests.append(req)
        session.pending_request = None
        r.actions.append({"type": "ADD_REQUEST", "payload": req})
        r.assistant_text, r.state = T.after_request(), "LISTENING"
        return
    # NO -> start over from the recipient
    session.pending_request = None
    session.pending_recipient = None
    session.recipient_no_count = 0
    _slot_recipient_buttons(session, r, T.confirm_no_restart())
