# iter-04 — API tests MVP: итоги

## Что реализовано (исходный срез MVP)

### Тесты (`backend/tests/`)
- **`conftest.py`** — `client` (session-scope TestClient), `auth_override` (dependency override для `get_current_user`). *После закрытия этапа 1:* фикстура **PostgreSQL** (Testcontainers) + Alembic + seed; между тестами — `TRUNCATE` записей/визитов/бонусов; `ADMIN_API_TOKEN` для сценариев админа; `get_settings.cache_clear` при смене `DATABASE_URL`.
- **`test_health.py`** — 1 тест: `GET /health` → 200
- **`test_slots.py`** — 5 тестов: рабочий день → список > 0; поля `starts_at`/`ends_at`; выходной → пустой список; отсутствие `date_to` → 422; отсутствие `service_ids` → 422; занятый слот исчезает из выдачи
- **`test_appointments.py`** — 6 тестов: happy path → 201 с корректным телом; `ends_at` = `starts_at` + длительность; второй запрос на тот же слот → 409 + `SLOT_NOT_AVAILABLE`; неизвестная услуга → 422; без токена → 401; два непересекающихся слота → оба 201
- **`test_services.py`** — 3 теста на каталог услуг (добавлено в рамках iter-05, остаётся в общем прогоне)

### Дополнение (согласовано с tasklist-backend и закрытием этапа 1)

- **`test_visit_confirm.py`** — 1 интеграционный тест: `POST /auth/telegram` → запись → `POST /admin/visits` → баланс бонусов на `GET /me/bonus-account` (только при PostgreSQL в фикстуре).

### Stub-реализация MVP-endpoint'ов (iter-04)
- **`api/v1/schemas.py`** — Pydantic-схемы: `AppointmentStatus(StrEnum)`, `ServiceLineItem`, `SlotWindow`, `SlotListResponse`, `AppointmentCreateRequest`, `Appointment`
- **`api/v1/deps.py`** — заглушка `get_current_user`: без токена → 401; с токеном → далее поддержка `BOT_SECRET` и `mvp-*` (расширено в последующих итерациях)
- **`storage/memory.py`** — in-memory хранилище: предзаполненная услуга `DEFAULT_SERVICE_ID` (60 мин, 2000 руб.), расписание Пн–Пт 09:00–18:00, функции `get_services()` / `get_appointments()` / `add_appointment()` / `reset_appointments()`
- **`services/slot_service.py`** — `get_free_slots()`: итерация по дням → генерация окон с шагом 30 мин → фильтрация занятых
- **`services/appointment_service.py`** — `create_appointment()`: валидация услуг → расчёт длительности и цены → проверка конфликта → сохранение
- **`api/v1/router.py`** — маршруты `GET /api/v1/slots` и `POST /api/v1/appointments` (+ далее каталог и подключение `routes_extended`)
- **`main.py`** — кастомный `http_exception_handler`: приводит `HTTPException.detail` к формату контракта `{"error": {"code": ..., "message": ...}}`

## Итог прогона (актуально на закрытие этапа 1)

```
16 passed (сессия с PostgreSQL в conftest)
ruff: All checks passed!
```

*Ранее исходный MVP-only прогон без контейнера был короче (порядка 12–13 тестов без PG-фикстуры).*

## Отклонения от плана

Исходный `plan.md` предполагал только in-memory и `reset_storage`. Фактически для стабильной проверки этапа 1 тесты опираются на **Testcontainers PostgreSQL** (см. `conftest.py`). Это зафиксировано в [`tasklist-backend.md`](../../../tasklist-backend.md) (iter-04).

## Принятые решения

- **In-memory stub** остаётся путём для быстрых прогонов без Docker; полный набор маршрутов этапа 1 проверяется на PostgreSQL.
- **`AppointmentStatus(StrEnum)`** — вместо `(str, Enum)` по требованию ruff UP042 (Python 3.11+).
- **Кастомный exception handler** в `main.py` — преобразует `HTTPException.detail` в формат контракта без изменения кода сервисов; не затрагивает Pydantic validation (422 от `RequestValidationError` остаётся стандартным).
- **`auth_override` как отдельный pytest-fixture** — тесты, требующие авторизации, запрашивают его явно; тест на 401 использует только `client`.
- **`scope="session"` у `client`** — TestClient создаётся один раз за сессию (с поднятым PG).

## Артефакты

- [`backend/src/pereobuyka/api/v1/schemas.py`](../../../../../backend/src/pereobuyka/api/v1/schemas.py)
- [`backend/src/pereobuyka/api/v1/deps.py`](../../../../../backend/src/pereobuyka/api/v1/deps.py)
- [`backend/src/pereobuyka/api/v1/router.py`](../../../../../backend/src/pereobuyka/api/v1/router.py) *(обновлён)*
- [`backend/src/pereobuyka/storage/memory.py`](../../../../../backend/src/pereobuyka/storage/memory.py)
- [`backend/src/pereobuyka/services/slot_service.py`](../../../../../backend/src/pereobuyka/services/slot_service.py)
- [`backend/src/pereobuyka/services/appointment_service.py`](../../../../../backend/src/pereobuyka/services/appointment_service.py)
- [`backend/src/pereobuyka/main.py`](../../../../../backend/src/pereobuyka/main.py) *(обновлён)*
- [`backend/tests/conftest.py`](../../../../../backend/tests/conftest.py)
- [`backend/tests/test_health.py`](../../../../../backend/tests/test_health.py)
- [`backend/tests/test_slots.py`](../../../../../backend/tests/test_slots.py)
- [`backend/tests/test_appointments.py`](../../../../../backend/tests/test_appointments.py)
- [`backend/tests/test_services.py`](../../../../../backend/tests/test_services.py)
- [`backend/tests/test_visit_confirm.py`](../../../../../backend/tests/test_visit_confirm.py)
