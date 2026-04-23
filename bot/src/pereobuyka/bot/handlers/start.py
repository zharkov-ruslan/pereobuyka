from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from pereobuyka.bot.ask_history import clear_ask_history
from pereobuyka.bot.keyboards import main_menu_reply
from pereobuyka.client.backend import BackendClient, BackendError, BackendUnavailableError

logger = logging.getLogger(__name__)

def _welcome_text(user: User) -> str:
    name = (user.first_name or "").strip()
    lead = f"Привет, {name}!" if name else "Привет!"
    return (
        f"{lead} Я бот-консультант шиномонтажного сервиса «Переобуйка». "
        "Выбери интересующее действие из меню"
    )


def build_router(backend: BackendClient) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return

        await state.clear()
        clear_ask_history(message.from_user.id)
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
        await message.answer(_welcome_text(message.from_user), reply_markup=main_menu_reply())

    return router
