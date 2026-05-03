"""Админский сценарий: NL→SQL (SELECT), валидация, выполнение, краткое резюме."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from pereobuyka.api.v1.schemas import AdminDataInsightResponse
from pereobuyka.config import Settings
from pereobuyka.llm.errors import ConsultationOrchestrationError
from pereobuyka.llm.openrouter_client import OpenRouterChatClient
from pereobuyka.services.safe_nl_sql import (
    SafeNlSqlError,
    nl_sql_schema_doc,
    validate_and_normalize_select,
    wrap_with_limit,
)

logger = logging.getLogger(__name__)


def _jsonable_cell(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _row_to_json(row: Any) -> dict[str, object]:
    return {str(k): _jsonable_cell(v) for k, v in dict(row).items()}


async def _llm_generate_select(*, llm: OpenRouterChatClient, question: str, max_rows: int) -> str:
    schema = nl_sql_schema_doc()
    user = (
        f"Вопрос администратора: {question}\n"
        f"Сервер добавит обёртку LIMIT не более {max_rows} строк к результату.\n"
        'Верни один JSON-объект с ключами "sql" (строка SELECT) и "notes" (кратко по-русски). '
        "Только SELECT; без точки с запятой в конце; имена таблиц из схемы."
    )
    raw = await llm.create_chat_completion_text(
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты помощник аналитики PostgreSQL. По схеме ниже генерируешь один безопасный "
                    "SELECT для ответа на вопрос.\n"
                    f"{schema}\n"
                    "Запрещено: любые операции кроме SELECT, обращения к другим схемам, функции "
                    "pg_sleep и подобные.\n"
                    "Ответ только валидным JSON."
                ),
            },
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConsultationOrchestrationError(f"Невалидный JSON от модели: {e!s}") from e
    sql = data.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        raise ConsultationOrchestrationError('Модель не вернула строковое поле "sql"')
    return sql.strip()


async def _llm_summarize(
    *,
    llm: OpenRouterChatClient,
    question: str,
    columns: list[str],
    rows: list[dict[str, object]],
) -> str:
    sample = rows[:25]
    payload = json.dumps(
        {"columns": columns, "sample_rows": sample, "total_rows_shown": len(rows)},
        ensure_ascii=False,
    )
    text_out = await llm.create_chat_completion_text(
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты аналитик. По выборке из БД кратко ответь на вопрос администратора "
                    "на русском (3–8 предложений). Используй только числа и факты из sample_rows; "
                    "не выдумывай. Если данных мало — так и скажи."
                ),
            },
            {
                "role": "user",
                "content": f"Вопрос: {question}\nДанные (JSON): {payload}",
            },
        ],
    )
    return text_out.strip() or "Нет текстового резюме."


async def run_admin_data_insight(
    *,
    settings: Settings,
    session: AsyncSession,
    admin_user_id: UUID,
    question: str,
    llm: OpenRouterChatClient,
) -> AdminDataInsightResponse:
    max_rows = max(1, min(int(settings.admin_nl_sql_max_rows), 500))
    timeout_ms = max(1000, min(int(settings.admin_nl_sql_statement_timeout_ms), 60000))

    raw_sql = await _llm_generate_select(llm=llm, question=question, max_rows=max_rows)
    inner_sql = validate_and_normalize_select(raw_sql)
    wrapped = wrap_with_limit(inner_sql, limit=max_rows)

    logger.info(
        "nl_sql audit admin_user_id=%s question=%r inner_sql=%s",
        admin_user_id,
        question[:400],
        inner_sql[:2000],
    )

    try:
        await session.execute(text(f"SET LOCAL statement_timeout = '{timeout_ms}ms'"))
        result = await session.execute(text(wrapped))
        mappings = result.mappings().all()
    except SQLAlchemyError as e:
        logger.warning("nl_sql execution error: %s", e)
        raise SafeNlSqlError("Не удалось выполнить запрос к базе") from e

    truncated = len(mappings) > max_rows
    slice_rows = mappings[:max_rows]
    columns = [] if not slice_rows else list(slice_rows[0].keys())
    rows = [_row_to_json(r) for r in slice_rows]

    summary = await _llm_summarize(llm=llm, question=question, columns=columns, rows=rows)

    return AdminDataInsightResponse(
        summary=summary,
        sql_executed=wrapped,
        columns=columns,
        rows=rows,
        truncated=truncated,
    )
