"""Тесты оркестратора консультации (без реального OpenRouter)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pereobuyka.config import get_settings
from pereobuyka.llm.openrouter_client import OpenRouterChatClient
from pereobuyka.services.consultation_orchestrator import (
    _parse_starts_at_for_consultation_tool,
    run_consultation,
)
from pereobuyka.services.slot_service import get_free_slots
from pereobuyka.storage.memory import DEFAULT_SERVICE_ID


class _FakeToolCall:
    def __init__(self, id_: str, name: str, arguments: str) -> None:
        self.id = id_
        self.function = type("Fn", (), {"name": name, "arguments": arguments})


class _FakeChoiceMsg:
    def __init__(
        self,
        *,
        content: str | None = None,
        tool_calls: list[_FakeToolCall] | None = None,
    ) -> None:
        self.content = content
        self.tool_calls = tool_calls or []


class _FakeChoice:
    def __init__(self, msg: _FakeChoiceMsg) -> None:
        self.message = msg


class _FakeCompletion:
    def __init__(self, msg: _FakeChoiceMsg) -> None:
        self.choices = [_FakeChoice(msg)]


class _FakeLLMClient:
    def __init__(self, seq: list[_FakeCompletion]) -> None:
        self._seq = list(seq)

    async def create_chat_completion(
        self,
        *,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]] | None = None,
    ) -> Any:
        _ = messages
        _ = tools
        return self._seq.pop(0)


@pytest.mark.asyncio
async def test_run_consultation_create_appointment_tool(
    postgres_connection_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Инструмент create_appointment создаёт запись в PostgreSQL (слот исчезает)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    get_settings.cache_clear()

    engine = create_async_engine(postgres_connection_url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with factory() as session:
            assert isinstance(session, AsyncSession)

            day = date.fromisoformat("2026-04-20")
            before = await get_free_slots(
                session,
                date_from=day,
                date_to=day,
                service_ids=[DEFAULT_SERVICE_ID],
            )
            assert before
            starts_at = before[0].starts_at.isoformat(timespec="minutes")

            args = {
                "starts_at": starts_at,
                "service_items": [{"service_id": str(DEFAULT_SERVICE_ID), "quantity": 1}],
                "bonus_spend": 0,
            }
            args_json = json.dumps(args, ensure_ascii=False)
            tool_call = _FakeToolCall("call_1", "create_appointment", args_json)
            fake_llm = _FakeLLMClient(
                [
                    _FakeCompletion(_FakeChoiceMsg(tool_calls=[tool_call])),
                    _FakeCompletion(_FakeChoiceMsg(content="Готово: запись создана.")),
                ]
            )

            result = await run_consultation(
                settings=get_settings(),
                session=session,
                user_id=uuid4(),
                message="Запишите меня",
                request_id=uuid4(),
                llm_client=cast(OpenRouterChatClient, fake_llm),
            )
            await session.commit()

        assert "запись" in result.reply.lower()

        async with factory() as session:
            after = await get_free_slots(
                session,
                date_from=day,
                date_to=day,
                service_ids=[DEFAULT_SERVICE_ID],
            )
            starts_at_list = [w.starts_at.isoformat(timespec="minutes") for w in after]
            assert not any(s.startswith(starts_at) for s in starts_at_list)
    finally:
        await engine.dispose()
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        get_settings.cache_clear()


@pytest.mark.parametrize(
    ("raw", "y", "mo", "d", "h", "mi"),
    [
        ("2025-04-24T09:00:00", 2025, 4, 24, 9, 0),
        ("2025-04-24T09:00:00+03:00", 2025, 4, 24, 9, 0),
        ("2025-04-24T09:00:00Z", 2025, 4, 24, 9, 0),
        ("2025-04-24T06:00:00+00:00", 2025, 4, 24, 6, 0),
    ],
)
def test_parse_starts_at_strips_offset_for_api_parity(
    raw: str, y: int, mo: int, d: int, h: int, mi: int
) -> None:
    """Тот же конвент, что и у интерактивной записи: наивные часы из ISO."""
    out = _parse_starts_at_for_consultation_tool(raw)
    assert out.tzinfo is None
    assert (out.year, out.month, out.day, out.hour, out.minute) == (y, mo, d, h, mi)
