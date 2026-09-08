"""Shared fixtures. Offline only: mock backend + stub LLM, no network, no API keys.

CI runs this with BACKEND_MODE=mock / LLM_PROVIDER=stub; the fixtures below force the
same thing locally by building Settings with `_env_file=None` so the repo-root .env
(which may hold a real GEMINI_API_KEY) is ignored.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Make `import app` work no matter where pytest is invoked from.
AI_SERVER_DIR = Path(__file__).resolve().parents[1]
if str(AI_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVER_DIR))

# Belt-and-suspenders for anything that reads os.environ directly.
os.environ.setdefault("BACKEND_MODE", "mock")
os.environ.setdefault("LLM_PROVIDER", "stub")

from app.config import DEFAULT_EXAMPLES_DIR, Settings  # noqa: E402


@pytest.fixture
def settings() -> Settings:
    """Defaults only — thresholds from config.py, no .env, no keys."""
    return Settings(_env_file=None, backend_mode="mock", llm_provider="stub")


@pytest.fixture
def load_example():
    """Load a docs/contracts/examples/*.json fixture by filename."""
    def _load(name: str):
        return json.loads((DEFAULT_EXAMPLES_DIR / name).read_text(encoding="utf-8"))

    return _load
