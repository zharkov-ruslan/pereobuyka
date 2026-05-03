"""Интеграционный тест POST /admin/analytics/data-insight с подменой LLM."""

from __future__ import annotations

import pytest

from pereobuyka.services import admin_nl_sql_service as nl_mod


@pytest.fixture
def patch_nl_sql_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _gen(*_a: object, **_k: object) -> str:
        return "SELECT COUNT(*)::bigint AS client_count FROM users WHERE role = 'client'"

    async def _sum(*_a: object, **_k: object) -> str:
        return "В выборке указано число клиентов."

    monkeypatch.setattr(nl_mod, "_llm_generate_select", _gen)
    monkeypatch.setattr(nl_mod, "_llm_summarize", _sum)


def test_admin_data_insight_success(
    client,
    postgres_connection_url: str,
    patch_nl_sql_llm: None,
) -> None:
    _ = postgres_connection_url
    response = client.post(
        "/api/v1/admin/analytics/data-insight",
        headers={"Authorization": "Bearer test-admin-token"},
        json={"question": "Сколько клиентов в базе?"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"]
    assert payload["truncated"] is False
    assert payload["columns"] == ["client_count"]
    assert len(payload["rows"]) == 1
    assert int(payload["rows"][0]["client_count"]) >= 1


def test_admin_data_insight_forbidden_without_admin_token(client) -> None:
    response = client.post(
        "/api/v1/admin/analytics/data-insight",
        headers={"Authorization": "Bearer mvp-00000000-0000-0000-0000-000000000099"},
        json={"question": "test"},
    )
    assert response.status_code == 403
