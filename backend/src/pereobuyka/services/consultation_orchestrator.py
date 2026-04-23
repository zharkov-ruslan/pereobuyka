"""Оркестратор LLM-консультации: OpenRouter + function-calling для фактов и записи."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from pereobuyka.api.v1.schemas import AppointmentCreateRequest, ServiceLineItem, SlotWindow
from pereobuyka.config import Settings, get_settings
from pereobuyka.llm.errors import ConsultationOrchestrationError
from pereobuyka.llm.openrouter_client import OpenRouterChatClient
from pereobuyka.llm.system_prompt import DEFAULT_SYSTEM_PROMPT
from pereobuyka.services.appointment_service import create_appointment
from pereobuyka.services.consultation_types import ConsultationResult
from pereobuyka.services.slot_service import get_free_slots
from pereobuyka.services.visit_commands import (
    fetch_bonus_account_client,
    fetch_loyalty_rules_public,
)
from pereobuyka.storage.postgres_repos import fetch_services_map

logger = logging.getLogger(__name__)


def _parse_starts_at_for_consultation_tool(raw: str) -> datetime:
    """Разобрать ``starts_at`` из инструмента ``create_appointment``.

    Слоты из ``list_slots`` — наивные ``YYYY-MM-DDTHH:MM`` (как в JSON к ``POST /appointments``).
    Модель часто добавляет ``+03:00``/``Z``; тогда :func:`datetime.fromisoformat` даёт aware-время,
    и :func:`pereobuyka.services.appointment_service.create_appointment` переводит в UTC
    (9:00 +03:00 → 6:00 UTC), тогда как интерактивная запись шлёт наивные часы.
    Снимаем смещение и сохраняем «числа на часах», как в ответе ``list_slots``.
    """
    s = str(raw).strip()
    if " " in s and "T" not in s:
        s = s.replace(" ", "T", 1)
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_services",
            "description": (
                "Вернуть актуальный каталог услуг: id, название, цену, длительность, активность."
            ),
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_slots",
            "description": (
                "Вернуть свободные окна записи в диапазоне дат для указанных услуг. "
                "Прошедшие на сегодня (по поясу сети) в ответе нет. "
                "Слоты в тексте — только по результату этого вызова."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "YYYY-MM-DD"},
                    "date_to": {"type": "string", "description": "YYYY-MM-DD"},
                    "service_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "UUID услуг",
                    },
                },
                "required": ["date_from", "date_to", "service_ids"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_appointment",
            "description": (
                "Создать запись пользователя. Только после согласования времени и состава услуг."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "starts_at": {
                        "type": "string",
                        "description": "ISO-8601 datetime начала записи",
                    },
                    "service_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "service_id": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1},
                            },
                            "required": ["service_id", "quantity"],
                            "additionalProperties": False,
                        },
                    },
                    "bonus_spend": {"type": "integer", "minimum": 0, "default": 0},
                },
                "required": ["starts_at", "service_items"],
                "additionalProperties": False,
            },
        },
    },
]


def _system_prompt(settings: Settings) -> str:
    raw = settings.consultation_system_prompt.strip()
    return raw or DEFAULT_SYSTEM_PROMPT


def _clock_block(settings: Settings) -> str:
    """Стабильная «сегодняшняя» дата/время для подписей и ссылок в ответе."""
    name = (settings.consultation_business_timezone or "Europe/Moscow").strip() or "Europe/Moscow"
    try:
        tz = ZoneInfo(name)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    return (
        f"ТЕКУЩИЕ ДАТА И ВРЕМЯ (часовой пояс: {name}): сейчас {now.isoformat(timespec='minutes')}. "
        f"Календарная дата «сегодня»: {now.date().isoformat()}. "
        "Слова «сегодня»/«завтра»/«послезавтра» в реплике пользователя относит к ЭТОЙ дате; "
        "в тексте не подставляй вымышленные даты (например, другой месяц/день). "
        "Перечисление конкретных времён слотов — только после вызова list_slots."
    )


def _drop_past_slot_windows(windows: list[SlotWindow], tz_name: str) -> list[SlotWindow]:
    """Окна, которые уже начались или прошли в бизнес-часовом поясе, отбрасываем."""
    name = (tz_name or "Europe/Moscow").strip() or "Europe/Moscow"
    try:
        tz = ZoneInfo(name)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    out: list[SlotWindow] = []
    for w in windows:
        s = w.starts_at
        s_aware = s.replace(tzinfo=tz) if s.tzinfo is None else s.astimezone(tz)
        if s_aware > now:
            out.append(w)
    return out


async def _client_facts_block(*, session: AsyncSession | None, user_id: UUID) -> str:
    if session is None:
        return (
            "КОНТЕКСТ (факты): недоступен без PostgreSQL-сессии "
            "(локальный режим без полноценной БД)."
        )

    parts: list[str] = []
    try:
        rules = await fetch_loyalty_rules_public(session)
        parts.append(f"Правила лояльности: {rules.model_dump_json()}")
    except Exception:
        parts.append("Правила лояльности: недоступны")

    try:
        bonus = await fetch_bonus_account_client(session, user_id)
        parts.append(f"Бонусный счёт клиента: {bonus.model_dump_json()}")
    except Exception:
        parts.append("Бонусный счёт клиента: недоступен")

    return "КОНТЕКСТ (факты сервиса для пользователя):\n" + "\n".join(parts)


async def _tool_list_services(session: AsyncSession | None) -> dict[str, Any]:
    if session is None:
        return {"ok": False, "error": {"code": "DB_UNAVAILABLE", "message": "Нет подключения к БД"}}
    services = await fetch_services_map(session, active_only=True)
    items = [
        {
            "id": str(s.id),
            "name": s.name,
            "duration_minutes": s.duration_minutes,
            "price": str(s.price),
            "is_active": s.is_active,
        }
        for s in services.values()
        if s.is_active
    ]
    return {"ok": True, "items": items}


async def _tool_list_slots(
    session: AsyncSession | None,
    args: dict[str, Any],
) -> dict[str, Any]:
    try:
        d0 = date.fromisoformat(str(args["date_from"]))
        d1 = date.fromisoformat(str(args["date_to"]))
        raw_ids = args["service_ids"]
        if not isinstance(raw_ids, list) or not raw_ids:
            return {"ok": False, "error": {"code": "INVALID_ARGS", "message": "service_ids пустой"}}
        service_ids = [UUID(str(x)) for x in raw_ids]
    except Exception:
        return {"ok": False, "error": {"code": "INVALID_ARGS", "message": "Неверные аргументы"}}

    if d1 < d0:
        return {
            "ok": False,
            "error": {"code": "INVALID_RANGE", "message": "date_to раньше date_from"},
        }

    slots = await get_free_slots(session, d0, d1, service_ids)
    cfg = get_settings()
    slots = _drop_past_slot_windows(slots, cfg.consultation_business_timezone)
    # Ограничиваем размер ответа, чтобы не раздувать контекст
    cap = 40
    trimmed = slots[:cap]
    return {
        "ok": True,
        "items": [
            {
                "starts_at": w.starts_at.isoformat(timespec="minutes"),
                "ends_at": w.ends_at.isoformat(timespec="minutes"),
            }
            for w in trimmed
        ],
        "truncated": len(slots) > cap,
        "total": len(slots),
    }


async def _tool_create_appointment(
    session: AsyncSession | None,
    user_id: UUID,
    args: dict[str, Any],
) -> dict[str, Any]:
    try:
        try:
            starts_at = _parse_starts_at_for_consultation_tool(str(args["starts_at"]))
        except (TypeError, ValueError) as e:
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_ARGS",
                    "message": f"Некорректный starts_at: {e!s}",
                },
            }
        raw_items = args["service_items"]
        if not isinstance(raw_items, list) or not raw_items:
            return {
                "ok": False,
                "error": {"code": "INVALID_ARGS", "message": "service_items пустой"},
            }
        items = [
            ServiceLineItem(service_id=UUID(str(it["service_id"])), quantity=int(it["quantity"]))
            for it in raw_items
        ]
        bonus_spend = int(args.get("bonus_spend", 0) or 0)
        req = AppointmentCreateRequest(
            starts_at=starts_at, service_items=items, bonus_spend=bonus_spend
        )
        appt = await create_appointment(session, user_id, req)
        return {
            "ok": True,
            "appointment": {
                "id": str(appt.id),
                "starts_at": appt.starts_at.isoformat(timespec="minutes"),
                "ends_at": appt.ends_at.isoformat(timespec="minutes"),
                "total_price": appt.total_price,
                "status": str(appt.status.value),
            },
        }
    except HTTPException as e:
        if isinstance(e.detail, dict):
            err = e.detail.get("error", {})
            if isinstance(err, dict):
                return {
                    "ok": False,
                    "error": {
                        "code": err.get("code", "HTTP_ERROR"),
                        "message": err.get("message", ""),
                    },
                }
        return {
            "ok": False,
            "error": {"code": "HTTP_ERROR", "message": "Не удалось создать запись"},
        }
    except Exception:
        logger.exception("create_appointment tool failed")
        return {
            "ok": False,
            "error": {"code": "INTERNAL", "message": "Внутренняя ошибка при создании записи"},
        }


async def _dispatch_tool(
    *,
    name: str,
    arguments_json: str,
    session: AsyncSession | None,
    user_id: UUID,
) -> str:
    try:
        args = json.loads(arguments_json or "{}")
        if not isinstance(args, dict):
            args = {}
    except json.JSONDecodeError:
        return json.dumps(
            {
                "ok": False,
                "error": {"code": "INVALID_JSON", "message": "Некорректный JSON аргументов"},
            }
        )

    if name == "list_services":
        payload = await _tool_list_services(session)
    elif name == "list_slots":
        payload = await _tool_list_slots(session, args)
    elif name == "create_appointment":
        payload = await _tool_create_appointment(session, user_id, args)
    else:
        payload = {"ok": False, "error": {"code": "UNKNOWN_TOOL", "message": name}}

    return json.dumps(payload, ensure_ascii=False)


async def run_consultation(
    *,
    settings: Settings,
    session: AsyncSession | None,
    user_id: UUID,
    message: str,
    request_id: UUID,
    llm_client: OpenRouterChatClient,
    history: list[dict[str, str]] | None = None,
) -> ConsultationResult:
    """Один пользовательский запрос: LLM + до N раундов tool-calls."""
    _ = request_id  # зарезервировано для логов/трейсинга

    facts = await _client_facts_block(session=session, user_id=user_id)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _system_prompt(settings)},
        {"role": "system", "content": facts},
        {"role": "system", "content": _clock_block(settings)},
    ]
    if history:
        for h in history:
            role = h.get("role", "")
            content = (h.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    max_rounds = max(1, int(settings.consultation_max_tool_rounds))
    for _round in range(max_rounds):
        completion = await llm_client.create_chat_completion(messages=messages, tools=_TOOLS)
        choice = completion.choices[0].message

        tool_calls = getattr(choice, "tool_calls", None) or []
        if tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": choice.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments or "{}",
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )
            for tc in tool_calls:
                name = tc.function.name
                output = await _dispatch_tool(
                    name=name,
                    arguments_json=tc.function.arguments or "{}",
                    session=session,
                    user_id=user_id,
                )
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})
            continue

        text = (choice.content or "").strip()
        if not text:
            raise ConsultationOrchestrationError("Пустой ответ модели")
        return ConsultationResult(reply=text, request_id=request_id)

    raise ConsultationOrchestrationError("Превышен лимит раундов tool-calls")
