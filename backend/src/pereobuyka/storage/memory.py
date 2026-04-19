"""In-memory storage — временный слой хранения данных.

Используется как MVP-хранилище до появления database-tasklist
с реализацией SQLAlchemy/PostgreSQL репозиториев.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal, TypedDict
from uuid import UUID

# ── Предзасеянные данные ──────────────────────────────────────────────────────

DEFAULT_SERVICE_ID = UUID("00000000-0000-0000-0000-000000000001")

# Шаг генерации слотов (минуты)
SLOT_STEP_MINUTES = 30

# Расписание: номер дня недели → (час открытия, час закрытия)
WORKING_HOURS: dict[int, tuple[int, int]] = {
    0: (9, 18),  # Пн
    1: (9, 18),  # Вт
    2: (9, 18),  # Ср
    3: (9, 18),  # Чт
    4: (9, 18),  # Пт
}


# ── Вспомогательные типы ──────────────────────────────────────────────────────


class ServiceLineItemDict(TypedDict):
    """Позиция услуги в хранилищном объекте записи."""

    service_id: str
    quantity: int


# ── Записи о сущностях ────────────────────────────────────────────────────────


@dataclass
class ServiceRecord:
    """Запись об услуге в каталоге."""

    id: UUID
    name: str
    duration_minutes: int
    price: Decimal
    is_active: bool = True


@dataclass
class AppointmentRecord:
    """Запись о визите клиента (хранилищный объект)."""

    id: UUID
    user_id: UUID
    starts_at: datetime
    ends_at: datetime
    total_price: Decimal
    status: Literal["scheduled", "completed", "cancelled"]
    created_at: datetime
    service_items: list[ServiceLineItemDict] = field(default_factory=list)


# ── Хранилища ─────────────────────────────────────────────────────────────────

_SERVICES: dict[UUID, ServiceRecord] = {
    DEFAULT_SERVICE_ID: ServiceRecord(
        id=DEFAULT_SERVICE_ID,
        name="Замена резины",
        duration_minutes=60,
        price=Decimal("2000.00"),
    )
}

_appointments: list[AppointmentRecord] = []


# ── Публичный интерфейс ───────────────────────────────────────────────────────


def get_services() -> dict[UUID, ServiceRecord]:
    """Вернуть каталог услуг."""
    return _SERVICES


def get_appointments() -> list[AppointmentRecord]:
    """Вернуть все записи о визитах."""
    return _appointments


def add_appointment(record: AppointmentRecord) -> None:
    """Добавить запись о визите в хранилище."""
    _appointments.append(record)


def reset_appointments() -> None:
    """Очистить список записей. Используется в тестах."""
    _appointments.clear()
