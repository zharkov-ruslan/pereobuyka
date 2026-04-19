"""Тесты POST /api/v1/appointments."""

from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from pereobuyka.storage.memory import DEFAULT_SERVICE_ID

_MONDAY_9 = "2026-04-20T09:00:00"
_MONDAY_10 = "2026-04-20T10:00:00"

_VALID_BODY = {
    "starts_at": _MONDAY_9,
    "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
}


def test_create_appointment_happy_path(client: TestClient, auth_override: UUID) -> None:
    response = client.post("/api/v1/appointments", json=_VALID_BODY)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "scheduled"
    assert "id" in data
    assert "ends_at" in data
    assert data["total_price"] == "2000.00"
    assert data["user_id"] == str(auth_override)


def test_create_appointment_ends_at_by_duration(client: TestClient, auth_override: UUID) -> None:
    response = client.post("/api/v1/appointments", json=_VALID_BODY)
    data = response.json()
    # Услуга 60 мин: 09:00 + 60 мин = 10:00
    assert data["ends_at"].startswith("2026-04-20T10:00:00")


def test_create_appointment_conflict_returns_409(client: TestClient, auth_override: UUID) -> None:
    first = client.post("/api/v1/appointments", json=_VALID_BODY)
    assert first.status_code == 201
    response = client.post("/api/v1/appointments", json=_VALID_BODY)
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "SLOT_NOT_AVAILABLE"


def test_create_appointment_unknown_service_returns_422(
    client: TestClient, auth_override: UUID
) -> None:
    body = {
        "starts_at": _MONDAY_10,
        "service_items": [{"service_id": str(uuid4()), "quantity": 1}],
    }
    response = client.post("/api/v1/appointments", json=body)
    assert response.status_code == 422


def test_create_appointment_without_auth_returns_401(client: TestClient) -> None:
    response = client.post("/api/v1/appointments", json=_VALID_BODY)
    assert response.status_code == 401


def test_create_two_non_overlapping_appointments_both_succeed(
    client: TestClient, auth_override: UUID
) -> None:
    body_first = {
        "starts_at": _MONDAY_9,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    body_second = {
        "starts_at": _MONDAY_10,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    r1 = client.post("/api/v1/appointments", json=body_first)
    r2 = client.post("/api/v1/appointments", json=body_second)
    assert r1.status_code == 201
    assert r2.status_code == 201
