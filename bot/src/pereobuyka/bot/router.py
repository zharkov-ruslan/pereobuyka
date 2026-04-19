from __future__ import annotations

from aiogram import Router

from pereobuyka.bot.handlers.book import build_router as build_book_router
from pereobuyka.bot.handlers.services import build_router as build_services_router
from pereobuyka.bot.handlers.start import build_router as build_start_router
from pereobuyka.client.backend import BackendClient
from pereobuyka.services.user_service import UserService


def build_root_router(*, user_service: UserService, backend: BackendClient) -> Router:
    router = Router()
    router.include_router(build_start_router(user_service))
    router.include_router(build_services_router(backend))
    router.include_router(build_book_router(backend))
    return router
