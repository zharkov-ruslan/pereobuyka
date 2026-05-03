"""Команда /ask — LLM-консультант: можно задать вопрос в одном сообщении или «жить в диалоге»."""

from __future__ import annotations

import io
import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from pereobuyka.bot.ask_history import append_ask_turn, get_ask_history
from pereobuyka.bot.keyboards import main_menu_reply
from pereobuyka.client.backend import BackendClient, BackendError, BackendUnavailableError

logger = logging.getLogger(__name__)

_MAX_LEN = 4000

_MODE_INTRO = (
    "Пишите как обычно (без /ask), или пользуйтесь кнопками. "
    "Завершить: «Завершить консультацию» или /ask_stop. "
    "Команды /book, /services — как раньше."
)


class ConsultationStates(StatesGroup):
    """Пользователь в беседе с LLM, может писать без префикса /ask."""

    chatting = State()


def extract_ask_text(message_text: str | None) -> str | None:
    """Достать текст вопроса после ``/ask`` (учитывает ``/ask@bot``). None = пусто после команды."""
    if not message_text:
        return None
    m = re.match(r"^/ask(?:@[\w_]+)?(?:\s+(.+))?$", message_text.strip(), flags=re.DOTALL)
    if not m:
        return None
    tail = (m.group(1) or "").strip()
    return tail or None


class _TextIsNotACommandFilter(BaseFilter):
    """Сообщение — текст, не команда (чтобы /book в режиме чата ушли в чужой хендлер)."""

    async def __call__(self, message: Message) -> bool:
        t = (message.text or "").lstrip()
        if not t:
            return False
        return not t.startswith("/")


async def _call_consultation(
    user_id: int,
    question: str,
    backend: BackendClient,
) -> tuple[str, bool]:
    """Ответ (текст, успех). При ошибке — (сообщение пользователю, False)."""
    user_client = backend.for_user(user_id)
    history = get_ask_history(user_id)
    try:
        resp = await user_client.send_consultation(question, history=history)
    except BackendUnavailableError:
        return "Сервис временно недоступен. Попробуйте позже.", False
    except BackendError as exc:
        if exc.status_code == 503 and exc.code == "SERVICE_UNAVAILABLE":
            # Бэкенд кладёт причину в error.message (таймаут LLM, нет ключа, лимит и т.д.)
            detail = (exc.message or "").strip()
            if detail:
                return detail, False
            return "Консультант временно недоступен. Попробуйте позже.", False
        logger.error("Backend error in /ask: %s", exc)
        return "Не удалось получить ответ. Попробуйте позже.", False

    reply = (resp.get("reply") or "").strip() or "Пустой ответ."
    append_ask_turn(user_id, question, reply)
    return reply, True


async def enter_consultation_welcome(message: Message, state: FSMContext) -> None:
    """Как /ask без текста: режим LLM, ждём вопрос (кнопка «Вопрос консультанту»)."""
    if message.from_user is None:
        return
    await state.set_state(ConsultationStates.chatting)
    await message.answer(
        "Напишите ваш вопрос. " + _MODE_INTRO,
        reply_markup=main_menu_reply(in_consultation=True),
    )


async def do_ask_stop(message: Message, state: FSMContext) -> None:
    await state.clear()
    if message.from_user is not None:
        await message.answer(
            "Режим консультанта выключен. Снова: /ask или кнопка «Вопрос консультанту».",
            reply_markup=main_menu_reply(in_consultation=False),
        )


def build_router(backend: BackendClient) -> Router:
    router = Router()

    @router.message(Command("ask"))
    async def cmd_ask(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        user_id = message.from_user.id

        question = extract_ask_text(message.text)
        if not question:
            await enter_consultation_welcome(message, state)
            return
        if len(question) > _MAX_LEN:
            await message.answer(
                f"Слишком длинный вопрос (максимум {_MAX_LEN} символов).",
                reply_markup=main_menu_reply(in_consultation=False),
            )
            return

        await state.set_state(ConsultationStates.chatting)
        text, _ok = await _call_consultation(user_id, question, backend)
        await message.answer(text, reply_markup=main_menu_reply(in_consultation=True))

    @router.message(Command("ask_stop"))
    async def cmd_ask_stop(message: Message, state: FSMContext) -> None:
        await do_ask_stop(message, state)

    @router.message(StateFilter(ConsultationStates.chatting), _TextIsNotACommandFilter())
    async def in_consultation_text(message: Message) -> None:
        if message.from_user is None:
            return
        q = (message.text or "").strip()
        if not q:
            return
        if len(q) > _MAX_LEN:
            await message.answer(
                f"Слишком длинно (максимум {_MAX_LEN} символов).",
                reply_markup=main_menu_reply(in_consultation=True),
            )
            return
        text, _ok = await _call_consultation(message.from_user.id, q, backend)
        await message.answer(text, reply_markup=main_menu_reply(in_consultation=True))

    @router.message(StateFilter(ConsultationStates.chatting), F.voice)
    async def in_consultation_voice(message: Message, bot: Bot) -> None:
        if message.from_user is None or message.voice is None:
            return
        user_id = message.from_user.id
        voice = message.voice
        buf = io.BytesIO()
        try:
            await bot.download(voice, destination=buf)
        except Exception:
            logger.exception("Failed to download voice message")
            await message.answer(
                "Не удалось загрузить голосовое сообщение. Напишите текстом или попробуйте ещё раз.",
                reply_markup=main_menu_reply(in_consultation=True),
            )
            return
        raw = buf.getvalue()
        if not raw:
            await message.answer(
                "Пустое аудио. Запишите ещё раз или напишите текстом.",
                reply_markup=main_menu_reply(in_consultation=True),
            )
            return

        user_client = backend.for_user(user_id)
        ext = "ogg" if (voice.mime_type and "ogg" in voice.mime_type) else "oga"
        fname = f"{voice.file_unique_id}.{ext}"
        ctype = voice.mime_type
        try:
            question = await user_client.transcribe_voice(
                raw, filename=fname, content_type=ctype
            )
        except BackendUnavailableError:
            await message.answer(
                "Сервис временно недоступен. Попробуйте позже или напишите текстом.",
                reply_markup=main_menu_reply(in_consultation=True),
            )
            return
        except BackendError as exc:
            if exc.status_code == 503:
                await message.answer(
                    "Распознавание голоса временно недоступно. Напишите вопрос текстом.",
                    reply_markup=main_menu_reply(in_consultation=True),
                )
                return
            logger.error("STT backend error: %s", exc)
            await message.answer(
                "Не удалось распознать голос. Напишите вопрос текстом.",
                reply_markup=main_menu_reply(in_consultation=True),
            )
            return

        question = (question or "").strip()
        if not question:
            await message.answer(
                "Не удалось распознать речь. Повторите запись или напишите текстом.",
                reply_markup=main_menu_reply(in_consultation=True),
            )
            return
        if len(question) > _MAX_LEN:
            await message.answer(
                f"Распознанный текст слишком длинный (максимум {_MAX_LEN} символов). "
                "Сократите вопрос.",
                reply_markup=main_menu_reply(in_consultation=True),
            )
            return

        text, _ok = await _call_consultation(user_id, question, backend)
        await message.answer(text, reply_markup=main_menu_reply(in_consultation=True))

    return router
