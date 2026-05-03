"""Регистрация / профиль пользователя (PostgreSQL)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pereobuyka.api.v1.schemas import (
    TelegramAuthRequest,
    TokenResponse,
    User,
    UserRole,
    UserSource,
    WebAuthRequest,
)
from pereobuyka.db.models import User as UserRow

_TELEGRAM_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def normalize_web_username(raw: str) -> str:
    s = raw.strip()
    if s.startswith("@"):
        s = s[1:]
    return s.lower()


async def telegram_auth_pg(
    session: AsyncSession, body: TelegramAuthRequest
) -> tuple[TokenResponse, bool]:
    """Upsert пользователя по telegram_id, детерминированный UUID как у deps.

    Второй элемент — True, если создана новая строка пользователя (ответ 201).
    """
    uid = uuid.uuid5(_TELEGRAM_NS, f"telegram:{body.telegram_id}")
    row = await session.scalar(select(UserRow).where(UserRow.telegram_id == body.telegram_id))
    now = datetime.now(UTC)
    created = False
    if row is None:
        created = True
        row = UserRow(
            id=uid,
            name=body.name,
            phone=body.phone,
            role="client",
            telegram_id=body.telegram_id,
            registered_at=now,
            source="telegram",
        )
        session.add(row)
        await session.flush()
    else:
        row.name = body.name
        row.phone = body.phone

    u = User(
        id=row.id,
        name=row.name,
        phone=row.phone,
        role=UserRole(row.role),
        telegram_id=row.telegram_id,
        telegram_username=getattr(row, "telegram_username", None),
        registered_at=_naive(row.registered_at),
        source=UserSource(row.source),
    )
    return TokenResponse(access_token=f"mvp-{row.id}", user=u), created


async def web_auth_pg(session: AsyncSession, body: WebAuthRequest) -> tuple[TokenResponse, bool]:
    """Upsert по telegram_username (MVP), детерминированный UUID."""
    normalized = normalize_web_username(body.telegram_username)
    uid = uuid.uuid5(_TELEGRAM_NS, f"web_username:{normalized}")
    row = await session.scalar(
        select(UserRow).where(UserRow.telegram_username == normalized),
    )
    now = datetime.now(UTC)
    created = False
    if row is None:
        existing = await session.get(UserRow, uid)
        if existing is None:
            created = True
            row = UserRow(
                id=uid,
                name=body.name or normalized,
                phone=body.phone,
                role="client",
                telegram_id=None,
                telegram_username=normalized,
                registered_at=now,
                source="web",
            )
            session.add(row)
            await session.flush()
        else:
            row = existing
            if row.telegram_username is None:
                row.telegram_username = normalized
            if body.name:
                row.name = body.name
            if body.phone is not None:
                row.phone = body.phone
            await session.flush()
    else:
        if body.name:
            row.name = body.name
        if body.phone is not None:
            row.phone = body.phone
        await session.flush()

    u = User(
        id=row.id,
        name=row.name,
        phone=row.phone,
        role=UserRole(row.role),
        telegram_id=row.telegram_id,
        telegram_username=row.telegram_username,
        registered_at=_naive(row.registered_at),
        source=UserSource(row.source),
    )
    return TokenResponse(access_token=f"mvp-{row.id}", user=u), created


async def get_me_pg(session: AsyncSession, user_id: UUID) -> User:
    row = await session.get(UserRow, user_id)
    if row is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Пользователь не найден"}},
        )
    return User(
        id=row.id,
        name=row.name,
        phone=row.phone,
        role=UserRole(row.role),
        telegram_id=row.telegram_id,
        telegram_username=getattr(row, "telegram_username", None),
        registered_at=_naive(row.registered_at),
        source=UserSource(row.source),
    )


def _naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)
