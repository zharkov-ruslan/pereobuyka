"""Репозитории PostgreSQL: услуги, записи, расписание (без ORM в ответах API)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Literal, cast
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pereobuyka.config import get_settings
from pereobuyka.db.models import (
    Appointment,
    AppointmentLine,
    ScheduleException,
    ScheduleRule,
    Service,
    User,
)
from pereobuyka.storage.memory import AppointmentRecord, ServiceLineItemDict, ServiceRecord


async def ensure_user_exists(session: AsyncSession, user_id: UUID) -> None:
    """Гарантировать строку users для FK записей (MVP: автосоздание «Клиент»)."""
    stmt = (
        pg_insert(User)
        .values(
            id=user_id,
            name="Клиент",
            phone=None,
            role="client",
            telegram_id=None,
            telegram_username=None,
            registered_at=datetime.now(UTC),
            source="web",
        )
        .on_conflict_do_nothing(index_elements=[User.id])
    )
    await session.execute(stmt)


async def fetch_services_map(
    session: AsyncSession, *, active_only: bool = True
) -> dict[UUID, ServiceRecord]:
    stmt = select(Service)
    if active_only:
        stmt = stmt.where(Service.is_active.is_(True))
    rows = (await session.scalars(stmt)).all()
    return {
        s.id: ServiceRecord(
            id=s.id,
            name=s.name,
            duration_minutes=s.duration_minutes,
            price=s.price,
            description=s.description or "",
            is_active=s.is_active,
        )
        for s in rows
    }


async def fetch_active_services_map(session: AsyncSession) -> dict[UUID, ServiceRecord]:
    """Только активные услуги (слоты, создание записи)."""
    return await fetch_services_map(session, active_only=True)


async def fetch_exceptions_by_date(session: AsyncSession) -> dict[date, ScheduleException]:
    rows = (await session.scalars(select(ScheduleException))).all()
    return {r.exception_date: r for r in rows}


async def fetch_schedule_by_weekday(session: AsyncSession) -> dict[int, tuple[time, time] | None]:
    """weekday → (start_time, end_time) или None если выходной / нет строки."""
    rows = (await session.scalars(select(ScheduleRule).order_by(ScheduleRule.weekday))).all()
    out: dict[int, tuple[time, time] | None] = {}
    for r in rows:
        if r.is_day_off:
            out[int(r.weekday)] = None
        else:
            out[int(r.weekday)] = (r.start_time, r.end_time)
    return out


async def list_appointments_non_cancelled(session: AsyncSession) -> list[AppointmentRecord]:
    stmt = (
        select(Appointment)
        .options(selectinload(Appointment.lines))
        .where(Appointment.status != "cancelled")
    )
    rows = (await session.scalars(stmt)).unique().all()
    records: list[AppointmentRecord] = []
    for a in rows:
        items = [
            ServiceLineItemDict(service_id=str(line.service_id), quantity=line.quantity)
            for line in a.lines
        ]
        st: Literal["scheduled", "completed", "cancelled"] = cast(
            Literal["scheduled", "completed", "cancelled"],
            a.status,
        )
        records.append(
            AppointmentRecord(
                id=a.id,
                user_id=a.user_id,
                starts_at=_as_utc_naive(a.starts_at),
                ends_at=_as_utc_naive(a.ends_at),
                total_price=a.total_price,
                status=st,
                created_at=_as_utc_naive(a.created_at),
                service_items=items,
            )
        )
    return records


def _as_utc_naive(dt: datetime) -> datetime:
    """Привести к naive UTC для совместимости со слотами и тестами (как in-memory)."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


async def insert_appointment(
    session: AsyncSession,
    *,
    appointment_id: UUID,
    user_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
    total_price: Decimal,
    status: str,
    created_at: datetime,
    service_items: list[ServiceLineItemDict],
    source: str = "web",
    discount_percent: int = 0,
    created_by_user_id: UUID | None = None,
) -> None:
    await ensure_user_exists(session, user_id)
    starts = _ensure_aware_utc(starts_at)
    ends = _ensure_aware_utc(ends_at)
    created = _ensure_aware_utc(created_at)
    ap = Appointment(
        id=appointment_id,
        user_id=user_id,
        starts_at=starts,
        ends_at=ends,
        total_price=total_price,
        status=status,
        created_at=created,
        source=source,
        discount_percent=discount_percent,
        created_by_user_id=created_by_user_id,
    )
    session.add(ap)
    await session.flush()
    for row in service_items:
        sid = UUID(row["service_id"])
        session.add(
            AppointmentLine(
                appointment_id=appointment_id,
                service_id=sid,
                quantity=row["quantity"],
            )
        )


def _ensure_aware_utc(dt: datetime) -> datetime:
    """Наивные часы в API — стена времени в зоне `consultation_business_timezone`."""
    if dt.tzinfo is not None:
        return dt.astimezone(UTC)
    tz_name = get_settings().consultation_business_timezone
    try:
        tz = ZoneInfo((tz_name or "Europe/Moscow").strip() or "Europe/Moscow")
    except Exception:
        tz = UTC
    return dt.replace(tzinfo=tz).astimezone(UTC)
