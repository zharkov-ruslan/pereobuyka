"""Handler команды /book — FSM-запись на обслуживание."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from pereobuyka.client.backend import (
    BackendClient,
    BackendError,
    BackendUnavailableError,
    SlotWindow,
)

logger = logging.getLogger(__name__)

# ── Состояния FSM ────────────────────────────────────────────────────────────


class BookStates(StatesGroup):
    choosing_service = State()
    entering_date = State()
    choosing_slot = State()


# ── Callback-данные ──────────────────────────────────────────────────────────


class ServiceCb(CallbackData, prefix="bksvc"):
    """Только service_id: в callback_data Telegram лимит 64 байта, имя услуги не помещается."""

    service_id: str


class DateCb(CallbackData, prefix="bkdate"):
    iso_date: str


class SlotCb(CallbackData, prefix="bkslot"):
    """Unix time UTC — в ISO-строке есть ``:``, aiogram CallbackData их запрещает в полях."""

    start_ts: int


class CancelCb(CallbackData, prefix="bkcancel"):
    pass


# ── Helpers ──────────────────────────────────────────────────────────────────


def _today() -> date:
    return datetime.now(tz=UTC).date()


def _filter_upcoming_slots(slots: list[SlotWindow], day: date) -> list[SlotWindow]:
    """Окна, которые ещё не начались: для сегодняшнего дня — только с start строго после «сейчас» (UTC)."""
    tday = _today()
    if day < tday:
        return []
    if day > tday:
        return list(slots)
    now = datetime.now(tz=UTC)
    return [s for s in slots if _parse_api_datetime(str(s["starts_at"])) > now]


def _parse_api_datetime(iso: str) -> datetime:
    """Разбор datetime из ответа API (naive считаем UTC)."""
    raw = iso.replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _starts_at_iso_for_api(start_ts: int) -> str:
    """Формат как в тестах backend: ``2026-04-20T09:00:00``."""
    return datetime.fromtimestamp(start_ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S")


def _date_keyboard(*, include_today: bool = True) -> InlineKeyboardMarkup:
    t = _today()
    if include_today:
        days: list[tuple[date, str]] = [
            (t, "Сегодня"),
            (t + timedelta(days=1), "Завтра"),
            (t + timedelta(days=2), "Послезавтра"),
        ]
    else:
        d3 = t + timedelta(days=3)
        days = [
            (t + timedelta(days=1), "Завтра"),
            (t + timedelta(days=2), "Послезавтра"),
            (d3, d3.strftime("%d.%m")),
        ]
    buttons = [[InlineKeyboardButton(text=label, callback_data=DateCb(iso_date=str(d)).pack())] for d, label in days]
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data=CancelCb().pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _slot_keyboard(slots: list[SlotWindow]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for slot in slots:
        starts = slot["starts_at"]
        ends = slot["ends_at"]
        start_time = str(starts)[11:16]
        end_time = str(ends)[11:16]
        label = f"{start_time}–{end_time}"
        start_ts = int(_parse_api_datetime(str(starts)).timestamp())
        btn = InlineKeyboardButton(
            text=label,
            callback_data=SlotCb(start_ts=start_ts).pack(),
        )
        row.append(btn)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Отмена", callback_data=CancelCb().pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Построение роутера ───────────────────────────────────────────────────────


def build_router(backend: BackendClient) -> Router:
    router = Router()

    @router.message(Command("book"))
    async def cmd_book(message: Message, state: FSMContext) -> None:
        await state.clear()
        try:
            services = await backend.get_services()
        except (BackendUnavailableError, BackendError):
            await message.answer("Сервис временно недоступен. Попробуйте позже.")
            return

        if not services:
            await message.answer("Каталог услуг пуст, запись недоступна.")
            return

        buttons = [
            [
                InlineKeyboardButton(
                    text=f"{s['name']} — {s['price']} ₽",
                    callback_data=ServiceCb(service_id=str(s["id"])).pack(),
                )
            ]
            for s in services
        ]
        buttons.append([InlineKeyboardButton(text="Отмена", callback_data=CancelCb().pack())])
        await state.set_state(BookStates.choosing_service)
        await message.answer(
            "Выберите услугу:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    @router.callback_query(BookStates.choosing_service, ServiceCb.filter())
    async def on_service_chosen(callback: CallbackQuery, callback_data: ServiceCb, state: FSMContext) -> None:
        try:
            services = await backend.get_services()
        except (BackendUnavailableError, BackendError):
            await callback.answer("Не удалось загрузить услуги.", show_alert=True)
            return
        service = next((s for s in services if str(s.get("id")) == callback_data.service_id), None)
        if service is None:
            await callback.answer("Услуга не найдена. Начните снова с /book.", show_alert=True)
            return
        if callback.from_user is None:
            await callback.answer("Не удалось определить пользователя.")
            return
        service_name = str(service["name"])
        await state.update_data(
            service_id=callback_data.service_id,
            service_name=service_name,
            duration=int(service["duration_minutes"]),
        )
        include_today = True
        user_client = backend.for_user(callback.from_user.id)
        try:
            day_slots = await user_client.get_slots(_today(), _today(), [UUID(callback_data.service_id)])
            include_today = bool(_filter_upcoming_slots(day_slots, _today()))
        except (BackendUnavailableError, BackendError):
            pass
        await state.set_state(BookStates.entering_date)
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"Услуга: {service_name}\n\nВыберите дату:",
            reply_markup=_date_keyboard(include_today=include_today),
        )
        await callback.answer()

    @router.callback_query(BookStates.entering_date, DateCb.filter())
    async def on_date_chosen(callback: CallbackQuery, callback_data: DateCb, state: FSMContext) -> None:
        fsm_data = await state.get_data()
        service_id = UUID(fsm_data["service_id"])
        chosen_date = date.fromisoformat(callback_data.iso_date)

        if callback.from_user is None:
            await callback.answer("Не удалось определить пользователя.")
            return

        user_client = backend.for_user(callback.from_user.id)
        try:
            slots = await user_client.get_slots(chosen_date, chosen_date, [service_id])
        except BackendUnavailableError:
            await callback.message.edit_text(  # type: ignore[union-attr]
                "Сервис временно недоступен. Попробуйте позже."
            )
            await state.clear()
            await callback.answer()
            return
        except BackendError as exc:
            logger.error("Backend error fetching slots: %s", exc)
            await callback.message.edit_text(  # type: ignore[union-attr]
                "Не удалось получить слоты. Попробуйте позже."
            )
            await state.clear()
            await callback.answer()
            return

        upcoming = _filter_upcoming_slots(slots, chosen_date)
        tday = _today()
        if not upcoming:
            if chosen_date == tday and slots:
                await callback.message.edit_text(  # type: ignore[union-attr]
                    "Запись на сегодня невозможна: на оставшееся время нет свободных окон. Выберите другую дату:",
                    reply_markup=_date_keyboard(include_today=False),
                )
            else:
                await callback.message.edit_text(  # type: ignore[union-attr]
                    f"На {callback_data.iso_date} свободных окон нет. Выберите другую дату:",
                    reply_markup=_date_keyboard(),
                )
            await callback.answer()
            return

        await state.update_data(chosen_date=callback_data.iso_date)
        await state.set_state(BookStates.choosing_slot)
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"Доступные окна на {callback_data.iso_date}:",
            reply_markup=_slot_keyboard(upcoming),
        )
        await callback.answer()

    @router.callback_query(BookStates.choosing_slot, SlotCb.filter())
    async def on_slot_chosen(callback: CallbackQuery, callback_data: SlotCb, state: FSMContext) -> None:
        fsm_data = await state.get_data()
        if callback.from_user is None:
            await callback.answer("Не удалось определить пользователя.")
            return

        user_client = backend.for_user(callback.from_user.id)
        service_id = fsm_data["service_id"]
        service_name = fsm_data["service_name"]

        try:
            appointment = await user_client.create_appointment(
                starts_at=_starts_at_iso_for_api(callback_data.start_ts),
                service_items=[{"service_id": service_id, "quantity": 1}],
            )
        except BackendUnavailableError:
            await callback.message.edit_text(  # type: ignore[union-attr]
                "Сервис временно недоступен. Попробуйте позже."
            )
            await state.clear()
            await callback.answer()
            return
        except BackendError as exc:
            if exc.status_code == 409:
                await callback.message.edit_text(  # type: ignore[union-attr]
                    "Это время уже занято. Выберите другой слот:",
                    reply_markup=_slot_keyboard(await _refetch_slots(user_client, fsm_data, service_id)),
                )
            elif exc.status_code == 401:
                logger.warning("Appointment create 401: %s", exc)
                await callback.message.edit_text(  # type: ignore[union-attr]
                    "Запись недоступна: не настроена авторизация бота с backend.\n\n"
                    "Задайте одинаковый BOT_SECRET в файлах bot/.env и backend/.env "
                    "и перезапустите бота и API."
                )
                await state.clear()
            else:
                logger.error("Backend error creating appointment: %s", exc)
                await callback.message.edit_text(  # type: ignore[union-attr]
                    "Не удалось создать запись. Попробуйте позже."
                )
                await state.clear()
            await callback.answer()
            return

        start_time = appointment["starts_at"][11:16]
        end_time = appointment["ends_at"][11:16]
        await state.clear()
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"Запись подтверждена!\n\n"
            f"Услуга: {service_name}\n"
            f"Дата: {appointment['starts_at'][:10]}\n"
            f"Время: {start_time}–{end_time}\n"
            f"Стоимость: {appointment['total_price']} ₽"
        )
        await callback.answer("Запись создана!")

    @router.callback_query(CancelCb.filter())
    async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.message.edit_text("Запись отменена.")  # type: ignore[union-attr]
        await callback.answer()

    # Игнорировать callback'и не в нужных состояниях (защита от устаревших сообщений)
    @router.callback_query(F.data.startswith(("bksvc:", "bkdate:", "bkslot:")))
    async def on_stale_callback(callback: CallbackQuery) -> None:
        await callback.answer("Сессия устарела. Начните заново с /book.", show_alert=True)

    return router


class _SlotsClientProtocol(Protocol):
    async def get_slots(self, date_from: date, date_to: date, service_ids: list[UUID]) -> list[SlotWindow]:
        """Return slot list from backend."""


async def _refetch_slots(
    user_client: _SlotsClientProtocol, fsm_data: dict[str, Any], service_id: str
) -> list[SlotWindow]:
    """Повторно запросить слоты при конфликте 409."""
    try:
        chosen_date = date.fromisoformat(fsm_data.get("chosen_date", str(_today())))
        raw = await user_client.get_slots(chosen_date, chosen_date, [UUID(service_id)])
        return _filter_upcoming_slots(raw, chosen_date)
    except BackendError:
        return []
