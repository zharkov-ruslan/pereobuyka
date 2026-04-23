"""Alembic: синхронный движок psycopg из DATABASE_URL (asyncpg → psycopg)."""

from __future__ import annotations

import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

from alembic import context

load_dotenv()

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_sync_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://pereobuyka:pereobuyka@127.0.0.1:5432/pereobuyka",
    )
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg", 1)
    if "sqlite" in url:
        msg = (
            "Alembic миграции рассчитаны на PostgreSQL. "
            "Укажите DATABASE_URL=postgresql+asyncpg://... в .env (см. backend/.env.example)."
        )
        raise RuntimeError(msg)
    return url


def run_migrations_offline() -> None:
    url = get_sync_url()
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_sync_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
