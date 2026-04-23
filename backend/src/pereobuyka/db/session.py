"""Async engine, session factory и зависимость FastAPI для PostgreSQL."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def is_postgres_database_url(url: str) -> bool:
    """True, если URL указывает на PostgreSQL (asyncpg), а не SQLite."""
    lowered = url.lower()
    return lowered.startswith("postgresql") and "sqlite" not in lowered


async def init_db_engine(database_url: str) -> None:
    """Создать async engine и sessionmaker (идемпотентно для PostgreSQL)."""
    global _engine, _session_factory
    if not is_postgres_database_url(database_url):
        return
    if _engine is not None:
        return
    if "+asyncpg" not in database_url:
        msg = "Для async SQLAlchemy ожидается DATABASE_URL с драйвером +asyncpg"
        raise ValueError(msg)
    _engine = create_async_engine(database_url, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info("Инициализирован async SQLAlchemy engine (PostgreSQL)")


async def dispose_db_engine() -> None:
    """Освободить пул соединений."""
    global _engine, _session_factory
    if _engine is None:
        return
    await _engine.dispose()
    _engine = None
    _session_factory = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        msg = (
            "Session factory недоступен: не PostgreSQL или lifespan ещё не выполнил init_db_engine."
        )
        raise RuntimeError(msg)
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    """Выдать сессию для запроса; для SQLite — None (роутеры используют in-memory)."""
    from pereobuyka.config import get_settings

    settings = get_settings()
    if not is_postgres_database_url(settings.database_url):
        yield None
        return
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise


def reset_engine_for_tests() -> None:
    """Сбросить глобальные ссылки на engine (только тесты / повторная инициализация)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
