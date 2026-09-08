"""Settings: process env > repo-root .env (parent of ai-server) > defaults.

Thresholds live in .env (.env.example is the reference). Do not hardcode them elsewhere.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AI_SERVER_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_SERVER_DIR.parent
AUDIO_CACHE_DIR = AI_SERVER_DIR / "audio_cache"
DEFAULT_EXAMPLES_DIR = REPO_ROOT / "docs" / "contracts" / "examples"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- external AI APIs ----
    openai_api_key: str | None = None
    stt_model: str = "gpt-4o-transcribe"
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "alloy"
    llm_provider: str = "openai"  # openai | anthropic | stub
    openai_llm_model: str = "gpt-4.1-mini"
    anthropic_api_key: str | None = None
    anthropic_llm_model: str = "claude-opus-5"

    # ---- Google Gemini (the key the team actually holds) ----
    gemini_api_key: str | None = None
    gemini_stt_model: str = "gemini-3.5-transcribe"
    gemini_tts_model: str = "gemini-3.1-flash-tts-preview"
    gemini_llm_model: str = "gemini-3.5-flash"
    gemini_tts_voice: str = "Kore"

    # ---- voice layer parameters ----
    senior_silence_ms: int = 2000
    baseline_silence_ms: int = 700
    match_accept: float = 0.80
    match_ask: float = 0.60
    match_tie_gap: float = 0.10
    intent_min_conf: float = 0.70

    # ---- service addresses ----
    backend_base_url: str = "http://localhost:8080"
    ai_base_url: str = "http://localhost:8000"
    backend_mode: str = "http"  # http | mock
    examples_dir: str | None = None  # override for docs/contracts/examples (mock backend)

    @field_validator("openai_api_key", "anthropic_api_key", "gemini_api_key", mode="before")
    @classmethod
    def _blank_key_is_none(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        if not v or v.endswith("..."):  # "" or the .env.example placeholder "sk-..."
            return None
        return v

    @field_validator("llm_provider", "backend_mode", mode="before")
    @classmethod
    def _lower_strip(cls, v):
        return str(v).strip().lower() if v is not None else v

    @property
    def examples_path(self) -> Path:
        return Path(self.examples_dir) if self.examples_dir else DEFAULT_EXAMPLES_DIR


@lru_cache
def get_settings() -> Settings:
    return Settings()
