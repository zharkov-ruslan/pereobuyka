# iter-db-05 — summary

## Результат

- **ORM:** [`backend/src/pereobuyka/db/`](../../../../../backend/src/pereobuyka/db/) — `Base`, модели `User`, `Service`, `ScheduleRule`, `Appointment`, `AppointmentLine` (`appointment_services`).
- **Сессия:** [`session.py`](../../../../../backend/src/pereobuyka/db/session.py) — `init_db_engine` / `dispose_db_engine`, `get_db_session` (для SQLite выдаёт `None`).
- **Репозиторий:** [`postgres_repos.py`](../../../../../backend/src/pereobuyka/storage/postgres_repos.py) — выборки и вставка; ответы API по-прежнему через Pydantic в сервисах ([ADR-003](../../../../../docs/tech/adr/adr-003-orm.md)).
- **Сервисы:** [`slot_service.py`](../../../../../backend/src/pereobuyka/services/slot_service.py) (`compute_free_slots` + расписание из БД или из `WORKING_HOURS`), [`appointment_service.py`](../../../../../backend/src/pereobuyka/services/appointment_service.py) — async `create_appointment`.
- **Роутер:** [`router.py`](../../../../../backend/src/pereobuyka/api/v1/router.py) — async, `SessionDep`.
- **Тесты:** [`conftest.py`](../../../../../backend/tests/conftest.py) — `PostgresContainer`, Alembic + seed, `TESTCONTAINERS_RYUK_DISABLED=true`, изоляция `TRUNCATE appointment_services, appointments CASCADE`.
- **Зависимости:** dev-группа [`testcontainers[postgres]`](../../../../../backend/pyproject.toml).

## Режимы `DATABASE_URL`

| URL | Поведение MVP-маршрутов |
|-----|-------------------------|
| `postgresql+asyncpg://…` | Данные из PostgreSQL |
| `sqlite+aiosqlite://…` | In-memory [`memory.py`](../../../../../backend/src/pereobuyka/storage/memory.py) |

## Следующие шаги (вне iter-db-05)

- Остальные сущности и эндпоинты из `data-model` / OpenAPI.
- Исключения расписания (`schedule_exceptions`) в расчёте слотов.
- Маркер `@pytest.mark.integration` / пропуск без Docker — по политике CI.
