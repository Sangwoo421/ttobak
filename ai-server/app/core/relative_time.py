"""ISO datetime -> relative spoken time: "오늘 아침" / "어제 오후" / "그저께 저녁" / "삼일 전"."""
from __future__ import annotations

from datetime import datetime

from app.core.korean_number import to_korean


def part_of_day(hour: int) -> str:
    if hour < 6:
        return "새벽"
    if hour < 12:
        return "아침"
    if hour < 18:
        return "오후"
    return "저녁"


def relative_time(iso: str, now: datetime | None = None) -> str:
    try:
        dt = datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return "얼마 전"
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    now = now or datetime.now()
    days = (now.date() - dt.date()).days
    part = part_of_day(dt.hour)
    if days <= 0:
        return f"오늘 {part}"
    if days == 1:
        return f"어제 {part}"
    if days == 2:
        return f"그저께 {part}"
    return f"{to_korean(days)}일 전"
