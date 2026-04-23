"""Постоянные клавиатуры: подписи = menu_text; в режиме LLM вместо «Вопрос…» — «Завершить…»."""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from pereobuyka.bot.menu_text import (
    BTN_APPOINTMENTS,
    BTN_ASK,
    BTN_BONUS,
    BTN_BOOK,
    BTN_CATALOG,
    BTN_CONSULT_END,
    BTN_VISITS,
)


def main_menu_reply(*, in_consultation: bool = False) -> ReplyKeyboardMarkup:
    """Пока консультация не идёт — видна кнопка «Вопрос консультанту»; во время — «Завершить консультацию»."""
    third_right = BTN_CONSULT_END if in_consultation else BTN_ASK
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CATALOG), KeyboardButton(text=BTN_BOOK)],
            [KeyboardButton(text=BTN_APPOINTMENTS), KeyboardButton(text=BTN_BONUS)],
            [KeyboardButton(text=BTN_VISITS), KeyboardButton(text=third_right)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Сообщение боту или кнопка",
    )
