"""Зависимости для консультации (DI в FastAPI + тестовые overrides)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from pereobuyka.config import Settings, get_settings
from pereobuyka.llm.openrouter_client import OpenRouterChatClient
from pereobuyka.services.consultation_orchestrator import run_consultation
from pereobuyka.services.consultation_types import ConsultationResult


class ConsultationRunner(Protocol):
    """Callable-интерфейс оркестратора (удобно подменять в тестах)."""

    async def __call__(
        self,
        *,
        settings: Settings,
        session: AsyncSession | None,
        user_id: UUID,
        message: str,
        request_id: UUID,
        llm_client: OpenRouterChatClient,
        history: list[dict[str, str]] | None = None,
    ) -> ConsultationResult: ...


async def get_consultation_runner() -> ConsultationRunner:
    """FastAPI Depends: дефолтный раннер — ``run_consultation``."""
    return run_consultation


def build_default_openrouter_client(settings: Settings | None = None) -> OpenRouterChatClient:
    """Собрать LLM-клиент из настроек."""
    s = settings or get_settings()
    return OpenRouterChatClient(
        api_key=s.openrouter_api_key,
        base_url=s.openrouter_base_url,
        model=s.openrouter_model,
        timeout_seconds=s.consultation_llm_timeout_seconds,
    )
