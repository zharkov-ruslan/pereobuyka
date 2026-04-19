"""Создание записи на обслуживание.

Хранилище — временный in-memory слой; переход на SQLAlchemy/PostgreSQL
планируется в рамках database-tasklist.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from starlette.status import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_CONTENT

from pereobuyka.api.v1.schemas import Appointment, AppointmentCreateRequest, AppointmentStatus
from pereobuyka.storage.memory import (
    AppointmentRecord,
    ServiceLineItemDict,
    add_appointment,
    get_appointments,
    get_services,
)
from pereobuyka.utils import overlaps


def create_appointment(user_id: UUID, request: AppointmentCreateRequest) -> Appointment:
    """Создать запись на обслуживание.

    Проверяет существование услуг, отсутствие конфликта по времени,
    рассчитывает длительность и стоимость, сохраняет запись.

    Args:
        user_id: Идентификатор клиента.
        request: Параметры создаваемой записи (время начала, услуги).

    Returns:
        Созданная запись с рассчитанными полями.

    Raises:
        HTTPException(422): Если одна из услуг не найдена.
        HTTPException(409): Если запрошенный слот уже занят.
    """
    services = get_services()

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

    booked = [a for a in get_appointments() if a.status != "cancelled"]
    if any(overlaps(request.starts_at, ends_at, a.starts_at, a.ends_at) for a in booked):
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

    record = AppointmentRecord(
        id=appt_id,
        user_id=user_id,
        starts_at=request.starts_at,
        ends_at=ends_at,
        total_price=total_price,
        status="scheduled",
        created_at=now,
        service_items=[
            ServiceLineItemDict(service_id=str(item.service_id), quantity=item.quantity)
            for item in request.service_items
        ],
    )
    add_appointment(record)

    return Appointment(
        id=appt_id,
        user_id=user_id,
        starts_at=request.starts_at,
        ends_at=ends_at,
        total_price=f"{total_price:.2f}",
        status=AppointmentStatus.scheduled,
        created_at=now,
        service_items=request.service_items,
    )
