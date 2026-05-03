"""Тесты POST /api/v1/consultation/transcribe."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from pereobuyka.config import get_settings


def test_transcribe_503_without_stt_key(
    client: TestClient, auth_override: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SPEECH_TO_TEXT_API_KEY", raising=False)
    get_settings.cache_clear()
    response = client.post(
        "/api/v1/consultation/transcribe",
        files={"file": ("v.ogg", b"x", "audio/ogg")},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_transcribe_200_mocked_upstream(
    client: TestClient, auth_override: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPEECH_TO_TEXT_API_KEY", "sk-test")
    get_settings.cache_clear()
    try:
        with patch(
            "pereobuyka.api.v1.endpoints.consultation.transcribe_uploaded_audio",
            new=AsyncMock(return_value="здравствуйте"),
        ):
            response = client.post(
                "/api/v1/consultation/transcribe",
                files={"file": ("v.ogg", b"x", "audio/ogg")},
            )
        assert response.status_code == 200
        assert response.json() == {"text": "здравствуйте"}
    finally:
        monkeypatch.delenv("SPEECH_TO_TEXT_API_KEY", raising=False)
        get_settings.cache_clear()


def test_transcribe_empty_file_422(client: TestClient, auth_override: UUID) -> None:
    response = client.post(
        "/api/v1/consultation/transcribe",
        files={"file": ("v.ogg", b"", "audio/ogg")},
    )
    assert response.status_code == 422
