"""Тесты GET /api/v1/slots."""

from datetime import date, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from pereobuyka.storage.memory import DEFAULT_SERVICE_ID
from tests.booking_helpers import bookable_day_and_starts


def test_slots_working_day_returns_non_empty_list_with_required_fields(client: TestClient) -> None:
    d0 = date.today() + timedelta(days=1)
    d1 = d0 + timedelta(days=14)
    response = client.get(
        "/api/v1/slots",
        params={
            "date_from": d0.isoformat(),
            "date_to": d1.isoformat(),
            "service_ids": str(DEFAULT_SERVICE_ID),
        },
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 0
    slot = items[0]
    assert "starts_at" in slot
    assert "ends_at" in slot


def test_slots_weekend_returns_empty_list(client: TestClient) -> None:
    d = date.today()
    days_ahead = (6 - d.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    sun = d + timedelta(days=days_ahead)
    sun_s = sun.isoformat()

    response = client.get(
        "/api/v1/slots",
        params={
            "date_from": sun_s,
            "date_to": sun_s,
            "service_ids": str(DEFAULT_SERVICE_ID),
        },
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_slots_missing_date_to_returns_422(client: TestClient) -> None:
    d0 = date.today() + timedelta(days=1)
    response = client.get(
        "/api/v1/slots",
        params={"date_from": d0.isoformat(), "service_ids": str(DEFAULT_SERVICE_ID)},
    )

    assert response.status_code == 422
    err = response.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert "fields" in err.get("details", {})


def test_slots_missing_service_ids_returns_422(client: TestClient) -> None:
    d0 = date.today() + timedelta(days=1)
    d1 = d0 + timedelta(days=7)
    response = client.get(
        "/api/v1/slots",
        params={"date_from": d0.isoformat(), "date_to": d1.isoformat()},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_slots_booked_slot_excluded_from_results(client: TestClient, auth_override: UUID) -> None:
    """После создания записи через API соответствующий слот пропадает из списка."""
    day, starts_at = bookable_day_and_starts(client)
    book_body = {
        "starts_at": starts_at,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }

    book_response = client.post("/api/v1/appointments", json=book_body)
    assert book_response.status_code == 201

    response = client.get(
        "/api/v1/slots",
        params={
            "date_from": day,
            "date_to": day,
            "service_ids": str(DEFAULT_SERVICE_ID),
        },
    )

    assert response.status_code == 200
    prefix16 = starts_at[:16]
    starts_at_list = [s["starts_at"] for s in response.json()["items"]]
    assert not any(s[:16] == prefix16 for s in starts_at_list)
