"""Форматирование дат из API для сообщений бота (локальный пояс сети)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

_FALLBACK_TZ = "Europe/Moscow"
# Если нет пакета tzdata (Windows), ZoneInfo недоступен — фиксированное UTC+3 для РФ.
_MSK_FIXED = timezone(timedelta(hours=3), "MSK")


def _zone(tz_name: str) -> tzinfo:
    name = (tz_name or "").strip() or _FALLBACK_TZ
    for candidate in (name, _FALLBACK_TZ, "UTC"):
        try:
            return ZoneInfo(candidate)
        except Exception:
            continue
    return _MSK_FIXED


def format_api_datetime(iso_str: str, tz_name: str) -> str:
    """Разобрать ISO из backend, вывести ``dd.MM.yyyy HH:MM`` в заданном поясе (по умолчанию Москва)."""
    try:
        value = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    local = value.astimezone(_zone(tz_name))
    return local.strftime("%d.%m.%Y %H:%M")
