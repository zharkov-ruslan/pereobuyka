"""Pydantic-схемы публичного API v1."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class AppointmentStatus(StrEnum):
    """Статус записи на обслуживание."""

    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class ServiceLineItem(BaseModel):
    """Позиция услуги в запросе или ответе."""

    service_id: UUID
    quantity: int = 1


class SlotWindow(BaseModel):
    """Свободное временное окно для записи."""

    starts_at: datetime
    ends_at: datetime


class SlotListResponse(BaseModel):
    """Ответ на запрос свободных слотов."""

    items: list[SlotWindow]


class AppointmentCreateRequest(BaseModel):
    """Запрос на создание записи."""

    starts_at: datetime
    service_items: list[ServiceLineItem]
    bonus_spend: int = 0


class Appointment(BaseModel):
    """Запись на обслуживание."""

    id: UUID
    user_id: UUID
    starts_at: datetime
    ends_at: datetime
    total_price: str
    status: AppointmentStatus
    created_at: datetime
    service_items: list[ServiceLineItem]


class ServiceItem(BaseModel):
    """Услуга из каталога."""

    id: UUID
    name: str
    duration_minutes: int
    price: Decimal
    is_active: bool


class ServiceListResponse(BaseModel):
    """Ответ на запрос каталога услуг."""

    items: list[ServiceItem]
