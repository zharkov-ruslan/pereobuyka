"""Преобразование ORM-строк в схемы публичного API."""

from __future__ import annotations

from pereobuyka.api.v1.schemas import (
    Appointment as AppointmentOut,
)
from pereobuyka.api.v1.schemas import (
    AppointmentStatus,
    ServiceLineItem,
    ServiceOut,
    User,
    UserRole,
    UserSource,
)
from pereobuyka.api.v1.schemas import (
    ScheduleException as ScheduleExceptionOut,
)
from pereobuyka.api.v1.schemas import (
    ScheduleRule as ScheduleRuleOut,
)
from pereobuyka.api.v1.schemas import (
    Visit as VisitOut,
)
from pereobuyka.db.models import (
    Appointment,
    ScheduleException,
    ScheduleRule,
    Service,
)
from pereobuyka.db.models import (
    User as UserRow,
)
from pereobuyka.db.models import (
    Visit as VisitRow,
)
from pereobuyka.storage.postgres_repos import _as_utc_naive


def user_from_orm(row: UserRow) -> User:
    """Собрать схему User из строки таблицы users."""
    return User(
        id=row.id,
        name=row.name,
        phone=row.phone,
        role=UserRole(row.role),
        telegram_id=row.telegram_id,
        registered_at=_as_utc_naive(row.registered_at),
        source=UserSource(row.source),
    )


def appointment_from_orm(ap: Appointment) -> AppointmentOut:
    """Собрать схему записи с загруженными позициями услуг."""
    st = AppointmentStatus(ap.status)
    items = [
        ServiceLineItem(service_id=line.service_id, quantity=line.quantity) for line in ap.lines
    ]
    return AppointmentOut(
        id=ap.id,
        user_id=ap.user_id,
        starts_at=_as_utc_naive(ap.starts_at),
        ends_at=_as_utc_naive(ap.ends_at),
        total_price=f"{ap.total_price:.2f}",
        status=st,
        created_at=_as_utc_naive(ap.created_at),
        service_items=items,
    )


def service_from_orm(s: Service) -> ServiceOut:
    """Собрать схему услуги для админского ответа (цена — строка)."""
    return ServiceOut(
        id=s.id,
        name=s.name,
        description=s.description or "",
        price=f"{s.price:.2f}",
        duration_minutes=s.duration_minutes,
        is_active=s.is_active,
    )


def schedule_rule_from_orm(r: ScheduleRule) -> ScheduleRuleOut:
    """Собрать схему правила дня недели."""
    return ScheduleRuleOut(
        id=r.id,
        weekday=int(r.weekday),
        start_time=r.start_time,
        end_time=r.end_time,
        is_day_off=r.is_day_off,
    )


def schedule_exception_from_orm(r: ScheduleException) -> ScheduleExceptionOut:
    """Собрать схему исключения расписания (дата из exception_date)."""
    return ScheduleExceptionOut(
        id=r.id,
        date=r.exception_date,
        start_time=r.start_time,
        end_time=r.end_time,
        is_day_off=r.is_day_off,
    )


def visit_from_orm(v: VisitRow) -> VisitOut:
    """Собрать схему визита с строками услуг."""
    lines = [
        ServiceLineItem(service_id=line.service_id, quantity=line.quantity) for line in v.lines
    ]
    return VisitOut(
        id=v.id,
        appointment_id=v.appointment_id,
        total_amount=f"{v.total_amount:.2f}",
        bonus_spent=v.bonus_spent,
        bonus_earned=v.bonus_earned,
        confirmed_at=_as_utc_naive(v.confirmed_at),
        confirmed_by_user_id=v.confirmed_by_user_id,
        lines=lines,
    )
