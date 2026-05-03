"""Идемпотентное начальное наполнение PostgreSQL для локальной разработки.

Повторный запуск не меняет уже существующие строки (ON CONFLICT DO NOTHING),
кроме случаев, когда явная политика — см. комментарии в run_seed().
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

import psycopg
from dotenv import load_dotenv

from pereobuyka.storage.memory import DEFAULT_SERVICE_ID

ADMIN_ACTOR_USER_ID = UUID("00000000-0000-0000-0000-0000000000aa")

# Демо-клиенты и сущности (идемпотентно по id)
DEMO_CLIENT_1 = UUID("10000000-0000-4000-8000-000000000001")
DEMO_CLIENT_2 = UUID("10000000-0000-4000-8000-000000000002")
DEMO_CLIENT_3 = UUID("10000000-0000-4000-8000-000000000003")
DEMO_APT_NEXT = UUID("20000000-0000-4000-8000-000000000001")
DEMO_APT_TG = UUID("20000000-0000-4000-8000-000000000002")
DEMO_APT_DONE = UUID("20000000-0000-4000-8000-000000000003")
DEMO_APT_WEB = UUID("20000000-0000-4000-8000-000000000004")
DEMO_APT_CANCEL = UUID("20000000-0000-4000-8000-000000000005")
DEMO_VISIT_1 = UUID("30000000-0000-4000-8000-000000000001")
DEMO_BONUS_1 = UUID("b0000001-0000-4000-8000-000000000001")
DEMO_BONUS_2 = UUID("b0000002-0000-4000-8000-000000000002")
DEMO_BONUS_3 = UUID("b0000003-0000-4000-8000-000000000003")
DEMO_CM_1 = UUID("c0000001-0000-4000-8000-000000000001")
DEMO_CM_2 = UUID("c0000002-0000-4000-8000-000000000002")


def _first_future_weekday_slot_local(tz: ZoneInfo, *, hour: int, minute: int = 0) -> datetime:
    """Ближайший будущий слот в будний день (Пн–Пт), не в прошлом."""
    now = datetime.now(tz)
    d = now.date()
    candidate = datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz)
    while candidate <= now or candidate.weekday() >= 5:
        d = d + timedelta(days=1)
        candidate = datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz)
    return candidate


def _utc_monday_start(tz: ZoneInfo) -> datetime:
    now = datetime.now(tz)
    day0 = now.date()
    days_back = day0.weekday()
    mon = day0 - timedelta(days=days_back)
    return datetime(mon.year, mon.month, mon.day, 0, 0, 0, tzinfo=tz)


def _seed_demo_bookings(cur) -> None:
    """Клиенты, записи на неделю, визит с оценками, бонусы, сообщения консультации."""
    tz = ZoneInfo("Europe/Moscow")
    monday = _utc_monday_start(tz)
    price = Decimal("2000.00")
    reg = datetime.now(UTC)

    # Слоты по дням текущей недели (Пн offset 0)
    def _utc_at(day_off: int, hour: int, minute: int) -> datetime:
        local = monday + timedelta(days=day_off, hours=hour, minutes=minute)
        return local.astimezone(UTC)

    slot_next = _first_future_weekday_slot_local(tz, hour=17, minute=0)
    starts_next = slot_next.astimezone(UTC)
    ends_next = starts_next + timedelta(minutes=60)

    starts_tg = _utc_at(1, 10, 0)
    ends_tg = starts_tg + timedelta(hours=1)
    starts_done = _utc_at(2, 11, 0)
    ends_done = starts_done + timedelta(hours=1)
    starts_web = _utc_at(3, 14, 0)
    ends_web = starts_web + timedelta(hours=1)
    starts_cx = _utc_at(4, 9, 30)
    ends_cx = starts_cx + timedelta(hours=1)

    demo_users_sql = """
        INSERT INTO users (id, name, phone, role, telegram_id, telegram_username,
            registered_at, source)
        VALUES (%s, %s, %s, 'client', NULL, %s, %s, 'telegram')
        ON CONFLICT (id) DO NOTHING
    """
    for uid, name, phone, uname in [
        (DEMO_CLIENT_1, "Клиент Анна", "+79001112221", "anna_demo"),
        (DEMO_CLIENT_2, "Клиент Борис", "+79001112222", "boris_demo"),
        (DEMO_CLIENT_3, "Клиент Вера", None, "vera_demo"),
    ]:
        cur.execute(demo_users_sql, (str(uid), name, phone, uname, reg))

    bonus_sql = """
        INSERT INTO bonus_accounts (id, user_id, balance)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    """
    cur.execute(bonus_sql, (str(DEMO_BONUS_1), str(DEMO_CLIENT_1), 80))
    cur.execute(bonus_sql, (str(DEMO_BONUS_2), str(DEMO_CLIENT_2), 120))
    cur.execute(bonus_sql, (str(DEMO_BONUS_3), str(DEMO_CLIENT_3), 0))

    ap_sql = """
        INSERT INTO appointments (id, user_id, starts_at, ends_at, total_price, status,
            created_at, source, discount_percent, created_by_user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """
    line_sql = """
        INSERT INTO appointment_services (appointment_id, service_id, quantity)
        VALUES (%s, %s, 1)
        ON CONFLICT (appointment_id, service_id) DO NOTHING
    """
    cre = reg
    rows = [
        (
            DEMO_APT_NEXT,
            DEMO_CLIENT_3,
            starts_next,
            ends_next,
            price,
            "scheduled",
            cre,
            "web",
            0,
            None,
        ),
        (
            DEMO_APT_TG,
            DEMO_CLIENT_1,
            starts_tg,
            ends_tg,
            price,
            "scheduled",
            cre,
            "telegram_bot",
            10,
            None,
        ),
        (
            DEMO_APT_DONE,
            DEMO_CLIENT_2,
            starts_done,
            ends_done,
            price,
            "completed",
            cre,
            "llm",
            0,
            None,
        ),
        (
            DEMO_APT_WEB,
            DEMO_CLIENT_1,
            starts_web,
            ends_web,
            price,
            "scheduled",
            cre,
            "web",
            0,
            None,
        ),
        (
            DEMO_APT_CANCEL,
            DEMO_CLIENT_3,
            starts_cx,
            ends_cx,
            price,
            "cancelled",
            cre,
            "admin",
            15,
            str(ADMIN_ACTOR_USER_ID),
        ),
    ]
    for row in rows:
        cur.execute(
            ap_sql,
            (
                str(row[0]),
                str(row[1]),
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                row[7],
                row[8],
                row[9],
            ),
        )
        cur.execute(line_sql, (str(row[0]), str(DEFAULT_SERVICE_ID)))

    visit_sql = """
        INSERT INTO visits (id, appointment_id, total_amount, bonus_spent, bonus_earned,
            confirmed_at, confirmed_by_user_id,
            client_rating_stars, client_rating_comment,
            service_rating_stars, service_rating_comment)
        VALUES (%s, %s, %s, 0, 50, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """
    vline_sql = """
        INSERT INTO visit_lines (visit_id, service_id, quantity)
        VALUES (%s, %s, 1)
        ON CONFLICT (visit_id, service_id) DO NOTHING
    """
    cur.execute(
        visit_sql,
        (
            str(DEMO_VISIT_1),
            str(DEMO_APT_DONE),
            price,
            ends_done,
            str(ADMIN_ACTOR_USER_ID),
            5,
            "Отлично",
            4,
            "Быстро",
        ),
    )
    cur.execute(vline_sql, (str(DEMO_VISIT_1), str(DEFAULT_SERVICE_ID)))

    cm_sql = """
        INSERT INTO consultation_messages (id, user_id, role, content, created_at, request_id)
        VALUES (%s, %s, %s, %s, %s, NULL)
        ON CONFLICT (id) DO NOTHING
    """
    cur.execute(
        cm_sql,
        (
            str(DEMO_CM_1),
            str(DEMO_CLIENT_1),
            "user",
            "Есть ли окна на завтра?",
            reg - timedelta(minutes=10),
        ),
    )
    cur.execute(
        cm_sql,
        (
            str(DEMO_CM_2),
            str(DEMO_CLIENT_1),
            "assistant",
            "Проверьте слоты через каталог или запись на сайте.",
            reg - timedelta(minutes=9),
        ),
    )


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
            _seed_demo_bookings(cur)
        conn.commit()
    print(
        "Seed выполнен (loyalty_settings, users/admin, services, schedule_rules; "
        "демо-клиенты, записи, визит, консультации)."
    )


def main() -> None:
    run_seed()


if __name__ == "__main__":
    main()
