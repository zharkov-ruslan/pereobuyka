"""Идемпотентное начальное наполнение PostgreSQL для локальной разработки.

Повторный запуск не меняет уже существующие строки (ON CONFLICT DO NOTHING),
кроме случаев, когда явная политика — см. комментарии в run_seed().
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, time
from decimal import Decimal
from uuid import UUID

import psycopg
from dotenv import load_dotenv

from pereobuyka.storage.memory import DEFAULT_SERVICE_ID

ADMIN_ACTOR_USER_ID = UUID("00000000-0000-0000-0000-0000000000aa")


def _sync_conninfo() -> str:
    load_dotenv()
    raw = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://pereobuyka:pereobuyka@127.0.0.1:5432/pereobuyka",
    )
    if "sqlite" in raw:
        print(
            "Seed рассчитан на PostgreSQL. Укажите в .env "
            "DATABASE_URL=postgresql+asyncpg://... (см. backend/.env.example).",
            file=sys.stderr,
        )
        raise SystemExit(1)
    for marker in ("postgresql+asyncpg://", "postgresql+psycopg://"):
        if raw.startswith(marker):
            return "postgresql://" + raw.split("://", 1)[1]
    if raw.startswith("postgresql://"):
        return raw
    msg = f"Неподдерживаемый DATABASE_URL для seed: {raw[:40]}..."
    raise ValueError(msg)


def run_seed() -> None:
    """Вставить эталонные строки: лояльность, расписание (как WORKING_HOURS), одна услуга."""
    conninfo = _sync_conninfo()
    price = Decimal("2000.00")

    loyalty_sql = """
        INSERT INTO loyalty_settings (id, max_bonus_spend_percent, earn_percent_after_visit)
        VALUES (1, 30, 5)
        ON CONFLICT (id) DO NOTHING
    """

    service_sql = """
        INSERT INTO services (id, name, description, price, duration_minutes, is_active)
        VALUES (%s, %s, %s, %s, %s, true)
        ON CONFLICT (id) DO NOTHING
    """

    rule_sql = """
        INSERT INTO schedule_rules (weekday, start_time, end_time, is_day_off)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (weekday) DO NOTHING
    """

    admin_user_sql = """
        INSERT INTO users (id, name, phone, role, telegram_id, registered_at, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """

    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            cur.execute(loyalty_sql)
            cur.execute(
                admin_user_sql,
                (
                    str(ADMIN_ACTOR_USER_ID),
                    "Администратор",
                    None,
                    "admin",
                    None,
                    datetime.now(UTC),
                    "web",
                ),
            )
            cur.execute(
                service_sql,
                (
                    str(DEFAULT_SERVICE_ID),
                    "Замена резины",
                    "Базовая услуга MVP; совпадает с in-memory каталогом.",
                    price,
                    60,
                ),
            )
            open_t = time(9, 0)
            close_t = time(18, 0)
            for weekday in range(7):
                is_off = weekday > 4
                cur.execute(
                    rule_sql,
                    (weekday, open_t, close_t, is_off),
                )
        conn.commit()
    print("Seed выполнен (loyalty_settings, users/admin, services, schedule_rules).")


def main() -> None:
    run_seed()


if __name__ == "__main__":
    main()
