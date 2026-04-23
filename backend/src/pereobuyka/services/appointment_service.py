"""Создание записи на обслуживание."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_CONTENT

from pereobuyka.api.v1.schemas import Appointment, AppointmentCreateRequest, AppointmentStatus
from pereobuyka.storage.memory import (
    AppointmentRecord,
    ServiceLineItemDict,
    add_appointment,
    get_appointments,
    get_services,
)
from pereobuyka.storage.postgres_repos import (
    fetch_active_services_map,
    insert_appointment,
    list_appointments_non_cancelled,
)
from pereobuyka.utils import overlaps


def _normalize_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


async def create_appointment(
    session: AsyncSession | None,
    user_id: UUID,
    request: AppointmentCreateRequest,
) -> Appointment:
    """Создать запись: PostgreSQL при переданной сессии, иначе in-memory (SQLite dev)."""
    if session is not None:
        services = await fetch_active_services_map(session)
        booked = await list_appointments_non_cancelled(session)
    else:
        services = get_services()
        booked = [a for a in get_appointments() if a.status != "cancelled"]

    for item in request.service_items:
        if item.service_id not in services:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": {
                        "code": "SERVICE_NOT_FOUND",
                        "message": f"Услуга {item.service_id} не найдена",
                    }
                },
            )

    total_minutes = sum(
        services[item.service_id].duration_minutes * item.quantity for item in request.service_items
    )
    total_price = sum(
        (services[item.service_id].price * item.quantity for item in request.service_items),
        Decimal(0),
    )

    ends_at = request.starts_at + timedelta(minutes=total_minutes)
    slot_st = _normalize_naive_utc(request.starts_at)
    slot_e = _normalize_naive_utc(ends_at)

    if any(
        overlaps(
            slot_st,
            slot_e,
            _normalize_naive_utc(a.starts_at),
            _normalize_naive_utc(a.ends_at),
        )
        for a in booked
    ):
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "SLOT_NOT_AVAILABLE",
                    "message": "Выбранный слот уже занят",
                }
            },
        )

    now = datetime.now(UTC)
    appt_id = uuid4()
    items = [
        ServiceLineItemDict(service_id=str(item.service_id), quantity=item.quantity)
        for item in request.service_items
    ]

    if session is not None:
        await insert_appointment(
            session,
            appointment_id=appt_id,
            user_id=user_id,
            starts_at=request.starts_at,
            ends_at=ends_at,
            total_price=total_price,
            status="scheduled",
            created_at=now,
            service_items=items,
        )
    else:
        record = AppointmentRecord(
            id=appt_id,
            user_id=user_id,
            starts_at=slot_st,
            ends_at=slot_e,
            total_price=total_price,
            status="scheduled",
            created_at=_normalize_naive_utc(now),
            service_items=items,
        )
        add_appointment(record)

    return Appointment(
        id=appt_id,
        user_id=user_id,
        starts_at=slot_st,
        ends_at=slot_e,
        total_price=f"{total_price:.2f}",
        status=AppointmentStatus.scheduled,
        created_at=_normalize_naive_utc(now),
        service_items=request.service_items,
    )
