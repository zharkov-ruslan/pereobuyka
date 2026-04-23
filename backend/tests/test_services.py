"""Тесты GET /api/v1/services."""

from fastapi.testclient import TestClient


def test_services_returns_200_with_items(client: TestClient) -> None:
    response = client.get("/api/v1/services")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0


def test_services_item_has_required_fields(client: TestClient) -> None:
    response = client.get("/api/v1/services")

    item = response.json()["items"][0]
    assert "id" in item
    assert "name" in item
    assert "duration_minutes" in item
    assert "price" in item
    assert "is_active" in item


def test_services_only_active_items_returned(client: TestClient) -> None:
    response = client.get("/api/v1/services")

    items = response.json()["items"]
    assert all(item["is_active"] for item in items)
