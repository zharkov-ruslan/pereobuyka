"""Handler команды /services — каталог услуг."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from pereobuyka.client.backend import BackendClient, BackendError, BackendUnavailableError

logger = logging.getLogger(__name__)


def build_router(backend: BackendClient) -> Router:
    router = Router()

    @router.message(Command("services"))
    async def cmd_services(message: Message) -> None:
        try:
            services = await backend.get_services()
        except BackendUnavailableError:
            await message.answer("Сервис временно недоступен. Попробуйте позже.")
            return
        except BackendError as exc:
            logger.error("Backend error in /services: %s", exc)
            await message.answer("Не удалось получить список услуг. Попробуйте позже.")
            return

        if not services:
            await message.answer("Каталог услуг пока пуст.")
            return

        lines = ["Услуги:\n"]
        for s in services:
            lines.append(f"• {s['name']} — {s['price']} ₽, {s['duration_minutes']} мин")
        await message.answer("\n".join(lines))

    return router
