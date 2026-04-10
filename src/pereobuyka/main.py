from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from pereobuyka.bot.router import build_root_router
from pereobuyka.config import load_config
from pereobuyka.services.user_service import UserService


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


async def _run() -> None:
    config = load_config()
    _setup_logging(config.log_level)

    bot = Bot(token=config.telegram_bot_token)
    dp = Dispatcher()

    user_service = UserService()
    dp.include_router(build_root_router(user_service=user_service))

    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()

