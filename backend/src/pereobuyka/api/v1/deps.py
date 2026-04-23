"""Зависимости авторизации API v1."""

import uuid
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import HTTP_401_UNAUTHORIZED

from pereobuyka.config import get_settings

_bearer = HTTPBearer(auto_error=False)

# Пространство имён для детерминированных UUID пользователей Telegram
_TELEGRAM_USER_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    x_telegram_user_id: str | None = Header(default=None),
) -> UUID:
    """Зависимость авторизации.

    Поддерживает авторизацию бота через BOT_SECRET:
    - Заголовок ``Authorization: Bearer <BOT_SECRET>``
    - Заголовок ``X-Telegram-User-Id: <telegram_id>`` → UUID через uuid5

    Если BOT_SECRET не задан или токен не совпадает — 401.
    Полноценная JWT / Telegram initData валидация реализуется в auth-tasklist.

    Raises:
        HTTPException(401): Токен отсутствует или не прошёл валидацию.
    """
    if credentials is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Токен не предоставлен"}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw = credentials.credentials

    # MVP-токен после POST /auth/telegram: «mvp-<uuid пользователя>»
    if raw.startswith("mvp-"):
        try:
            return UUID(raw.removeprefix("mvp-"))
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "UNAUTHORIZED", "message": "Неверный формат токена"}},
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    settings = get_settings()
    if settings.bot_secret and raw == settings.bot_secret:
        if x_telegram_user_id:
            return uuid.uuid5(_TELEGRAM_USER_NS, f"telegram:{x_telegram_user_id}")
        return uuid.uuid5(_TELEGRAM_USER_NS, "bot")

    # TODO(auth-tasklist): реализовать проверку JWT / Telegram initData
    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "UNAUTHORIZED", "message": "Авторизация не реализована"}},
        headers={"WWW-Authenticate": "Bearer"},
    )
