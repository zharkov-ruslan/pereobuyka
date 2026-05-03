"""Тесты POST /api/v1/appointments."""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from pereobuyka.storage.memory import DEFAULT_SERVICE_ID
from tests.booking_helpers import bookable_starts_at, starts_at_plus_hours


def test_create_appointment_happy_path(client: TestClient, auth_override: UUID) -> None:
    starts_at = bookable_starts_at(client)
    body = {
        "starts_at": starts_at,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    response = client.post("/api/v1/appointments", json=body)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "scheduled"
    assert "id" in data
    assert "ends_at" in data
    assert data["total_price"] == "2000.00"
    assert data["user_id"] == str(auth_override)


def test_create_appointment_ends_at_by_duration(client: TestClient, auth_override: UUID) -> None:
    starts_at = bookable_starts_at(client)
    body = {
        "starts_at": starts_at,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    response = client.post("/api/v1/appointments", json=body)

    data = response.json()
    start = datetime.fromisoformat(data["starts_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(data["ends_at"].replace("Z", "+00:00"))
    assert int((end - start).total_seconds()) == 3600


def test_create_appointment_conflict_returns_409(client: TestClient, auth_override: UUID) -> None:
    starts_at = bookable_starts_at(client)
    body = {
        "starts_at": starts_at,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    first = client.post("/api/v1/appointments", json=body)
    assert first.status_code == 201

    response = client.post("/api/v1/appointments", json=body)

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "SLOT_NOT_AVAILABLE"


def test_create_appointment_past_starts_returns_422(
    client: TestClient, auth_override: UUID
) -> None:
    body = {
        "starts_at": "2000-01-01T09:00:00",
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    response = client.post("/api/v1/appointments", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "STARTS_AT_IN_PAST"


def test_create_appointment_unknown_service_returns_422(
    client: TestClient, auth_override: UUID
) -> None:
    starts_at = bookable_starts_at(client)
    body = {
        "starts_at": starts_at,
        "service_items": [{"service_id": str(uuid4()), "quantity": 1}],
    }

    response = client.post("/api/v1/appointments", json=body)

    assert response.status_code == 422


def test_create_appointment_without_auth_returns_401(client: TestClient) -> None:
    starts_at = bookable_starts_at(client)
    body = {
        "starts_at": starts_at,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    response = client.post("/api/v1/appointments", json=body)

    assert response.status_code == 401


def test_create_two_non_overlapping_appointments_both_succeed(
    client: TestClient, auth_override: UUID
) -> None:
    s0 = bookable_starts_at(client)
    s1 = starts_at_plus_hours(s0, 2)
    body_first = {
        "starts_at": s0,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }
    body_second = {
        "starts_at": s1,
        "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
    }

    r1 = client.post("/api/v1/appointments", json=body_first)
    r2 = client.post("/api/v1/appointments", json=body_second)

    assert r1.status_code == 201
    assert r2.status_code == 201
