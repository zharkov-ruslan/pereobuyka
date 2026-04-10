from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from pereobuyka.services.user_service import UserService


logger = logging.getLogger(__name__)


def build_router(user_service: UserService) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        if message.from_user is None:
            return

        user = user_service.get_or_create(message.from_user.id)
        logger.info("User started bot", extra={"telegram_user_id": user.telegram_user_id})

        await message.answer(
            "Привет! Я бот-консультант шиномонтажа.\n"
            "Пока я в режиме MVP-инфраструктуры: могу отвечать на /start.\n"
            "Дальше добавим прайс, слоты и запись."
        )

    return router

