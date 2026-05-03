"""Общие утилиты пакета pereobuyka."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Вернуть True, если интервалы [a_start, a_end) и [b_start, b_end) пересекаются."""
    return a_start < b_end and a_end > b_start


def to_utc_aware(dt: datetime, business_tz: str) -> datetime:
    """Наивное время — часы в бизнес-поясе; с tz — перевод в UTC (для сравнения с «сейчас»)."""
    name = (business_tz or "Europe/Moscow").strip() or "Europe/Moscow"
    try:
        tz = ZoneInfo(name)
    except Exception:
        tz = ZoneInfo("UTC")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz).astimezone(UTC)
    return dt.astimezone(UTC)


def to_utc_naive_overlap(dt: datetime, business_tz: str) -> datetime:
    """То же для сравнения интервалов с записями в БД (хранятся как naive UTC)."""
    return to_utc_aware(dt, business_tz).replace(tzinfo=None)
