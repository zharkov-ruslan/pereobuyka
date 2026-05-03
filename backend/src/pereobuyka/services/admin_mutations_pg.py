"""Изменение записей/визитов администратором и выставление оценок."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_409_CONFLICT

from pereobuyka.api.v1.schemas import (
    AdminAppointmentPatchBody,
    AdminClientRow,
    AdminVisitPatchBody,
    ServiceLineItem,
)
from pereobuyka.api.v1.schemas import (
    Appointment as AppointmentOut,
)
from pereobuyka.api.v1.schemas import (
    Visit as VisitOut,
)
from pereobuyka.config import get_settings
from pereobuyka.db.models import Appointment, AppointmentLine, Visit, VisitLine
from pereobuyka.db.models import User as UserRow
from pereobuyka.services.api_adapters import appointment_from_orm, visit_from_orm
from pereobuyka.services.appointment_service import ensure_starts_at_not_in_past
from pereobuyka.storage.postgres_repos import (
    _as_utc_naive,
    fetch_active_services_map,
    insert_appointment,
    list_appointments_non_cancelled,
)
from pereobuyka.utils import overlaps, to_utc_naive_overlap


async def patch_appointment_admin(
    session: AsyncSession,
    *,
    appointment_id: UUID,
    body: AdminAppointmentPatchBody,
) -> AppointmentOut:
    ap = await session.get(Appointment, appointment_id)
    if ap is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Запись не найдена"}},
        )

    if body.status is not None:
        ap.status = body.status.value

    if body.source is not None:
        ap.source = body.source.value

    if body.discount_percent is not None:
        ap.discount_percent = body.discount_percent

    if body.service_items is not None:
        services = await fetch_active_services_map(session)
        for item in body.service_items:
            if item.service_id not in services:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": {
                            "code": "SERVICE_NOT_FOUND",
                            "message": f"Услуга {item.service_id} не найдена",
                        }
                    },
                )
        total_minutes = sum(
            services[i.service_id].duration_minutes * i.quantity for i in body.service_items
        )
        subtotal = sum(
            (services[i.service_id].price * i.quantity for i in body.service_items),
            Decimal(0),
        )
        disc = (
            int(body.discount_percent)
            if body.discount_percent is not None
            else int(ap.discount_percent)
        )
        ap.discount_percent = disc
        total_price = (subtotal * Decimal(100 - disc) / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        ends_at = ap.starts_at + timedelta(minutes=total_minutes)
        ap.ends_at = ends_at
        ap.total_price = total_price

        await session.execute(
            delete(AppointmentLine).where(AppointmentLine.appointment_id == ap.id)
        )
        for item in body.service_items:
            session.add(
                AppointmentLine(
                    appointment_id=ap.id,
                    service_id=item.service_id,
                    quantity=item.quantity,
                )
            )

        booked = await list_appointments_non_cancelled(session)
        slot_st = _as_utc_naive(ap.starts_at)
        slot_e = _as_utc_naive(ends_at)
        for other in booked:
            if other.id == ap.id:
                continue
            if overlaps(
                slot_st,
                slot_e,
                _as_utc_naive(other.starts_at),
                _as_utc_naive(other.ends_at),
            ):
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "SLOT_NOT_AVAILABLE",
                            "message": "После изменения запись пересекается с другой",
                        }
                    },
                )

    elif body.discount_percent is not None:
        await session.refresh(ap, attribute_names=["lines"])
        services_map = await fetch_active_services_map(session)
        subtotal = Decimal(0)
        for line in ap.lines:
            s = services_map.get(line.service_id)
            if s is None:
                raise HTTPException(
                    status_code=422,
                    detail={"error": {"code": "SERVICE_NOT_FOUND", "message": "Услуга в записи"}},
                )
            subtotal += s.price * line.quantity
        disc = int(body.discount_percent)
        total_price = (subtotal * Decimal(100 - disc) / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        ap.discount_percent = disc
        ap.total_price = total_price

    await session.flush()
    await session.refresh(ap, attribute_names=["lines"])
    return appointment_from_orm(ap)


async def create_client_quick_admin(
    session: AsyncSession,
    *,
    name: str,
    phone: str | None,
) -> AdminClientRow:
    uid = uuid4()
    now = datetime.now(UTC)
    clean_phone = phone.strip() if phone and phone.strip() else None
    row = UserRow(
        id=uid,
        name=name.strip(),
        phone=clean_phone,
        role="client",
        telegram_id=None,
        telegram_username=None,
        registered_at=now,
        source="web",
    )
    session.add(row)
    await session.flush()
    return AdminClientRow(
        user_id=uid,
        name=row.name,
        phone=row.phone,
        telegram_id=None,
        telegram_username=None,
        visits_count=0,
        total_spent="0.00",
        bonus_balance=0,
        rating_avg=None,
    )


async def create_appointment_admin(
    session: AsyncSession,
    *,
    admin_user_id: UUID,
    user_id: UUID,
    starts_at: datetime,
    service_items: list[ServiceLineItem],
    discount_percent: int,
) -> AppointmentOut:
    if not service_items:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Нужна хотя бы одна услуга",
                },
            },
        )

    ensure_starts_at_not_in_past(starts_at)

    client = await session.get(UserRow, user_id)
    if client is None or client.role != "client":
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Клиент не найден"}},
        )

    services = await fetch_active_services_map(session)
    for item in service_items:
        if item.service_id not in services:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "SERVICE_NOT_FOUND",
                        "message": f"Услуга {item.service_id} не найдена",
                    },
                },
            )

    total_minutes = sum(services[i.service_id].duration_minutes * i.quantity for i in service_items)
    subtotal = sum(
        (services[i.service_id].price * i.quantity for i in service_items),
        Decimal(0),
    )
    disc = min(max(int(discount_percent), 0), 100)
    total_price = (subtotal * Decimal(100 - disc) / Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    ends_at = starts_at + timedelta(minutes=total_minutes)

    tz_name = get_settings().consultation_business_timezone
    slot_st = to_utc_naive_overlap(starts_at, tz_name)
    slot_e = to_utc_naive_overlap(ends_at, tz_name)

    booked = await list_appointments_non_cancelled(session)
    for other in booked:
        if overlaps(
            slot_st,
            slot_e,
            _as_utc_naive(other.starts_at),
            _as_utc_naive(other.ends_at),
        ):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "SLOT_NOT_AVAILABLE",
                        "message": "Выбранный слот уже занят",
                    },
                },
            )

    appt_id = uuid4()
    now = datetime.now(UTC)
    item_rows = [
        {"service_id": str(item.service_id), "quantity": item.quantity} for item in service_items
    ]

    await insert_appointment(
        session,
        appointment_id=appt_id,
        user_id=user_id,
        starts_at=starts_at,
        ends_at=ends_at,
        total_price=total_price,
        status="scheduled",
        created_at=now,
        service_items=item_rows,
        source="admin",
        discount_percent=disc,
        created_by_user_id=admin_user_id,
    )
    await session.flush()
    ap = await session.get(Appointment, appt_id)
    if ap is None:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL", "message": "Не удалось создать запись"}},
        )
    await session.refresh(ap, attribute_names=["lines"])
    return appointment_from_orm(ap)


async def patch_visit_admin(
    session: AsyncSession,
    *,
    visit_id: UUID,
    body: AdminVisitPatchBody,
) -> VisitOut:
    v = await session.get(Visit, visit_id)
    if v is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Визит не найден"}},
        )

    if body.total_amount is not None:
        v.total_amount = Decimal(body.total_amount).quantize(Decimal("0.01"))
    if body.bonus_spent is not None:
        v.bonus_spent = body.bonus_spent
    if body.bonus_earned is not None:
        v.bonus_earned = body.bonus_earned

    if body.lines is not None:
        services = await fetch_active_services_map(session)
        for item in body.lines:
            if item.service_id not in services:
                raise HTTPException(
                    status_code=422,
                    detail={"error": {"code": "SERVICE_NOT_FOUND", "message": "Услуга не найдена"}},
                )
        await session.execute(delete(VisitLine).where(VisitLine.visit_id == v.id))
        for item in body.lines:
            session.add(
                VisitLine(
                    visit_id=v.id,
                    service_id=item.service_id,
                    quantity=item.quantity,
                )
            )

    await session.flush()
    await session.refresh(v, attribute_names=["lines"])
    return visit_from_orm(v)


async def set_client_rating_admin(
    session: AsyncSession,
    *,
    visit_id: UUID,
    stars: int,
    comment: str | None,
) -> VisitOut:
    v = await session.get(Visit, visit_id)
    if v is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Визит не найден"}},
        )
    v.client_rating_stars = stars
    v.client_rating_comment = comment
    await session.flush()
    await session.refresh(v, attribute_names=["lines"])
    return visit_from_orm(v)


async def set_service_rating_client(
    session: AsyncSession,
    *,
    user_id: UUID,
    visit_id: UUID,
    stars: int,
    comment: str | None,
) -> VisitOut:
    v = await session.get(Visit, visit_id)
    if v is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Визит не найден"}},
        )
    ap = await session.get(Appointment, v.appointment_id)
    if ap is None or ap.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "FORBIDDEN", "message": "Чужой визит"}},
        )
    v.service_rating_stars = stars
    v.service_rating_comment = comment
    await session.flush()
    await session.refresh(v, attribute_names=["lines"])
    return visit_from_orm(v)
