"""Регистрация и вход через Telegram."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from pereobuyka.api.v1.deps_extra import SessionPg
from pereobuyka.api.v1.schemas import TelegramAuthRequest, WebAuthRequest
from pereobuyka.services.auth_user_pg import telegram_auth_pg, web_auth_pg

router = APIRouter(tags=["Auth"])


@router.post("/auth/telegram")
async def auth_telegram(session: SessionPg, body: TelegramAuthRequest) -> JSONResponse:
    """Вход / регистрация: upsert пользователя и выдача MVP-токена."""
    token_payload, created = await telegram_auth_pg(session, body)
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return JSONResponse(content=token_payload.model_dump(mode="json"), status_code=status_code)


@router.post("/auth/web")
async def auth_web(session: SessionPg, body: WebAuthRequest) -> JSONResponse:
    """Вход клиента в веб по telegram username (MVP)."""
    token_payload, created = await web_auth_pg(session, body)
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return JSONResponse(content=token_payload.model_dump(mode="json"), status_code=status_code)
