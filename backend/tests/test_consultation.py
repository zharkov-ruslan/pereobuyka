"""Тесты POST /api/v1/consultation/messages."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from pereobuyka.api.v1.endpoints import consultation as consultation_endpoint
from pereobuyka.config import get_settings
from pereobuyka.main import app
from pereobuyka.services.consultation_deps import get_consultation_runner
from pereobuyka.services.consultation_types import ConsultationResult


class _DummyLLM:
    pass


@pytest.fixture()
def openrouter_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_consultation_requires_openrouter_key(client: TestClient, auth_override: UUID) -> None:
    get_settings.cache_clear()
    response = client.post("/api/v1/consultation/messages", json={"message": "Привет"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_consultation_empty_message_422(
    client: TestClient, auth_override: UUID, openrouter_key: None
) -> None:
    response = client.post("/api/v1/consultation/messages", json={"message": "   "})
    assert response.status_code == 422


def test_consultation_happy_path_override_runner(
    client: TestClient, auth_override: UUID, openrouter_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_run(**kwargs: Any) -> ConsultationResult:  # noqa: ANN401
        assert kwargs.get("history") == [
            {"role": "user", "content": "привет"},
            {"role": "assistant", "content": "здрасьте"},
        ]
        return ConsultationResult(reply="ok", request_id=kwargs["request_id"])

    monkeypatch.setattr(
        consultation_endpoint, "build_default_openrouter_client", lambda settings: _DummyLLM()
    )
    app.dependency_overrides[get_consultation_runner] = lambda: _fake_run
    try:
        response = client.post(
            "/api/v1/consultation/messages",
            json={
                "message": "Привет",
                "history": [
                    {"role": "user", "content": "привет"},
                    {"role": "assistant", "content": "здрасьте"},
                ],
            },
        )
    finally:
        app.dependency_overrides.pop(get_consultation_runner, None)

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "ok"
    assert data["request_id"]


def test_consultation_provider_error_maps_to_503(
    client: TestClient, auth_override: UUID, openrouter_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pereobuyka.llm.errors import ConsultationProviderError

    async def _boom(**kwargs: Any) -> ConsultationResult:  # noqa: ANN401
        raise ConsultationProviderError()

    monkeypatch.setattr(
        consultation_endpoint, "build_default_openrouter_client", lambda settings: _DummyLLM()
    )
    app.dependency_overrides[get_consultation_runner] = lambda: _boom
    try:
        response = client.post("/api/v1/consultation/messages", json={"message": "Привет"})
    finally:
        app.dependency_overrides.pop(get_consultation_runner, None)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
