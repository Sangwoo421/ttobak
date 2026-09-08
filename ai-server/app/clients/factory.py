"""Pick the backend client from Settings, mirroring app/providers/factory.py.

BACKEND_MODE=http  -> HttpBackendClient, but only if the backend answers GET /api/health at
                     startup; if it does not (or the client can't even be constructed), fall
                     back to MockBackend and record why.
anything else       -> MockBackend (offline dev + CI).

Returns (client, selection) where `selection` is what GET /ai/health reports so config vs.
reality is always visible.
"""
from __future__ import annotations

import logging
from typing import Any

from app.clients.backend_client import BackendUnavailable, HttpBackendClient
from app.clients.mock_backend import MockBackend
from app.config import Settings

logger = logging.getLogger(__name__)


def build_backend(settings: Settings) -> tuple[Any, dict]:
    configured = settings.backend_mode

    if configured != "http":
        logger.info("BACKEND_MODE=%s -> MockBackend (examples JSON)", configured)
        return MockBackend(settings), {
            "configured_mode": configured,
            "client": "mock",
            "fell_back_at_startup": False,
            "startup_error": None,
        }

    # http requested — try to stand up a real client and verify it reaches the backend now.
    try:
        client = HttpBackendClient(settings)
    except Exception as exc:  # noqa: BLE001 - constructing httpx / reading settings blew up
        logger.error("BACKEND_MODE=http but HttpBackendClient could not be built (%s); using MockBackend", exc)
        return MockBackend(settings), {
            "configured_mode": "http",
            "client": "mock",
            "fell_back_at_startup": True,
            "startup_error": f"client build failed: {exc}",
        }

    try:
        client.ping()
    except BackendUnavailable as exc:
        logger.error(
            "BACKEND_MODE=http but %s did not answer at startup (%s); using MockBackend. "
            "Restart once the backend is up.",
            client.base_url, exc,
        )
        client.close()
        return MockBackend(settings), {
            "configured_mode": "http",
            "client": "mock",
            "fell_back_at_startup": True,
            "startup_error": f"backend unreachable at startup: {exc}",
        }

    logger.info("BACKEND_MODE=http -> HttpBackendClient connected to %s", client.base_url)
    return client, {
        "configured_mode": "http",
        "client": "http",
        "fell_back_at_startup": False,
        "startup_error": None,
    }
