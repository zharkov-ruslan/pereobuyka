"""Pytest: TestClient, авторизация, PostgreSQL через Testcontainers + Alembic + seed."""

from __future__ import annotations

import os

# Ryuk (reaper) на части конфигураций Windows/Docker даёт ошибку порта 8080 при старте.
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from pereobuyka.api.v1.deps import get_current_user
from pereobuyka.config import get_settings
from pereobuyka.db.session import reset_engine_for_tests
from pereobuyka.main import app

BACKEND_ROOT = Path(__file__).resolve().parent.parent

FAKE_USER_ID = UUID("00000000-0000-0000-0000-000000000099")

os.environ.setdefault("ADMIN_API_TOKEN", "test-admin-token")


def _to_asyncpg(url: str) -> str:
    """Преобразовать URL контейнера в asyncpg для SQLAlchemy."""
    u = url.strip()
    if "+asyncpg" in u:
        return u
    for prefix in ("postgresql+psycopg2://", "postgresql+psycopg://"):
        if u.startswith(prefix):
            u = "postgresql://" + u.split("://", 1)[1]
            break
    if u.startswith("postgresql://"):
        return "postgresql+asyncpg://" + u[len("postgresql://") :]
    raise ValueError(f"Неизвестный формат URL БД: {url[:60]}...")


def _to_psycopg_sync(async_url: str) -> str:
    return async_url.replace("+asyncpg", "+psycopg", 1)


@pytest.fixture(scope="session")
def postgres_connection_url() -> Generator[str, None, None]:
    """Один контейнер PostgreSQL на сессию: миграции Alembic и seed."""
    with PostgresContainer("postgres:16-alpine") as pg:
        raw = pg.get_connection_url()
        async_url = _to_asyncpg(raw)
        sync_url = _to_psycopg_sync(async_url)
        env = {**os.environ, "DATABASE_URL": sync_url}
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=BACKEND_ROOT,
            env=env,
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "pereobuyka.scripts.seed"],
            cwd=BACKEND_ROOT,
            env=env,
            check=True,
        )
        os.environ["DATABASE_URL"] = async_url
        get_settings.cache_clear()
        reset_engine_for_tests()
        yield async_url
    os.environ.pop("DATABASE_URL", None)
    get_settings.cache_clear()
    reset_engine_for_tests()


@pytest.fixture(scope="session")
def client(postgres_connection_url: str) -> Generator[TestClient, None, None]:
    """TestClient после настройки DATABASE_URL (lifespan поднимает async engine)."""
    assert postgres_connection_url  # порядок фикстур: контейнер до TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_override() -> Generator[UUID, None, None]:
    """Подменить get_current_user так, чтобы возвращался FAKE_USER_ID."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER_ID
    yield FAKE_USER_ID
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def truncate_appointments(postgres_connection_url: str) -> Generator[None, None, None]:
    """Пустить записи между тестами (каталог и расписание остаются от seed)."""
    sync_url = _to_psycopg_sync(postgres_connection_url)
    engine = create_engine(sync_url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE bonus_transactions, visit_lines, visits, "
                "appointment_services, appointments, bonus_accounts RESTART IDENTITY CASCADE"
            )
        )
    yield
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE bonus_transactions, visit_lines, visits, "
                "appointment_services, appointments, bonus_accounts RESTART IDENTITY CASCADE"
            )
        )
    engine.dispose()
