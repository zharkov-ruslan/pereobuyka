"""Маршруты API v1: каталог услуг, свободные слоты, создание записи."""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from pereobuyka.api.v1.deps import get_current_user
from pereobuyka.api.v1.routes_extended import router as routes_extended_router
from pereobuyka.api.v1.schemas import (
    Appointment,
    AppointmentCreateRequest,
    ServiceItem,
    ServiceListResponse,
    SlotListResponse,
)
from pereobuyka.db.session import get_db_session
from pereobuyka.services.appointment_service import create_appointment
from pereobuyka.services.slot_service import get_free_slots
from pereobuyka.storage.memory import get_services
from pereobuyka.storage.postgres_repos import fetch_services_map

router = APIRouter()
router.include_router(routes_extended_router)

SessionDep = Annotated[AsyncSession | None, Depends(get_db_session)]


@router.get("/services", response_model=ServiceListResponse, summary="Каталог услуг")
async def list_services(
    session: SessionDep,
    active_only: bool = Query(True, description="Только активные услуги"),
) -> ServiceListResponse:
    """Вернуть список услуг (по умолчанию только активные)."""
    if session is not None:
        services = await fetch_services_map(session, active_only=active_only)
    else:
        services = get_services()
    items = [
        ServiceItem(
            id=s.id,
            name=s.name,
            description=s.description,
            duration_minutes=s.duration_minutes,
            price=s.price,
            is_active=s.is_active,
        )
        for s in services.values()
        if not active_only or s.is_active
    ]
    return ServiceListResponse(items=items)


@router.get("/slots", response_model=SlotListResponse, summary="Свободные окна")
async def list_slots(
    session: SessionDep,
    date_from: date = Query(..., description="Начало диапазона (включительно)"),
    date_to: date = Query(..., description="Конец диапазона (включительно)"),
    service_ids: list[UUID] = Query(..., description="Идентификаторы услуг"),
) -> SlotListResponse:
    """Вернуть свободные временные окна для указанных услуг в диапазоне дат."""
    slots = await get_free_slots(session, date_from, date_to, service_ids)
    return SlotListResponse(items=slots)


@router.post(
    "/appointments",
    response_model=Appointment,
    status_code=201,
    summary="Создать запись",
)
async def create_appointment_endpoint(
    request: AppointmentCreateRequest,
    session: SessionDep,
    current_user_id: UUID = Depends(get_current_user),
) -> Appointment:
    """Создать запись клиента на обслуживание."""
    return await create_appointment(session, current_user_id, request)
