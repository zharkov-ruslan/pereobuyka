"""Текстовые кнопки меню: приоритет выше режима LLM, те же сценарии, что /commands."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from pereobuyka.bot.handlers.appointments import run_appointments_list
from pereobuyka.bot.handlers.ask import do_ask_stop, enter_consultation_welcome
from pereobuyka.bot.handlers.book import start_booking
from pereobuyka.bot.handlers.loyalty import run_bonus, run_visits
from pereobuyka.bot.handlers.services import run_services_list
from pereobuyka.bot.menu_text import (
    BTN_APPOINTMENTS,
    BTN_ASK,
    BTN_ASK_STOP_LEGACY,
    BTN_BONUS,
    BTN_BOOK,
    BTN_CATALOG,
    BTN_CONSULT_END,
    BTN_VISITS,
)
from pereobuyka.client.backend import BackendClient


def build_router(backend: BackendClient, display_timezone: str) -> Router:
    router = Router()

    @router.message(F.text == BTN_CATALOG)
    async def text_catalog(m: Message) -> None:
        await run_services_list(m, backend)

    @router.message(F.text == BTN_BOOK)
    async def text_book(m: Message, state: FSMContext) -> None:
        await start_booking(m, state, backend)

    @router.message(F.text == BTN_APPOINTMENTS)
    async def text_appt(m: Message) -> None:
        await run_appointments_list(m, backend, display_timezone)

    @router.message(F.text == BTN_BONUS)
    async def text_bonus(m: Message) -> None:
        await run_bonus(m, backend, display_timezone)

    @router.message(F.text == BTN_VISITS)
    async def text_visits(m: Message) -> None:
        await run_visits(m, backend, display_timezone)

    @router.message(F.text == BTN_ASK)
    async def text_ask(m: Message, state: FSMContext) -> None:
        await enter_consultation_welcome(m, state)

    @router.message(F.text.in_({BTN_CONSULT_END, BTN_ASK_STOP_LEGACY}))
    async def text_consult_end(m: Message, state: FSMContext) -> None:
        await do_ask_stop(m, state)

    return router
