from __future__ import annotations

from aiogram import Router

from pereobuyka.bot.handlers.start import build_router as build_start_router
from pereobuyka.services.user_service import UserService


def build_root_router(*, user_service: UserService) -> Router:
    router = Router()
    router.include_router(build_start_router(user_service))
    return router

