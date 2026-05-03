"""Вспомогательные функции для тестов записи (слоты в будущем)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient

from pereobuyka.storage.memory import DEFAULT_SERVICE_ID


def bookable_starts_at(
    client: TestClient,
    *,
    service_id: object = DEFAULT_SERVICE_ID,
) -> str:
    """Первый свободный starts_at из /slots на горизонте от завтра."""
    d0 = date.today() + timedelta(days=1)
    d1 = d0 + timedelta(days=30)
    r = client.get(
        "/api/v1/slots",
        params={
            "date_from": d0.isoformat(),
            "date_to": d1.isoformat(),
            "service_ids": str(service_id),
        },
    )
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert items, "нет свободных слотов в диапазоне теста"
    return items[0]["starts_at"]


def starts_at_plus_hours(iso: str, hours: int) -> str:
    """Тот же формат наивного ISO, что часто приходит из /slots."""
    normalized = iso.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    out = (dt + timedelta(hours=hours)).astimezone(UTC)
    return out.strftime("%Y-%m-%dT%H:%M:%S")


def bookable_day_and_starts(client: TestClient) -> tuple[str, str]:
    """(YYYY-MM-DD, starts_at) для параметров /slots."""
    s = bookable_starts_at(client)
    return s[:10], s
