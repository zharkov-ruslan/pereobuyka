"""Расчёт свободных слотов по расписанию и занятым записям.

Хранилище — временный in-memory слой; переход на SQLAlchemy/PostgreSQL
планируется в рамках database-tasklist.
"""

from datetime import date, datetime, timedelta
from uuid import UUID

from pereobuyka.api.v1.schemas import SlotWindow
from pereobuyka.storage.memory import (
    SLOT_STEP_MINUTES,
    WORKING_HOURS,
    get_appointments,
    get_services,
)
from pereobuyka.utils import overlaps


def get_free_slots(
    date_from: date,
    date_to: date,
    service_ids: list[UUID],
) -> list[SlotWindow]:
    """Вернуть список свободных окон для набора услуг в диапазоне дат.

    Args:
        date_from: Начало диапазона поиска (включительно).
        date_to: Конец диапазона поиска (включительно).
        service_ids: Идентификаторы услуг; неизвестные услуги игнорируются.

    Returns:
        Список свободных временных окон, отсортированных по возрастанию.
    """
    services = get_services()
    total_minutes = sum(services[sid].duration_minutes for sid in service_ids if sid in services)
    if total_minutes == 0:
        return []

    booked = [a for a in get_appointments() if a.status != "cancelled"]
    slots: list[SlotWindow] = []

    current = date_from
    while current <= date_to:
        weekday = current.weekday()
        if weekday in WORKING_HOURS:
            open_h, close_h = WORKING_HOURS[weekday]
            slot_start = datetime(current.year, current.month, current.day, open_h)
            day_end = datetime(current.year, current.month, current.day, close_h)
            while True:
                slot_end = slot_start + timedelta(minutes=total_minutes)
                if slot_end > day_end:
                    break
                if not any(overlaps(slot_start, slot_end, a.starts_at, a.ends_at) for a in booked):
                    slots.append(SlotWindow(starts_at=slot_start, ends_at=slot_end))
                slot_start += timedelta(minutes=SLOT_STEP_MINUTES)
        current += timedelta(days=1)

    return slots
