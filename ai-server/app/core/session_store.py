"""In-memory session store. Sessions live only in this process (hackathon scope)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.core.candidates import Candidate


@dataclass
class Session:
    session_id: str
    user_id: int
    mode: str = "layered"  # layered | baseline
    state: str = "BRIEFING"
    user_name: str = ""
    briefing: dict = field(default_factory=dict)          # raw backend BriefingResponse
    items: list[dict] = field(default_factory=list)       # BriefingItemSpoken
    remaining_count: int = 0
    briefing_text: str = ""
    counterparties: list[dict] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    pending_request: dict | None = None                   # transfer request being built
    pending_recipient: dict | None = None                 # ASK_AGAIN candidate awaiting YES
    pending_question: dict | None = None                  # OFFER_ADD_QUESTION payload awaiting YES
    requests: list[dict] = field(default_factory=list)    # confirmed transfer requests
    questions: list[dict] = field(default_factory=list)   # counter questions
    turns: list[dict] = field(default_factory=list)       # TurnDebug per turn
    actions: list[dict] = field(default_factory=list)     # every action ever emitted
    last_assistant_text: str = ""
    last_tone: str = "friendly"
    last_choices: list[dict] = field(default_factory=list)
    last_tx_id: int | None = None
    clarify_intent: str | None = None                     # intent to apply when a TX choice is tapped
    confirm_attempts: int = 0
    recipient_no_count: int = 0
    amount_fail_count: int = 0
    summary: dict | None = None
    summary_fingerprint: tuple | None = None
    created_at: datetime = field(default_factory=datetime.now)

    # ---- helpers ----
    def tx_candidates(self) -> list[Candidate]:
        return [c for c in self.candidates if c.kind == "TX"]

    def cp_candidates(self) -> list[Candidate]:
        return [c for c in self.candidates if c.kind == "CP"]

    def intent_candidates(self) -> list[Candidate]:
        return [c for c in self.candidates if c.kind == "INTENT"]

    def raw_items(self) -> list[dict]:
        return list(self.briefing.get("items") or [])

    def item_by_tx(self, tx_id: int) -> dict | None:
        for it in self.raw_items():
            if it["transaction"]["id"] == tx_id:
                return it
        return None

    def label_for(self, cand_id: str) -> str:
        for c in self.candidates:
            if c.id == cand_id:
                return c.label
        return cand_id

    def counterparty_by_id(self, cp_id: int) -> dict | None:
        for cp in self.counterparties:
            if cp.get("id") == cp_id:
                return cp
        for it in self.raw_items():
            cp = it["classification"].get("counterparty")
            if cp and cp.get("id") == cp_id:
                return cp
        return None

    def tx_name_forms(self) -> list[str]:
        forms: list[str] = []
        for c in self.tx_candidates():
            forms += [f for f in c.surface_forms if len(f) >= 2 and not any(ch.isdigit() for ch in f)
                      and f not in ("첫째", "첫 번째", "첫번째", "하나", "둘째", "두 번째", "두번째", "셋째", "세 번째", "세번째")]
        return forms

    def stt_hints(self) -> list[str]:
        hints: list[str] = []
        for cp in self.counterparties:
            hints.append(cp.get("name", ""))
            hints += list(cp.get("aliases") or [])
        for it in self.raw_items():
            hints.append(it["classification"].get("spoken_name", ""))
            hints.append(it["transaction"].get("counterparty_name", ""))
        seen, out = set(), []
        for h in hints:
            h = (h or "").strip()
            if h and h not in seen:
                seen.add(h)
                out.append(h)
        return out


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, user_id: int, mode: str = "layered") -> Session:
        sid = f"sess_{uuid.uuid4().hex[:10]}"
        s = Session(session_id=sid, user_id=user_id, mode=mode)
        self._sessions[sid] = s
        return s

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def clear(self) -> None:
        self._sessions.clear()


store = SessionStore()
