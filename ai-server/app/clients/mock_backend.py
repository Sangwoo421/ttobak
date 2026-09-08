"""Pretends to be the Spring backend by reading docs/contracts/examples/*.json (BACKEND_MODE=mock)."""
from __future__ import annotations

import json
from typing import Any

from app.config import Settings


class MockBackend:
    def __init__(self, settings: Settings) -> None:
        self._dir = settings.examples_path

    def _load(self, filename: str) -> Any:
        return json.loads((self._dir / filename).read_text(encoding="utf-8"))

    def get_briefing(self, user_id: int) -> dict:
        return self._load("briefing.json")

    def get_counterparties(self, user_id: int) -> list[dict]:
        return self._load("counterparties.json")

    def get_classification(self, transaction_id: int) -> dict | None:
        path = self._dir / f"classification-{transaction_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        for item in self.get_briefing(0).get("items", []):
            if item["transaction"]["id"] == transaction_id:
                return item["classification"]
        return None

    def create_summary(self, payload: dict) -> dict:
        return self._load("summary.json")

    def mark_heard(self, notification_id: int) -> None:
        return None

    def create_mute_rule(self, payload: dict) -> dict:
        return {"status": "ok"}

    def create_dialog_log(self, payload: dict) -> dict:
        return {"status": "ok"}
