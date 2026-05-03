"""Pydantic-схемы публичного API v1 (согласованы с docs/tech/api/openapi.yaml)."""

from datetime import UTC, datetime, time
from datetime import date as Date
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


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


class AppointmentSource(StrEnum):
    llm = "llm"
    telegram_bot = "telegram_bot"
    web = "web"
    admin = "admin"


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
    source: AppointmentSource = AppointmentSource.web
    discount_percent: int = Field(default=0, ge=0, le=100)


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
    telegram_username: str | None = None
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
    client_rating_stars: int | None = None
    client_rating_comment: str | None = None
    service_rating_stars: int | None = None
    service_rating_comment: str | None = None


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


class WebAuthRequest(BaseModel):
    """Вход клиента в веб по Telegram username (MVP без доказательства владения)."""

    telegram_username: str = Field(min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=32)


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


class ConsultationTranscribeResponse(BaseModel):
    text: str


class ConsultationMessageOut(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    request_id: UUID | None = None


class ConsultationMessageListResponse(BaseModel):
    items: list[ConsultationMessageOut]
    total: int


class DashboardTodayResponse(BaseModel):
    date: Date
    appointments_total: int
    visits_total: int
    cancellations_total: int
    bookings_scheduled_today_by_source: dict[str, int]
    consultation_user_messages_last_7_days: int


class WeekGridEvent(BaseModel):
    state: Literal["scheduled", "completed", "cancelled"]
    appointment_id: UUID
    visit_id: UUID | None = None
    total_price: str
    client_name: str
    service_summaries: list[str]
    client_rating_stars: int | None = None
    client_rating_comment: str | None = None


def _datetime_utc_iso_z(dt: datetime) -> str:
    """UTC instant для JSON: всегда с суффиксом Z (не +00:00)."""
    aware = dt.astimezone(UTC) if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
    if aware.microsecond:
        return aware.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    return aware.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


class WeekGridSlot(BaseModel):
    starts_at: datetime
    ends_at: datetime
    events: list[WeekGridEvent]

    @field_serializer("starts_at", "ends_at", when_used="json")
    def ser_slot_bounds_utc_z(self, value: datetime) -> str:
        return _datetime_utc_iso_z(value)


class WeekGridDay(BaseModel):
    date: Date
    slots: list[WeekGridSlot]


class WeekGridResponse(BaseModel):
    week_start: Date
    slot_step_minutes: int
    days: list[WeekGridDay]


class AnalyticsWeekDay(BaseModel):
    date: Date
    appointments_count: int
    visits_count: int
    cancellations_count: int
    revenue_amount: str
    bookings_by_source: dict[str, int]


class TopServiceStat(BaseModel):
    service_id: UUID
    name: str
    bookings_count: int


class AnalyticsWeekResponse(BaseModel):
    """Недельная аналитика для графиков."""

    week_start: Date
    top_services: list[TopServiceStat]
    days: list[AnalyticsWeekDay]


class AdminClientRow(BaseModel):
    user_id: UUID
    name: str
    phone: str | None
    telegram_id: int | None
    telegram_username: str | None
    visits_count: int
    total_spent: str
    bonus_balance: int
    rating_avg: str | None


class AdminClientListResponse(BaseModel):
    items: list[AdminClientRow]
    total: int


class AdminClientQuickCreateBody(BaseModel):
    """Быстрое заведение клиента из админки (без Telegram)."""

    name: str = Field(min_length=1, max_length=200)
    phone: str | None = None


class AdminAppointmentCreateBody(BaseModel):
    """Создание записи на клиента из админ-панели."""

    user_id: UUID
    starts_at: datetime
    service_items: list[ServiceLineItem]
    discount_percent: int = Field(default=0, ge=0, le=100)


class AdminAppointmentPatchBody(BaseModel):
    status: AppointmentStatus | None = None
    service_items: list[ServiceLineItem] | None = None
    discount_percent: int | None = Field(default=None, ge=0, le=100)
    source: AppointmentSource | None = None


class AdminVisitPatchBody(BaseModel):
    lines: list[ServiceLineItem] | None = None
    total_amount: str | None = None
    bonus_spent: int | None = Field(default=None, ge=0)
    bonus_earned: int | None = Field(default=None, ge=0)


class VisitRatingBody(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ServiceRatingBody(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class AdminDataInsightRequest(BaseModel):
    """Вопрос администратора на естественном языке → безопасный SELECT."""

    question: str = Field(min_length=1, max_length=2000)


class AdminDataInsightResponse(BaseModel):
    summary: str
    sql_executed: str
    columns: list[str]
    rows: list[dict[str, object]]
    truncated: bool
