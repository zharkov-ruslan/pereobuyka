"""Дополнительные зависимости: PostgreSQL-only, админ-токен."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_403_FORBIDDEN, HTTP_503_SERVICE_UNAVAILABLE

from pereobuyka.api.v1.deps import _bearer
from pereobuyka.config import get_settings
from pereobuyka.db.session import get_db_session


async def require_postgres_session(
    session: Annotated[AsyncSession | None, Depends(get_db_session)],
) -> AsyncSession:
    """Отказ без PostgreSQL (режим SQLite / in-memory не поддерживает полный этап 1)."""
    if session is None:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "STORAGE_UNAVAILABLE",
                    "message": "Операция доступна только при DATABASE_URL PostgreSQL.",
                },
            },
        )
    return session


SessionPg = Annotated[AsyncSession, Depends(require_postgres_session)]


async def get_admin_actor_uuid(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UUID:
    """Bearer должен совпасть с settings.admin_api_token и не быть пустым."""
    settings = get_settings()
    token = getattr(settings, "admin_api_token", "") or ""
    if not token or credentials is None or credentials.credentials != token:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Требуются права администратора"}},
        )
    return settings.admin_actor_user_id


AdminActor = Annotated[UUID, Depends(get_admin_actor_uuid)]
