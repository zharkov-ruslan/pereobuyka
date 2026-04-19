"""Маршруты API v1: каталог услуг, свободные слоты, создание записи."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from pereobuyka.api.v1.deps import get_current_user
from pereobuyka.api.v1.schemas import (
    Appointment,
    AppointmentCreateRequest,
    ServiceItem,
    ServiceListResponse,
    SlotListResponse,
)
from pereobuyka.services.appointment_service import create_appointment
from pereobuyka.services.slot_service import get_free_slots
from pereobuyka.storage.memory import get_services

router = APIRouter()


@router.get("/services", response_model=ServiceListResponse, summary="Каталог услуг")
async def list_services() -> ServiceListResponse:
    """Вернуть список активных услуг."""
    services = get_services()
    items = [
        ServiceItem(
            id=s.id,
            name=s.name,
            duration_minutes=s.duration_minutes,
            price=s.price,
            is_active=s.is_active,
        )
        for s in services.values()
        if s.is_active
    ]
    return ServiceListResponse(items=items)


@router.get("/slots", response_model=SlotListResponse, summary="Свободные окна")
async def list_slots(
    date_from: date = Query(..., description="Начало диапазона (включительно)"),
    date_to: date = Query(..., description="Конец диапазона (включительно)"),
    service_ids: list[UUID] = Query(..., description="Идентификаторы услуг"),
) -> SlotListResponse:
    """Вернуть свободные временные окна для указанных услуг в диапазоне дат."""
    slots = get_free_slots(date_from, date_to, service_ids)
    return SlotListResponse(items=slots)


@router.post(
    "/appointments",
    response_model=Appointment,
    status_code=201,
    summary="Создать запись",
)
async def create_appointment_endpoint(
    request: AppointmentCreateRequest,
    current_user_id: UUID = Depends(get_current_user),
) -> Appointment:
    """Создать запись клиента на обслуживание."""
    return create_appointment(current_user_id, request)
