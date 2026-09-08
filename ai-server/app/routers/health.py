from __future__ import annotations

from fastapi import APIRouter, Request

from app.clients.mock_backend import MockBackend

router = APIRouter()


def _backend_status(backend: object, backend_mode: str) -> str:
    """What is actually wired, not what .env asked for.

    There is no app/clients/backend_client.py yet, so app.state.backend is always a MockBackend.
    When BACKEND_MODE=http the config and reality disagree — say so instead of parroting 'http'.
    """
    if isinstance(backend, MockBackend):
        if backend_mode == "mock":
            return "mock"
        return f"mock (no http client; BACKEND_MODE={backend_mode})"
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
