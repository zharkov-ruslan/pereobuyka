"""Handlers для просмотра и отмены записей клиента."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from pereobuyka.client.backend import BackendClient, BackendError, BackendUnavailableError

logger = logging.getLogger(__name__)


class CancelAppointmentCb(CallbackData, prefix="apcancel"):
    appointment_id: str


def _format_time(raw_iso: str) -> str:
    try:
        value = datetime.fromisoformat(raw_iso.replace("Z", "+00:00"))
    except ValueError:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M")


async def run_appointments_list(message: Message, backend: BackendClient) -> None:
    if message.from_user is None:
        return
    user_client = backend.for_user(message.from_user.id)
    try:
        appointments = await user_client.list_my_appointments(status="scheduled", limit=10)
    except BackendUnavailableError:
        await message.answer("Сервис временно недоступен. Попробуйте позже.")
        return
    except BackendError as exc:
        logger.error("Backend error in /appointments: %s", exc)
        await message.answer("Не удалось получить записи. Попробуйте позже.")
        return

    if not appointments:
        await message.answer("У вас нет активных записей.")
        return

    lines = ["Ваши активные записи:\n"]
    buttons: list[list[InlineKeyboardButton]] = []
    for item in appointments:
        appointment_id = str(item.get("id", ""))
        starts_at = _format_time(str(item.get("starts_at", "")))
        ends_at = _format_time(str(item.get("ends_at", "")))
        lines.append(f"• {starts_at} - {ends_at}, статус: {item.get('status')}")
        if appointment_id:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"Отменить {starts_at}",
                        callback_data=CancelAppointmentCb(appointment_id=appointment_id).pack(),
                    )
                ]
            )
    await message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
    )


def build_router(backend: BackendClient) -> Router:
    router = Router()

    @router.message(Command("appointments"))
    async def cmd_appointments(message: Message) -> None:
        await run_appointments_list(message, backend)

    @router.callback_query(CancelAppointmentCb.filter())
    async def on_cancel_appointment(callback: CallbackQuery, callback_data: CancelAppointmentCb) -> None:
        if callback.from_user is None:
            await callback.answer("Не удалось определить пользователя.", show_alert=True)
            return
        user_client = backend.for_user(callback.from_user.id)
        try:
            await user_client.cancel_appointment(callback_data.appointment_id)
        except BackendUnavailableError:
            await callback.answer("Сервис временно недоступен.", show_alert=True)
            return
        except BackendError as exc:
            if exc.status_code == 409:
                await callback.answer("Запись уже нельзя отменить.", show_alert=True)
                return
            logger.error("Backend error cancelling appointment: %s", exc)
            await callback.answer("Не удалось отменить запись.", show_alert=True)
            return

        await callback.answer("Запись отменена.")
        if callback.message is not None:
            await callback.message.answer("Запись успешно отменена. Обновите список: /appointments")

    return router
