"""BackendClient: the two failure policies, and which URLs it actually calls.

Offline — httpx.MockTransport stands in for the Spring backend, no network, no running server.
"""
from __future__ import annotations

import httpx
import pytest

from app.clients.backend_client import BackendClient, BackendUnavailable
from app.config import Settings


def _client(handler) -> BackendClient:
    """A BackendClient whose transport is `handler` instead of a socket."""
    client = BackendClient(Settings(_env_file=None, backend_base_url="http://backend:8080"))
    client._client = httpx.Client(base_url="http://backend:8080", transport=httpx.MockTransport(handler))
    return client


def _ok(payload, status=200):
    return lambda request: httpx.Response(status, json=payload)


def _boom(request):
    raise httpx.ConnectError("connection refused")


def _status(code):
    return lambda request: httpx.Response(code, text="backend said no")


# ---------------------------------------------------------------- URLs

def test_calls_the_paths_the_contract_defines():
    seen = []

    def record(request):
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={})

    c = _client(record)
    c.get_briefing(1)
    c.get_counterparties(1)
    c.get_classification(103)
    c.create_summary({"user_id": 1})
    c.mark_heard(1001)
    c.create_mute_rule({"user_id": 1})
    c.create_dialog_log({"session_id": "s"})

    assert seen == [
        ("GET", "/api/users/1/briefing"),
        ("GET", "/api/users/1/counterparties"),
        ("GET", "/api/transactions/103/classification"),
        ("POST", "/api/summaries"),
        ("POST", "/api/notifications/1001/heard"),
        ("POST", "/api/mute-rules"),
        ("POST", "/api/dialog-logs"),
    ]


def test_briefing_returns_the_payload():
    c = _client(_ok({"user_name": "김영자", "items": []}))
    assert c.get_briefing(1)["user_name"] == "김영자"


# ---------------------------------------------------------------- essential calls raise

@pytest.mark.parametrize("handler", [_boom, _status(500), _status(404)])
def test_essential_reads_raise_rather_than_serve_mock_data(handler):
    """A demo that reads someone else's transactions aloud is worse than one that errors."""
    c = _client(handler)
    with pytest.raises(BackendUnavailable):
        c.get_briefing(1)
    with pytest.raises(BackendUnavailable):
        c.get_counterparties(1)
    with pytest.raises(BackendUnavailable):
        c.create_summary({"user_id": 1})


# ---------------------------------------------------------------- side effects never raise

@pytest.mark.parametrize("handler", [_boom, _status(500)])
def test_side_effects_degrade_quietly(handler):
    """Losing a heard flag or a log line must not end the conversation mid-turn."""
    c = _client(handler)
    assert c.mark_heard(1001) is None
    assert c.create_mute_rule({"user_id": 1})["status"] == "skipped"
    assert c.create_dialog_log({"session_id": "s"})["status"] == "skipped"


@pytest.mark.parametrize("handler", [_boom, _status(404)])
def test_classification_returns_none_so_the_caller_default_applies(handler):
    # state_machine does `ctx.backend.get_classification(...) or cls`
    assert _client(handler).get_classification(103) is None


# ---------------------------------------------------------------- misc

def test_204_becomes_none_not_a_json_error():
    assert _client(lambda r: httpx.Response(204))._json("POST", "/api/notifications/1/heard") is None


def test_counterparties_never_returns_none():
    assert _client(lambda r: httpx.Response(200, text=""))._client is not None
    assert _client(lambda r: httpx.Response(204)).get_counterparties(1) == []


def test_ping_reports_reachability():
    assert _client(_ok({"status": "ok"})).ping() is True
    assert _client(_boom).ping() is False


def test_base_url_is_normalised_for_health_output():
    c = BackendClient(Settings(_env_file=None, backend_base_url="http://localhost:8080/"))
    assert c.base_url == "http://localhost:8080"
    c.close()
