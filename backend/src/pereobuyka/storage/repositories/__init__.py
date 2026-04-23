"""Репозитории PostgreSQL (адаптеры SQLAlchemy к сценариям API)."""

from pereobuyka.storage.repositories.postgres import (
    PostgresAppointmentRepository,
    PostgresScheduleRepository,
    PostgresServiceRepository,
)

__all__ = [
    "PostgresAppointmentRepository",
    "PostgresScheduleRepository",
    "PostgresServiceRepository",
]
