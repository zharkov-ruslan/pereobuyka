"""Тесты GET /api/v1/slots."""

from uuid import UUID

from fastapi.testclient import TestClient

from pereobuyka.storage.memory import DEFAULT_SERVICE_ID

WORKING_MONDAY = "2026-04-20"  # Понедельник
WEEKEND_SUNDAY = "2026-04-19"  # Воскресенье


def test_slots_working_day_returns_non_empty_list_with_required_fields(client: TestClient) -> None:
    response = client.get(
        "/api/v1/slots",
        params={
            "date_from": WORKING_MONDAY,
            "date_to": WORKING_MONDAY,
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
    response = client.get(
        "/api/v1/slots",
        params={
            "date_from": WEEKEND_SUNDAY,
            "date_to": WEEKEND_SUNDAY,
            "service_ids": str(DEFAULT_SERVICE_ID),
        },
    )
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_slots_missing_date_to_returns_422(client: TestClient) -> None:
    response = client.get(
        "/api/v1/slots",
        params={"date_from": WORKING_MONDAY, "service_ids": str(DEFAULT_SERVICE_ID)},
    )
    assert response.status_code == 422


def test_slots_missing_service_ids_returns_422(client: TestClient) -> None:
    response = client.get(
        "/api/v1/slots",
        params={"date_from": WORKING_MONDAY, "date_to": WORKING_MONDAY},
    )
    assert response.status_code == 422


def test_slots_booked_slot_excluded_from_results(client: TestClient, auth_override: UUID) -> None:
    """После создания записи через API соответствующий слот пропадает из списка."""
    book_body = {
        "starts_at": "2026-04-20T09:00:00",
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    book_response = client.post("/api/v1/appointments", json=book_body)
    assert book_response.status_code == 201

    response = client.get(
        "/api/v1/slots",
        params={
            "date_from": WORKING_MONDAY,
            "date_to": WORKING_MONDAY,
            "service_ids": str(DEFAULT_SERVICE_ID),
        },
    )
    assert response.status_code == 200
    starts_at_list = [s["starts_at"] for s in response.json()["items"]]
    assert not any(s.startswith("2026-04-20T09:00:00") for s in starts_at_list)
