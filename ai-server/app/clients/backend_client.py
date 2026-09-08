"""Talks to the real Spring backend over HTTP (BACKEND_MODE=http).

Same surface as MockBackend so main.py can swap one for the other.

Two failure policies, on purpose:

* **Essential reads/writes** (`get_briefing`, `get_counterparties`, `create_summary`) raise
  `BackendUnavailable`. They must not silently fall back to `MockBackend`: the examples describe a
  different user with different transactions, so serving them while the real backend is down would
  put wrong money on screen and read it out loud. An error the operator can see beats a demo that
  lies. The deliberate fallback is `BACKEND_MODE=mock`, chosen by a human.
* **Side effects** (`mark_heard`, `create_mute_rule`, `create_dialog_log`) and `get_classification`
  never raise. Losing a "heard" flag or a log line must not end a conversation mid-turn, and
  `get_classification` already has a caller-side default (`... or cls` in state_machine).
"""
from __future__ import annotations

import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class BackendUnavailable(RuntimeError):
    """The Spring backend could not answer a call the conversation cannot continue without."""


class BackendClient:
    def __init__(self, settings: Settings, timeout: float = 5.0) -> None:
        self._base = settings.backend_base_url.rstrip("/")
        self._client = httpx.Client(base_url=self._base, timeout=timeout)

    @property
    def base_url(self) -> str:
        return self._base

    # ------------------------------------------------------------------ plumbing

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise BackendUnavailable(f"{method} {path}: {exc}") from exc
        if response.status_code >= 400:
            raise BackendUnavailable(f"{method} {path}: HTTP {response.status_code} {response.text[:200]}")
        return response

    def _json(self, method: str, path: str, **kwargs):
        response = self._request(method, path, **kwargs)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def _best_effort(self, method: str, path: str, **kwargs) -> dict:
        """Side effects: log and carry on. The conversation matters more than the bookkeeping."""
        try:
            self._request(method, path, **kwargs)
            return {"status": "ok"}
        except BackendUnavailable as exc:
            logger.warning("backend call failed, continuing: %s", exc)
            return {"status": "skipped", "reason": str(exc)}

    # ------------------------------------------------------------------ essential

    def get_briefing(self, user_id: int) -> dict:
        return self._json("GET", f"/api/users/{user_id}/briefing")

    def get_counterparties(self, user_id: int) -> list[dict]:
        return self._json("GET", f"/api/users/{user_id}/counterparties") or []

    def get_transactions(self, user_id: int, limit: int = 10) -> list[dict]:
        """청취 여부와 무관한 최근 거래. 브리핑은 미청취 3건뿐이라 내역 화면에는 쓸 수 없다."""
        return self._json("GET", f"/api/users/{user_id}/transactions", params={"limit": limit}) or []

    def create_summary(self, payload: dict) -> dict:
        return self._json("POST", "/api/summaries", json=payload)

    # ------------------------------------------------------------------ tolerant

    def get_classification(self, transaction_id: int) -> dict | None:
        try:
            return self._json("GET", f"/api/transactions/{transaction_id}/classification")
        except BackendUnavailable as exc:
            logger.warning("classification unavailable for tx %s: %s", transaction_id, exc)
            return None

    def mark_heard(self, notification_id: int) -> None:
        self._best_effort("POST", f"/api/notifications/{notification_id}/heard")

    def create_mute_rule(self, payload: dict) -> dict:
        return self._best_effort("POST", "/api/mute-rules", json=payload)

    def create_dialog_log(self, payload: dict) -> dict:
        return self._best_effort("POST", "/api/dialog-logs", json=payload)

    # ------------------------------------------------------------------ lifecycle

    def ping(self) -> bool:
        """Used by /ai/health to report whether the backend is actually reachable right now."""
        try:
            self._request("GET", "/api/health")
            return True
        except BackendUnavailable:
            return False

    def close(self) -> None:
        self._client.close()
