"""Типы сервиса консультации (без тяжёлых зависимостей — удобно для DI/тестов)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ConsultationResult:
    """Результат одного запроса консультации."""

    reply: str
    request_id: UUID
