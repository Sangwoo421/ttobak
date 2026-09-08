from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.clients.mock_backend import MockBackend
from app.config import AUDIO_CACHE_DIR, get_settings
from app.providers.factory import build_safe_llm, build_stt_provider, build_tts_provider
from app.routers import debug, health, session, stt, summary, tts, turn

settings = get_settings()
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="또박또박 AI Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

stt_provider, stt_name = build_stt_provider(settings)
tts_provider, tts_name = build_tts_provider(settings)
safe_llm = build_safe_llm(settings)

# BACKEND_MODE=http (real Spring backend) lands with app/clients/backend_client.py; mock is all
# that exists so far, so it's used regardless of the setting.
app.state.settings = settings
app.state.backend = MockBackend(settings)
app.state.stt = stt_provider
app.state.tts = tts_provider
app.state.llm = safe_llm
app.state.provider_names = {"stt": stt_name, "tts": tts_name, "llm": safe_llm.name}

app.include_router(health.router)
app.include_router(session.router)
app.include_router(turn.router)
app.include_router(stt.router)
app.include_router(tts.router)
app.include_router(summary.router)
app.include_router(debug.router)

app.mount("/ai/audio", StaticFiles(directory=str(AUDIO_CACHE_DIR)), name="audio")
