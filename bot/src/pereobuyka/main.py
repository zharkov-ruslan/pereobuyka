from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from pereobuyka.bot.router import build_root_router
from pereobuyka.client.backend import BackendClient
from pereobuyka.config import load_config


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


async def _run() -> None:
    config = load_config()
    _setup_logging(config.log_level)

    bot = Bot(token=config.telegram_bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    backend = BackendClient(
        config.backend_base_url,
        config.bot_secret,
        consultation_read_timeout=config.consultation_request_timeout,
    )

    dp.include_router(build_root_router(backend=backend))

    try:
        await dp.start_polling(bot)
    finally:
        await backend.close()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
