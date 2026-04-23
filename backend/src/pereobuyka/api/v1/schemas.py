"""Pydantic-схемы публичного API v1 (согласованы с docs/tech/api/openapi.yaml)."""

from datetime import date as Date
from datetime import datetime, time
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AppointmentStatus(StrEnum):
    """Статус записи на обслуживание."""

    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class UserRole(StrEnum):
    client = "client"
    admin = "admin"


class UserSource(StrEnum):
    telegram = "telegram"
    web = "web"


class ServiceLineItem(BaseModel):
    """Позиция услуги в записи или визите."""

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


class AppointmentPatchRequest(BaseModel):
    """Обновление записи клиентом."""

    status: AppointmentStatus | None = None


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


class AppointmentListResponse(BaseModel):
    items: list[Appointment]
    total: int


class User(BaseModel):
    """Пользователь в ответах API."""

    id: UUID
    name: str
    phone: str | None = None
    role: UserRole
    telegram_id: int | None = None
    registered_at: datetime
    source: UserSource


class AppointmentAdmin(Appointment):
    user: User | None = None


class AdminAppointmentListResponse(BaseModel):
    items: list[AppointmentAdmin]
    total: int


class ServiceItem(BaseModel):
    """Услуга в публичном каталоге (расширено полем description по контракту)."""

    id: UUID
    name: str
    description: str = ""
    duration_minutes: int
    price: Decimal
    is_active: bool


class ServiceOut(BaseModel):
    """Услуга как в OpenAPI `Service` (цена — строка в JSON)."""

    id: UUID
    name: str
    description: str
    price: str
    duration_minutes: int
    is_active: bool


class ServiceCreate(BaseModel):
    name: str
    description: str
    price: str
    duration_minutes: int
    is_active: bool


class ServicePatch(BaseModel):
    name: str | None = None
    description: str | None = None
    price: str | None = None
    duration_minutes: int | None = None
    is_active: bool | None = None


class ServiceListResponse(BaseModel):
    """Ответ каталога услуг."""

    items: list[ServiceItem]


class ScheduleRule(BaseModel):
    id: UUID
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_day_off: bool


class ScheduleRuleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_day_off: bool


class ScheduleRulePatch(BaseModel):
    weekday: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    is_day_off: bool | None = None


class ScheduleRuleListResponse(BaseModel):
    items: list[ScheduleRule]


class ScheduleException(BaseModel):
    id: UUID
    date: Date
    start_time: time
    end_time: time
    is_day_off: bool


class ScheduleExceptionCreate(BaseModel):
    date: Date
    start_time: time
    end_time: time
    is_day_off: bool


class ScheduleExceptionPatch(BaseModel):
    date: Date | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_day_off: bool | None = None


class ScheduleExceptionListResponse(BaseModel):
    items: list[ScheduleException]


class Visit(BaseModel):
    id: UUID
    appointment_id: UUID
    total_amount: str
    bonus_spent: int
    bonus_earned: int
    confirmed_at: datetime
    confirmed_by_user_id: UUID
    lines: list[ServiceLineItem]


class VisitListResponse(BaseModel):
    items: list[Visit]
    total: int


class VisitConfirmRequest(BaseModel):
    appointment_id: UUID
    lines: list[ServiceLineItem]
    total_amount: str
    bonus_spent: int = 0


class BonusTransactionType(StrEnum):
    earn = "earn"
    spend = "spend"
    adjust = "adjust"


class BonusAccount(BaseModel):
    id: UUID
    user_id: UUID
    balance: int


class BonusTransaction(BaseModel):
    id: UUID
    type: BonusTransactionType
    amount: int
    visit_id: UUID | None = None
    created_at: datetime
    comment: str | None = None


class BonusTransactionListResponse(BaseModel):
    items: list[BonusTransaction]
    total: int


class BonusAdjustRequest(BaseModel):
    amount: int
    comment: str


class LoyaltyRules(BaseModel):
    max_bonus_spend_percent: int = Field(ge=0, le=100)
    earn_percent_after_visit: int = Field(ge=0, le=100)


class TelegramAuthRequest(BaseModel):
    telegram_id: int
    name: str
    phone: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class ConsultationHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ConsultationRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ConsultationHistoryItem] = Field(default_factory=list, max_length=20)


class ConsultationResponse(BaseModel):
    reply: str
    request_id: UUID | None = None
