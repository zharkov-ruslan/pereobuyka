"""Расчёт свободных слотов по расписанию и занятым записям."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from pereobuyka.api.v1.schemas import SlotWindow
from pereobuyka.db.models import ScheduleException as ScheduleExceptionRow
from pereobuyka.storage.memory import (
    SLOT_STEP_MINUTES,
    WORKING_HOURS,
    AppointmentRecord,
    ServiceRecord,
    get_appointments,
    get_services,
)
from pereobuyka.storage.postgres_repos import (
    fetch_active_services_map,
    fetch_exceptions_by_date,
    fetch_schedule_by_weekday,
    list_appointments_non_cancelled,
)
from pereobuyka.utils import overlaps


def _memory_weekday_schedule() -> dict[int, tuple[time, time] | None]:
    """Расписание как в legacy `WORKING_HOURS` (только часы)."""
    out: dict[int, tuple[time, time] | None] = {}
    for w in range(7):
        if w in WORKING_HOURS:
            h0, h1 = WORKING_HOURS[w]
            out[w] = (time(h0, 0), time(h1, 0))
        else:
            out[w] = None
    return out


def compute_free_slots(
    date_from: date,
    date_to: date,
    service_ids: list[UUID],
    services: dict[UUID, ServiceRecord],
    appointments: list[AppointmentRecord],
    weekday_schedule: dict[int, tuple[time, time] | None],
    exceptions_by_date: dict[date, ScheduleExceptionRow] | None = None,
) -> list[SlotWindow]:
    """Построить список свободных окон (наивные datetime, как в MVP in-memory)."""
    total_minutes = sum(services[sid].duration_minutes for sid in service_ids if sid in services)
    if total_minutes == 0:
        return []

    booked = [a for a in appointments if a.status != "cancelled"]
    slots: list[SlotWindow] = []

    exceptions_by_date = exceptions_by_date or {}

    current = date_from
    while current <= date_to:
        ex = exceptions_by_date.get(current)
        if ex is not None:
            if ex.is_day_off:
                current += timedelta(days=1)
                continue
            open_t, close_t = ex.start_time, ex.end_time
        else:
            window = weekday_schedule.get(current.weekday())
            if window is None:
                current += timedelta(days=1)
                continue
            open_t, close_t = window
        slot_start = datetime.combine(current, open_t)
        day_end = datetime.combine(current, close_t)
        while True:
            slot_end = slot_start + timedelta(minutes=total_minutes)
            if slot_end > day_end:
                break
            if not any(overlaps(slot_start, slot_end, a.starts_at, a.ends_at) for a in booked):
                slots.append(SlotWindow(starts_at=slot_start, ends_at=slot_end))
            slot_start += timedelta(minutes=SLOT_STEP_MINUTES)
        current += timedelta(days=1)

    return slots


async def get_free_slots(
    session: AsyncSession | None,
    date_from: date,
    date_to: date,
    service_ids: list[UUID],
) -> list[SlotWindow]:
    """Свободные слоты: PostgreSQL через `session`, иначе in-memory."""
    if session is not None:
        services = await fetch_active_services_map(session)
        appointments = await list_appointments_non_cancelled(session)
        schedule = await fetch_schedule_by_weekday(session)
        exc_map = await fetch_exceptions_by_date(session)
    else:
        services = get_services()
        appointments = list(get_appointments())
        schedule = _memory_weekday_schedule()
        exc_map = {}
    return compute_free_slots(
        date_from,
        date_to,
        service_ids,
        services,
        appointments,
        schedule,
        exc_map if session is not None else None,
    )
