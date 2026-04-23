from __future__ import annotations

from aiogram import Router

from pereobuyka.bot.handlers.appointments import build_router as build_appointments_router
from pereobuyka.bot.handlers.book import build_router as build_book_router
from pereobuyka.bot.handlers.loyalty import build_router as build_loyalty_router
from pereobuyka.bot.handlers.services import build_router as build_services_router
from pereobuyka.bot.handlers.start import build_router as build_start_router
from pereobuyka.client.backend import BackendClient


def build_root_router(*, backend: BackendClient) -> Router:
    router = Router()
    router.include_router(build_start_router(backend))
    router.include_router(build_services_router(backend))
    router.include_router(build_book_router(backend))
    router.include_router(build_appointments_router(backend))
    router.include_router(build_loyalty_router(backend))
    return router
