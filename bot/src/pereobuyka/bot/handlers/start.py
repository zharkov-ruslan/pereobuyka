from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from pereobuyka.client.backend import BackendClient, BackendError, BackendUnavailableError

logger = logging.getLogger(__name__)

_WELCOME = (
    "Привет! Я бот-консультант шиномонтажного сервиса «Переобуйка».\n\n"
    "Доступные команды:\n"
    "/services — каталог услуг и цен\n"
    "/book — записаться на обслуживание\n"
    "/appointments — мои активные записи и отмена\n"
    "/bonus — бонусный баланс и операции\n"
    "/visits — последние визиты\n"
)


def build_router(backend: BackendClient) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        if message.from_user is None:
            return

        user_client = backend.for_user(message.from_user.id)
        try:
            profile = await user_client.get_me()
            logger.info(
                "User resolved in backend",
                extra={"telegram_user_id": message.from_user.id, "user_id": profile.get("id")},
            )
        except BackendUnavailableError:
            await message.answer("Сервис временно недоступен. Попробуйте позже.")
            return
        except BackendError as exc:
            if exc.status_code == 404:
                full_name = (
                    " ".join(
                        item for item in [message.from_user.first_name, message.from_user.last_name] if item
                    ).strip()
                    or f"user-{message.from_user.id}"
                )
                try:
                    await user_client.auth_telegram(
                        telegram_id=message.from_user.id,
                        name=full_name,
                    )
                except (BackendUnavailableError, BackendError) as register_exc:
                    logger.error("Backend registration error in /start: %s", register_exc)
                    await message.answer("Сервис временно недоступен. Попробуйте позже.")
                    return
                logger.info("User registered in backend", extra={"telegram_user_id": message.from_user.id})
            else:
                logger.error("Backend error in /start: %s", exc)
                await message.answer("Сервис временно недоступен. Попробуйте позже.")
                return
        await message.answer(_WELCOME)

    return router
