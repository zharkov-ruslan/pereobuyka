"""Подтверждение визита администратором и начисление бонусов (PostgreSQL)."""

from fastapi.testclient import TestClient

from pereobuyka.storage.memory import DEFAULT_SERVICE_ID

ADMIN_TOKEN = "test-admin-token"


def test_confirm_visit_earns_bonus_after_auth_and_booking(client: TestClient) -> None:
    """Полный цикл: telegram auth → запись → admin confirm visit → бонусы на счёте клиента."""
    tg_id = 42_424_242

    auth = client.post("/api/v1/auth/telegram", json={"telegram_id": tg_id, "name": "Клиент"})
    assert auth.status_code in (200, 201)

    token = auth.json()["access_token"]
    user_id = auth.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    booking = client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "starts_at": "2026-04-20T11:00:00",
            "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
            "bonus_spend": 0,
        },
    )
    assert booking.status_code == 201, booking.text

    appointment_id = booking.json()["id"]

    confirm = client.post(
        "/api/v1/admin/visits",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
        json={
            "appointment_id": appointment_id,
            "lines": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
            "total_amount": "4000.00",
            "bonus_spent": 0,
        },
    )
    assert confirm.status_code == 201, confirm.text

    data = confirm.json()
    assert data["bonus_earned"] == 200

    bonus = client.get("/api/v1/me/bonus-account", headers=headers)
    assert bonus.status_code == 200
    assert bonus.json()["balance"] == 200
    assert bonus.json()["user_id"] == user_id
