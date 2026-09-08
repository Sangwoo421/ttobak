from __future__ import annotations

from fastapi import APIRouter, Request

from app.clients.backend_client import BackendUnavailable, HttpBackendClient

router = APIRouter()


def _backend_health(backend: object, selection: dict) -> tuple[str, dict]:
    """(summary_string, detail_dict) — what is actually wired, and whether it really answers.

    `selection` is set at startup by app.clients.factory.build_backend:
      configured_mode  what BACKEND_MODE asked for
      client           what got wired ("http" | "mock")
      fell_back_at_startup / startup_error   http was asked for but the backend wasn't there

    When client == "http" we probe GET /api/health live here, so config vs. reality is never stale.
    """
    configured = selection.get("configured_mode", "?")
    client = selection.get("client", "?")
    detail: dict = {
        "configured_mode": configured,
        "client": client,
        "fell_back_at_startup": selection.get("fell_back_at_startup", False),
        "startup_error": selection.get("startup_error"),
    }

    if isinstance(backend, HttpBackendClient):
        detail["base_url"] = backend.base_url
        detail["checked"] = "GET /api/health"
        try:
            body = backend.ping()
            detail["reachable"] = True
            detail["backend_status"] = body.get("status")
        except BackendUnavailable as exc:
            detail["reachable"] = False
            detail["error"] = str(exc)
        stats = backend.stats()
        detail["error_count"] = stats["error_count"]
        detail["last_error"] = stats["last_error"]
        if detail["reachable"]:
            return f"http (connected to {backend.base_url})", detail
        return f"http (configured, but UNREACHABLE: {detail.get('error')})", detail

    # MockBackend is wired.
    detail["reachable"] = None
    if configured == "mock":
        return "mock", detail
    if detail["fell_back_at_startup"]:
        return f"mock (fell back from http: {detail['startup_error']})", detail
    return f"mock (BACKEND_MODE={configured}, but mock client is wired)", detail


@router.get("/ai/health")
def health(request: Request) -> dict:
    settings = request.app.state.settings
    names = request.app.state.provider_names
    selection = getattr(request.app.state, "backend_selection", {"configured_mode": settings.backend_mode, "client": "?"})
    backend_summary, backend_detail = _backend_health(request.app.state.backend, selection)
    return {
        "status": "ok",
        "stt": names["stt"],
        "tts": names["tts"],
        "llm": names["llm"],
        "backend_mode": settings.backend_mode,   # 설정값 (.env)
        "backend": backend_summary,              # 실제 클라이언트 + 실연결 여부
        "backend_detail": backend_detail,
    }
