from __future__ import annotations

from fastapi import APIRouter, Request

from app.clients.backend_client import BackendClient
from app.clients.mock_backend import MockBackend

router = APIRouter()


def _backend_status(backend: object, backend_mode: str) -> str:
    """What is actually wired and reachable, not what .env asked for.

    For the http client this pings /api/health, so a backend that is configured but down reads as
    'http (unreachable ...)' rather than a green 'http' that only means the object was constructed.
    """
    if isinstance(backend, BackendClient):
        base = backend.base_url
        return f"http ({base})" if backend.ping() else f"http (unreachable: {base})"
    if isinstance(backend, MockBackend):
        if backend_mode == "mock":
            return "mock"
        return f"mock (BACKEND_MODE={backend_mode})"
    return type(backend).__name__


@router.get("/ai/health")
def health(request: Request) -> dict:
    settings = request.app.state.settings
    names = request.app.state.provider_names
    return {
        "status": "ok",
        "stt": names["stt"],
        "tts": names["tts"],
        "llm": names["llm"],
        "backend_mode": settings.backend_mode,                       # 설정값 (.env)
        "backend": _backend_status(request.app.state.backend, settings.backend_mode),  # 실제 클라이언트
    }
