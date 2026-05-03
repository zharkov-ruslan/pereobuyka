"""Агрегаты админ-панели веб UI: дашборд, сетка недели, аналитика, клиенты."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pereobuyka.api.v1.schemas import (
    AdminClientListResponse,
    AdminClientRow,
    AnalyticsWeekDay,
    AnalyticsWeekResponse,
    AppointmentStatus,
    DashboardTodayResponse,
    TopServiceStat,
    WeekGridDay,
    WeekGridEvent,
    WeekGridResponse,
    WeekGridSlot,
)
from pereobuyka.db.models import (
    Appointment,
    AppointmentLine,
    BonusAccount,
    ConsultationMessage,
    Service,
    User,
)
from pereobuyka.db.models import Visit as VisitRow
from pereobuyka.storage.memory import SLOT_STEP_MINUTES
from pereobuyka.storage.postgres_repos import (
    fetch_exceptions_by_date,
    fetch_schedule_by_weekday,
)
from pereobuyka.utils import overlaps


def _tz_from_settings(tz_name: str) -> ZoneInfo:
    return ZoneInfo(tz_name)


def _local_day_bounds_utc(d: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start_local = datetime(d.year, d.month, d.day, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def _aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


async def dashboard_today(
    session: AsyncSession,
    *,
    business_tz: str,
) -> DashboardTodayResponse:
    tz = _tz_from_settings(business_tz)
    today_local = datetime.now(tz).date()
    day_start, day_end = _local_day_bounds_utc(today_local, tz)

    # Как в сетке недели: день = [day_start, day_end) в UTC, запись учитывается при пересечении
    # интервала [starts_at, ends_at) с этим окном (не только если starts_at попал в день).
    appt_today = [
        Appointment.starts_at < day_end,
        Appointment.ends_at > day_start,
    ]
    total_stmt = select(func.count()).select_from(Appointment).where(*appt_today)
    appointments_total = int((await session.scalar(total_stmt)) or 0)

    visits_stmt = (
        select(func.count())
        .select_from(VisitRow)
        .where(VisitRow.confirmed_at >= day_start, VisitRow.confirmed_at < day_end)
    )
    visits_total = int((await session.scalar(visits_stmt)) or 0)

    cancel_stmt = (
        select(func.count())
        .select_from(Appointment)
        .where(
            *appt_today,
            Appointment.status == AppointmentStatus.cancelled.value,
        )
    )
    cancellations_total = int((await session.scalar(cancel_stmt)) or 0)

    # Источники записей на сегодня: все статусы (включая отмены), пересечение с календарным днём.
    sched_stmt = (
        select(Appointment.source, func.count())
        .where(
            *appt_today,
            Appointment.status.in_(
                (
                    AppointmentStatus.scheduled.value,
                    AppointmentStatus.completed.value,
                    AppointmentStatus.cancelled.value,
                ),
            ),
        )
        .group_by(Appointment.source)
    )
    rows = (await session.execute(sched_stmt)).all()
    by_src: dict[str, int] = {
        "llm": 0,
        "telegram_bot": 0,
        "web": 0,
        "admin": 0,
    }
    for src, cnt in rows:
        key = src if src in by_src else "web"
        by_src[key] = int(cnt)

    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    cq_stmt = (
        select(func.count())
        .select_from(ConsultationMessage)
        .where(
            ConsultationMessage.created_at >= seven_days_ago,
            ConsultationMessage.role == "user",
        )
    )
    cq_cnt = int((await session.scalar(cq_stmt)) or 0)

    return DashboardTodayResponse(
        date=today_local,
        appointments_total=appointments_total,
        visits_total=visits_total,
        cancellations_total=cancellations_total,
        bookings_scheduled_today_by_source=by_src,
        consultation_user_messages_last_7_days=cq_cnt,
    )


async def week_grid(
    session: AsyncSession,
    *,
    week_start: date,
    business_tz: str,
) -> WeekGridResponse:
    tz = _tz_from_settings(business_tz)
    monday = week_start
    week_end_day = monday + timedelta(days=6)
    range_start = datetime(monday.year, monday.month, monday.day, tzinfo=tz).astimezone(UTC)
    range_end = (
        datetime(week_end_day.year, week_end_day.month, week_end_day.day, tzinfo=tz)
        + timedelta(days=1)
    ).astimezone(UTC)

    appt_stmt = (
        select(Appointment)
        .options(selectinload(Appointment.lines))
        .where(Appointment.starts_at < range_end, Appointment.ends_at > range_start)
    )
    appointments = list((await session.scalars(appt_stmt)).unique().all())
    user_ids = {a.user_id for a in appointments}
    users_map: dict[UUID, User] = {}
    if user_ids:
        urows = (await session.scalars(select(User).where(User.id.in_(user_ids)))).all()
        users_map = {u.id: u for u in urows}

    if appointments:
        visit_stmt = select(VisitRow).where(
            VisitRow.appointment_id.in_([a.id for a in appointments]),
        )
        visits = list((await session.scalars(visit_stmt)).unique().all())
    else:
        visits = []
    visit_by_appt = {v.appointment_id: v for v in visits}

    services = {s.id: s for s in (await session.scalars(select(Service))).all()}
    weekday_sched = await fetch_schedule_by_weekday(session)
    exc_map = await fetch_exceptions_by_date(session)

    days_out: list[WeekGridDay] = []
    day = monday
    while day <= week_end_day:
        day_ds, day_de = _local_day_bounds_utc(day, tz)

        ex = exc_map.get(day)
        if ex is not None:
            if ex.is_day_off:
                days_out.append(WeekGridDay(date=day, slots=[]))
                day += timedelta(days=1)
                continue
            open_t, close_t = ex.start_time, ex.end_time
        else:
            window = weekday_sched.get(day.weekday())
            if window is None:
                days_out.append(WeekGridDay(date=day, slots=[]))
                day += timedelta(days=1)
                continue
            open_t, close_t = window

        day_appts = [
            ap
            for ap in appointments
            if overlaps(
                day_ds,
                day_de,
                _aware_utc(ap.starts_at),
                _aware_utc(ap.ends_at),
            )
        ]

        slots: list[WeekGridSlot] = []
        day_start_local = datetime(day.year, day.month, day.day, tzinfo=tz)
        slot_start = day_start_local.replace(
            hour=open_t.hour, minute=open_t.minute, second=open_t.second
        )
        day_end_dt = day_start_local.replace(
            hour=close_t.hour, minute=close_t.minute, second=close_t.second
        )

        step = timedelta(minutes=SLOT_STEP_MINUTES)
        while True:
            slot_end = slot_start + step
            if slot_end > day_end_dt:
                break
            st_utc = slot_start.astimezone(UTC)
            en_utc = slot_end.astimezone(UTC)
            events: list[WeekGridEvent] = []
            for ap in day_appts:
                astart = _aware_utc(ap.starts_at)
                aend = _aware_utc(ap.ends_at)
                if not overlaps(st_utc, en_utc, astart, aend):
                    continue
                u = users_map.get(ap.user_id)
                labels: list[str] = []
                for line in ap.lines:
                    sv = services.get(line.service_id)
                    name = sv.name if sv else str(line.service_id)
                    labels.append(f"{name} ×{line.quantity}")

                visit = visit_by_appt.get(ap.id)
                if visit is not None:
                    state: Literal["scheduled", "completed", "cancelled"] = "completed"
                elif ap.status == AppointmentStatus.cancelled.value:
                    state = "cancelled"
                else:
                    state = "scheduled"

                events.append(
                    WeekGridEvent(
                        state=state,
                        appointment_id=ap.id,
                        visit_id=visit.id if visit else None,
                        total_price=f"{ap.total_price:.2f}",
                        client_name=u.name if u else "?",
                        service_summaries=labels,
                        client_rating_stars=visit.client_rating_stars if visit else None,
                        client_rating_comment=visit.client_rating_comment if visit else None,
                    )
                )

            slots.append(
                WeekGridSlot(
                    starts_at=st_utc,
                    ends_at=en_utc,
                    events=events,
                )
            )
            slot_start = slot_end

        days_out.append(WeekGridDay(date=day, slots=slots))
        day += timedelta(days=1)

    return WeekGridResponse(
        week_start=monday,
        slot_step_minutes=SLOT_STEP_MINUTES,
        days=days_out,
    )


async def analytics_week(
    session: AsyncSession,
    *,
    week_start: date,
    business_tz: str,
) -> AnalyticsWeekResponse:
    tz = _tz_from_settings(business_tz)
    monday = week_start
    sunday = monday + timedelta(days=6)
    range_start = datetime(monday.year, monday.month, monday.day, tzinfo=tz).astimezone(UTC)
    range_end = (
        datetime(sunday.year, sunday.month, sunday.day, tzinfo=tz) + timedelta(days=1)
    ).astimezone(UTC)

    days: list[AnalyticsWeekDay] = []
    d = monday
    while d <= sunday:
        ds, de = _local_day_bounds_utc(d, tz)

        ac = int(
            (
                await session.scalar(
                    select(func.count())
                    .select_from(Appointment)
                    .where(Appointment.starts_at >= ds, Appointment.starts_at < de)
                )
            )
            or 0
        )
        vc = int(
            (
                await session.scalar(
                    select(func.count())
                    .select_from(VisitRow)
                    .where(VisitRow.confirmed_at >= ds, VisitRow.confirmed_at < de)
                )
            )
            or 0
        )
        cc = int(
            (
                await session.scalar(
                    select(func.count())
                    .select_from(Appointment)
                    .where(
                        Appointment.starts_at >= ds,
                        Appointment.starts_at < de,
                        Appointment.status == AppointmentStatus.cancelled.value,
                    )
                )
            )
            or 0
        )

        rev = (
            await session.scalar(
                select(func.coalesce(func.sum(VisitRow.total_amount), 0)).where(
                    VisitRow.confirmed_at >= ds,
                    VisitRow.confirmed_at < de,
                )
            )
        ) or Decimal(0)

        sched_stmt = (
            select(Appointment.source, func.count())
            .where(
                Appointment.starts_at >= ds,
                Appointment.starts_at < de,
                Appointment.status == AppointmentStatus.scheduled.value,
            )
            .group_by(Appointment.source)
        )
        sch_rows = (await session.execute(sched_stmt)).all()
        by_src: dict[str, int] = {"llm": 0, "telegram_bot": 0, "web": 0, "admin": 0}
        for src, cnt in sch_rows:
            key = src if src in by_src else "web"
            by_src[key] = int(cnt)

        days.append(
            AnalyticsWeekDay(
                date=d,
                appointments_count=ac,
                visits_count=vc,
                cancellations_count=cc,
                revenue_amount=f"{Decimal(rev):.2f}",
                bookings_by_source=by_src,
            )
        )
        d += timedelta(days=1)

    bc = func.count(AppointmentLine.appointment_id).label("bc")
    top_stmt = (
        select(Service.id, Service.name, bc)
        .join(AppointmentLine, AppointmentLine.service_id == Service.id)
        .join(Appointment, Appointment.id == AppointmentLine.appointment_id)
        .where(Appointment.starts_at >= range_start, Appointment.starts_at < range_end)
        .group_by(Service.id, Service.name)
        .order_by(bc.desc())
        .limit(3)
    )
    top_rows = (await session.execute(top_stmt)).all()
    top_services = [
        TopServiceStat(service_id=r[0], name=r[1], bookings_count=int(r[2])) for r in top_rows
    ]

    return AnalyticsWeekResponse(week_start=monday, top_services=top_services, days=days)


async def admin_clients_list(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
) -> AdminClientListResponse:
    stmt_users: Select[tuple[User]] = (
        select(User)
        .where(User.role == "client")
        .order_by(User.name.asc())
        .limit(limit)
        .offset(offset)
    )
    clients = list((await session.scalars(stmt_users)).all())

    cnt_stmt = select(func.count()).select_from(User).where(User.role == "client")
    total = int((await session.scalar(cnt_stmt)) or 0)

    items: list[AdminClientRow] = []
    for u in clients:
        visits_cnt = int(
            (
                await session.scalar(
                    select(func.count())
                    .select_from(VisitRow)
                    .join(Appointment, Appointment.id == VisitRow.appointment_id)
                    .where(Appointment.user_id == u.id)
                )
            )
            or 0
        )
        spent = (
            await session.scalar(
                select(func.coalesce(func.sum(VisitRow.total_amount), 0))
                .select_from(VisitRow)
                .join(Appointment, Appointment.id == VisitRow.appointment_id)
                .where(Appointment.user_id == u.id)
            )
        ) or Decimal(0)

        bal = await session.scalar(select(BonusAccount.balance).where(BonusAccount.user_id == u.id))
        bonus_bal = int(bal) if bal is not None else 0

        rating_avg = await session.scalar(
            select(func.avg(VisitRow.client_rating_stars))
            .select_from(VisitRow)
            .join(Appointment, Appointment.id == VisitRow.appointment_id)
            .where(Appointment.user_id == u.id, VisitRow.client_rating_stars.is_not(None))
        )
        rating_str = f"{float(rating_avg):.2f}" if rating_avg is not None else None

        items.append(
            AdminClientRow(
                user_id=u.id,
                name=u.name,
                phone=u.phone,
                telegram_id=u.telegram_id,
                telegram_username=getattr(u, "telegram_username", None),
                visits_count=visits_cnt,
                total_spent=f"{Decimal(spent):.2f}",
                bonus_balance=bonus_bal,
                rating_avg=rating_str,
            )
        )

    return AdminClientListResponse(items=items, total=total)
