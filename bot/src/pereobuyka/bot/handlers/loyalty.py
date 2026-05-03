"""Handlers для бонусного баланса и истории визитов."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from pereobuyka.bot.display_datetime import format_api_datetime
from pereobuyka.client.backend import BackendClient, BackendError, BackendUnavailableError

logger = logging.getLogger(__name__)


def _as_int(raw: object, default: int = 0) -> int:
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float | str):
        try:
            return int(raw)
        except ValueError:
            return default
    return default


async def run_bonus(message: Message, backend: BackendClient, display_timezone: str) -> None:
    if message.from_user is None:
        return
    user_client = backend.for_user(message.from_user.id)
    try:
        account = await user_client.get_bonus_account()
        transactions = await user_client.list_bonus_transactions(limit=5)
    except BackendUnavailableError:
        await message.answer("Сервис временно недоступен. Попробуйте позже.")
        return
    except BackendError as exc:
        logger.error("Backend error in /bonus: %s", exc)
        await message.answer("Не удалось получить бонусный баланс. Попробуйте позже.")
        return

    lines = [f"Текущий бонусный баланс: {account.get('balance', 0)}"]
    if transactions:
        lines.append("\nПоследние операции:")
        for tx in transactions:
            created = format_api_datetime(str(tx.get("created_at", "")), display_timezone)
            tx_type = str(tx.get("type", "unknown"))
            amount = _as_int(tx.get("amount", 0))
            lines.append(f"• {created}: {tx_type} {amount:+d}")
    await message.answer("\n".join(lines))


async def run_visits(message: Message, backend: BackendClient, display_timezone: str) -> None:
    if message.from_user is None:
        return
    user_client = backend.for_user(message.from_user.id)
    try:
        visits = await user_client.list_visits(limit=5)
    except BackendUnavailableError:
        await message.answer("Сервис временно недоступен. Попробуйте позже.")
        return
    except BackendError as exc:
        logger.error("Backend error in /visits: %s", exc)
        await message.answer("Не удалось получить историю визитов. Попробуйте позже.")
        return

    if not visits:
        await message.answer("История визитов пока пуста.")
        return

    lines = ["Последние визиты:\n"]
    for visit in visits:
        confirmed_at = format_api_datetime(str(visit.get("confirmed_at", "")), display_timezone)
        total_amount = str(visit.get("total_amount", "0"))
        bonus_earned = _as_int(visit.get("bonus_earned", 0))
        bonus_spent = _as_int(visit.get("bonus_spent", 0))
        lines.append(f"• {confirmed_at}: сумма {total_amount} ₽, бонусы +{bonus_earned}, списано {bonus_spent}")
    await message.answer("\n".join(lines))


def build_router(backend: BackendClient, display_timezone: str) -> Router:
    router = Router()

    @router.message(Command("bonus"))
    async def cmd_bonus(message: Message) -> None:
        await run_bonus(message, backend, display_timezone)

    @router.message(Command("visits"))
    async def cmd_visits(message: Message) -> None:
        await run_visits(message, backend, display_timezone)

    return router
