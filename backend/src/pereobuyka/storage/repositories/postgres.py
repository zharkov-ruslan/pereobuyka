"""Классы-репозитории для доступа к PostgreSQL (этап 1 API)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from pereobuyka.api.v1.schemas import (
    AppointmentAdmin,
    AppointmentStatus,
    ScheduleExceptionCreate,
    ScheduleExceptionPatch,
    ScheduleRuleCreate,
    ScheduleRulePatch,
    ServiceCreate,
    ServicePatch,
)
from pereobuyka.db.models import (
    Appointment,
    ScheduleException,
    ScheduleRule,
    Service,
    User,
)
from pereobuyka.db.models import Visit as VisitRow
from pereobuyka.services.api_adapters import appointment_from_orm, user_from_orm

WhereClause = ColumnElement[bool]


def _day_start_utc(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)


def _day_end_utc(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 23, 59, 59, 999999, tzinfo=UTC)


class PostgresAppointmentRepository:
    """Записи, визиты клиента и журнал для администратора."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        date_from: date | None,
        date_to: date | None,
        status: AppointmentStatus | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Appointment], int]:
        """Список записей пользователя с фильтрами и общим количеством."""
        filters: list[WhereClause] = [Appointment.user_id == user_id]
        if date_from is not None:
            filters.append(Appointment.starts_at >= _day_start_utc(date_from))
        if date_to is not None:
            filters.append(Appointment.starts_at <= _day_end_utc(date_to))
        if status is not None:
            filters.append(Appointment.status == status.value)

        cnt_stmt = select(func.count()).select_from(Appointment).where(*filters)
        total = int((await self._session.scalar(cnt_stmt)) or 0)

        stmt = (
            select(Appointment)
            .options(selectinload(Appointment.lines))
            .where(*filters)
            .order_by(Appointment.starts_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.scalars(stmt)).unique().all()
        return list(rows), total

    async def get_for_user(self, user_id: UUID, appt_id: UUID) -> Appointment | None:
        """Одна запись пользователя с позициями или None."""
        stmt = (
            select(Appointment)
            .options(selectinload(Appointment.lines))
            .where(Appointment.id == appt_id, Appointment.user_id == user_id)
        )
        return (await self._session.scalars(stmt)).first()

    async def list_visits_for_user(
        self,
        *,
        user_id: UUID,
        date_from: date | None,
        date_to: date | None,
        limit: int,
        offset: int,
    ) -> tuple[list[VisitRow], int]:
        """Визиты клиента (через join с записью) с пагинацией."""
        filters: list[WhereClause] = [Appointment.user_id == user_id]
        if date_from is not None:
            filters.append(VisitRow.confirmed_at >= _day_start_utc(date_from))
        if date_to is not None:
            filters.append(VisitRow.confirmed_at <= _day_end_utc(date_to))

        cnt_stmt = (
            select(func.count())
            .select_from(VisitRow)
            .join(Appointment, VisitRow.appointment_id == Appointment.id)
            .where(*filters)
        )
        total = int((await self._session.scalar(cnt_stmt)) or 0)

        stmt = (
            select(VisitRow)
            .join(Appointment, VisitRow.appointment_id == Appointment.id)
            .options(selectinload(VisitRow.lines))
            .where(*filters)
            .order_by(VisitRow.confirmed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.scalars(stmt)).unique().all()
        return list(rows), total

    async def list_for_admin(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        status: AppointmentStatus | None,
        user_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[tuple[Appointment, User | None]], int]:
        """Журнал записей для админки с пользователем и total."""
        filters: list[WhereClause] = []
        if date_from is not None:
            filters.append(Appointment.starts_at >= _day_start_utc(date_from))
        if date_to is not None:
            filters.append(Appointment.starts_at <= _day_end_utc(date_to))
        if status is not None:
            filters.append(Appointment.status == status.value)
        if user_id is not None:
            filters.append(Appointment.user_id == user_id)

        cnt_stmt = (
            select(func.count()).select_from(Appointment).where(*filters)
            if filters
            else select(func.count()).select_from(Appointment)
        )
        total = int((await self._session.scalar(cnt_stmt)) or 0)

        stmt = (
            select(Appointment, User)
            .join(User, Appointment.user_id == User.id)
            .options(selectinload(Appointment.lines))
        )
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(Appointment.starts_at.desc()).limit(limit).offset(offset)
        result = (await self._session.execute(stmt)).unique().all()
        out: list[tuple[Appointment, User | None]] = [(ap, u) for ap, u in result]
        return out, total

    @staticmethod
    def build_admin_rows(pairs: list[tuple[Appointment, User | None]]) -> list[AppointmentAdmin]:
        """Собрать ответ AdminAppointmentList из ORM-пар."""
        items: list[AppointmentAdmin] = []
        for ap, u in pairs:
            base = appointment_from_orm(ap)
            admin_ap = AppointmentAdmin(
                **base.model_dump(),
                user=user_from_orm(u) if u is not None else None,
            )
            items.append(admin_ap)
        return items


class PostgresServiceRepository:
    """CRUD услуг (админский прайс)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, *, is_active: bool | None) -> list[Service]:
        """Все услуги с опциональным фильтром по активности."""
        stmt = select(Service).order_by(Service.name)
        if is_active is not None:
            stmt = stmt.where(Service.is_active.is_(is_active))
        return list((await self._session.scalars(stmt)).all())

    async def create(self, body: ServiceCreate) -> Service:
        """Создать услугу."""
        price = Decimal(body.price).quantize(Decimal("0.01"))
        s = Service(
            id=uuid4(),
            name=body.name,
            description=body.description,
            price=price,
            duration_minutes=body.duration_minutes,
            is_active=body.is_active,
        )
        self._session.add(s)
        await self._session.flush()
        return s

    async def get(self, service_id: UUID) -> Service | None:
        """Получить услугу по id."""
        return await self._session.get(Service, service_id)

    async def patch(self, service_id: UUID, body: ServicePatch) -> Service | None:
        """Частичное обновление услуги."""
        s = await self._session.get(Service, service_id)
        if s is None:
            return None
        if body.name is not None:
            s.name = body.name
        if body.description is not None:
            s.description = body.description
        if body.price is not None:
            s.price = Decimal(body.price).quantize(Decimal("0.01"))
        if body.duration_minutes is not None:
            s.duration_minutes = body.duration_minutes
        if body.is_active is not None:
            s.is_active = body.is_active
        await self._session.flush()
        return s

    async def delete(self, service_id: UUID) -> None:
        """Удалить услугу (FK может вызвать IntegrityError)."""
        s = await self._session.get(Service, service_id)
        if s is None:
            return
        await self._session.delete(s)
        await self._session.flush()


class PostgresScheduleRepository:
    """Шаблоны по дням недели и исключения по датам."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_rules(self) -> list[ScheduleRule]:
        """Все правила расписания по дням недели."""
        rows = (
            await self._session.scalars(select(ScheduleRule).order_by(ScheduleRule.weekday))
        ).all()
        return list(rows)

    async def create_rule(self, body: ScheduleRuleCreate) -> ScheduleRule:
        """Создать правило дня недели."""
        r = ScheduleRule(
            id=uuid4(),
            weekday=body.weekday,
            start_time=body.start_time,
            end_time=body.end_time,
            is_day_off=body.is_day_off,
        )
        self._session.add(r)
        await self._session.flush()
        return r

    async def get_rule(self, rule_id: UUID) -> ScheduleRule | None:
        return await self._session.get(ScheduleRule, rule_id)

    async def patch_rule(self, rule_id: UUID, body: ScheduleRulePatch) -> ScheduleRule | None:
        r = await self._session.get(ScheduleRule, rule_id)
        if r is None:
            return None
        if body.weekday is not None:
            r.weekday = body.weekday
        if body.start_time is not None:
            r.start_time = body.start_time
        if body.end_time is not None:
            r.end_time = body.end_time
        if body.is_day_off is not None:
            r.is_day_off = body.is_day_off
        await self._session.flush()
        return r

    async def delete_rule(self, rule_id: UUID) -> bool:
        r = await self._session.get(ScheduleRule, rule_id)
        if r is None:
            return False
        await self._session.delete(r)
        await self._session.flush()
        return True

    async def list_exceptions(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
    ) -> list[ScheduleException]:
        stmt = select(ScheduleException).order_by(ScheduleException.exception_date)
        if date_from is not None:
            stmt = stmt.where(ScheduleException.exception_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(ScheduleException.exception_date <= date_to)
        return list((await self._session.scalars(stmt)).all())

    async def create_exception(self, body: ScheduleExceptionCreate) -> ScheduleException:
        r = ScheduleException(
            id=uuid4(),
            exception_date=body.date,
            start_time=body.start_time,
            end_time=body.end_time,
            is_day_off=body.is_day_off,
        )
        self._session.add(r)
        await self._session.flush()
        return r

    async def get_exception(self, exc_id: UUID) -> ScheduleException | None:
        return await self._session.get(ScheduleException, exc_id)

    async def patch_exception(
        self, exc_id: UUID, body: ScheduleExceptionPatch
    ) -> ScheduleException | None:
        r = await self._session.get(ScheduleException, exc_id)
        if r is None:
            return None
        if body.date is not None:
            r.exception_date = body.date
        if body.start_time is not None:
            r.start_time = body.start_time
        if body.end_time is not None:
            r.end_time = body.end_time
        if body.is_day_off is not None:
            r.is_day_off = body.is_day_off
        await self._session.flush()
        return r

    async def delete_exception(self, exc_id: UUID) -> bool:
        r = await self._session.get(ScheduleException, exc_id)
        if r is None:
            return False
        await self._session.delete(r)
        await self._session.flush()
        return True
