"""ORM-модели PostgreSQL (согласованы с Alembic `0001_initial`)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pereobuyka.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text())
    phone: Mapped[str | None] = mapped_column(Text(), nullable=True)
    role: Mapped[str] = mapped_column(Text())
    telegram_id: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(Text(), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(Text())


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text())
    description: Mapped[str] = mapped_column(Text())
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    duration_minutes: Mapped[int] = mapped_column(Integer())
    is_active: Mapped[bool] = mapped_column(Boolean(), server_default=sa.true())


class ScheduleRule(Base):
    __tablename__ = "schedule_rules"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    weekday: Mapped[int] = mapped_column(SmallInteger())
    start_time: Mapped[time] = mapped_column(Time())
    end_time: Mapped[time] = mapped_column(Time())
    is_day_off: Mapped[bool] = mapped_column(Boolean())


class ScheduleException(Base):
    __tablename__ = "schedule_exceptions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    exception_date: Mapped[date] = mapped_column(Date())
    start_time: Mapped[time] = mapped_column(Time())
    end_time: Mapped[time] = mapped_column(Time())
    is_day_off: Mapped[bool] = mapped_column(Boolean())


class AppointmentLine(Base):
    __tablename__ = "appointment_services"

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    quantity: Mapped[int] = mapped_column(Integer())

    appointment: Mapped[Appointment] = relationship(back_populates="lines")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(Text(), server_default="web")
    discount_percent: Mapped[int] = mapped_column(SmallInteger(), server_default="0")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    lines: Mapped[list[AppointmentLine]] = relationship(
        back_populates="appointment",
        lazy="selectin",
    )


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="RESTRICT"),
        unique=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    bonus_spent: Mapped[int] = mapped_column(Integer(), server_default="0")
    bonus_earned: Mapped[int] = mapped_column(Integer(), server_default="0")
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    client_rating_stars: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    client_rating_comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    service_rating_stars: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
    service_rating_comment: Mapped[str | None] = mapped_column(Text(), nullable=True)

    lines: Mapped[list[VisitLine]] = relationship(back_populates="visit", lazy="selectin")


class VisitLine(Base):
    __tablename__ = "visit_lines"

    visit_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="CASCADE"),
        primary_key=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    quantity: Mapped[int] = mapped_column(Integer())

    visit: Mapped[Visit] = relationship(back_populates="lines")


class BonusAccount(Base):
    __tablename__ = "bonus_accounts"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
    )
    balance: Mapped[int] = mapped_column(Integer(), server_default="0")


class BonusTransaction(Base):
    __tablename__ = "bonus_transactions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bonus_accounts.id", ondelete="RESTRICT"),
    )
    type: Mapped[str] = mapped_column(Text())
    amount: Mapped[int] = mapped_column(Integer())
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)


class LoyaltySettings(Base):
    __tablename__ = "loyalty_settings"

    id: Mapped[int] = mapped_column(SmallInteger(), primary_key=True)
    max_bonus_spend_percent: Mapped[int] = mapped_column(SmallInteger())
    earn_percent_after_visit: Mapped[int] = mapped_column(SmallInteger())


class FaqEntry(Base):
    __tablename__ = "faq_entries"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    question: Mapped[str] = mapped_column(Text())
    answer: Mapped[str] = mapped_column(Text())
    is_active: Mapped[bool] = mapped_column(Boolean(), server_default=sa.true())


class ConsultationMessage(Base):
    __tablename__ = "consultation_messages"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    role: Mapped[str] = mapped_column(Text())
    content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    request_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
