"""HTTP client for the Spring backend (BACKEND_MODE=http).

Same method surface as app/clients/mock_backend.MockBackend, so app.state.backend can be either
one and nothing downstream cares. Calls the endpoints in docs/contracts/openapi-backend.yaml at
settings.backend_base_url.

Design rules (from the AI-server side, senior demo):
- Short timeouts. A slow or dead backend must never make a dialog turn hang for seconds.
- A failed call never raises into a request handler — the data methods return a safe, empty-shaped
  fallback (mirroring what MockBackend would give for "nothing there").
- Failures are NOT swallowed silently: every one is logged AND recorded on the client
  (`error_count`, `last_error`, `last_error_at`), which GET /ai/health reads and reports.
- No money-moving endpoint exists in the contract and none is called here.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class BackendUnavailable(RuntimeError):
    """Raised only by ping()/probe helpers. The data methods never raise — they degrade."""


_EMPTY_BRIEFING = {"user_name": "", "items": [], "remaining_count": 0}


class HttpBackendClient:
    # Reads sit on the dialog hot path — keep them near-instant.
    _CONNECT_TIMEOUT = 1.5
    _READ_TIMEOUT = 2.5
    _WRITE_TIMEOUT = 4.0
    _PING_TIMEOUT = 1.5

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.backend_base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self._READ_TIMEOUT, connect=self._CONNECT_TIMEOUT),
            headers={"accept": "application/json"},
            follow_redirects=True,
        )
        self.error_count = 0
        self.last_error: str | None = None
        self.last_error_at: float | None = None
        self.last_ok_at: float | None = None

    # ------------------------------------------------------------------ health
    def ping(self) -> dict:
        """GET /api/health with a tight timeout. Raise BackendUnavailable on any failure."""
        try:
            resp = self._http.get("/api/health", timeout=httpx.Timeout(self._PING_TIMEOUT, connect=1.0))
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - normalize every failure mode to one type
            self._mark_error("GET /api/health", exc)
            raise BackendUnavailable(str(exc)) from exc
        self._mark_ok()
        body = resp.json() if resp.content else {}
        return body if isinstance(body, dict) else {"status": str(body)}

    def stats(self) -> dict:
        return {
            "base_url": self.base_url,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_error_at": _iso(self.last_error_at),
            "last_ok_at": _iso(self.last_ok_at),
        }

    # ------------------------------------------------------------------- reads
    def get_briefing(self, user_id: int) -> dict:
        data, ok = self._request("GET", f"/api/users/{user_id}/briefing")
        if ok and isinstance(data, dict):
            return data
        return {"user_id": user_id, **_EMPTY_BRIEFING}

    def get_counterparties(self, user_id: int) -> list[dict]:
        data, ok = self._request("GET", f"/api/users/{user_id}/counterparties")
        return data if ok and isinstance(data, list) else []

    def get_classification(self, transaction_id: int) -> dict | None:
        data, ok = self._request(
            "GET", f"/api/transactions/{transaction_id}/classification", allow_404=True
        )
        return data if ok and isinstance(data, dict) else None

    # ------------------------------------------------------------------ writes
    def create_summary(self, payload: dict) -> dict:
        data, ok = self._request("POST", "/api/summaries", json=payload, timeout=self._WRITE_TIMEOUT)
        return data if ok and isinstance(data, dict) else {}

    def mark_heard(self, notification_id: int) -> None:
        self._request(
            "POST", f"/api/notifications/{notification_id}/heard", timeout=self._WRITE_TIMEOUT
        )

    def create_mute_rule(self, payload: dict) -> dict:
        data, ok = self._request("POST", "/api/mute-rules", json=payload, timeout=self._WRITE_TIMEOUT)
        if ok and isinstance(data, dict):
            return data
        return {"status": "ok" if ok else "error"}

    def create_dialog_log(self, payload: dict) -> dict:
        data, ok = self._request("POST", "/api/dialog-logs", json=payload, timeout=self._WRITE_TIMEOUT)
        if ok and isinstance(data, dict):
            return data
        return {"status": "ok" if ok else "error"}

    # --------------------------------------------------------------- internals
    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        timeout: float | None = None,
        allow_404: bool = False,
    ) -> tuple[Any, bool]:
        """-> (parsed_body_or_None, ok). ok=False means the call failed and was recorded."""
        try:
            resp = self._http.request(method, path, json=json, timeout=timeout or self._READ_TIMEOUT)
            if allow_404 and resp.status_code == 404:
                self._mark_ok()
                return None, True
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - one turn must not die on a backend hiccup
            self._mark_error(f"{method} {path}", exc)
            return None, False
        self._mark_ok()
        if resp.status_code == 204 or not resp.content:
            return None, True
        try:
            return resp.json(), True
        except ValueError:
            logger.warning("backend %s %s returned non-JSON body; treating as empty", method, path)
            return None, True

    def _mark_ok(self) -> None:
        self.last_ok_at = time.time()

    def _mark_error(self, what: str, exc: Exception) -> None:
        self.error_count += 1
        self.last_error = f"{what} -> {type(exc).__name__}: {exc}"
        self.last_error_at = time.time()
        logger.warning("backend call failed (%d total): %s", self.error_count, self.last_error)

    def close(self) -> None:
        self._http.close()


def _iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts))
