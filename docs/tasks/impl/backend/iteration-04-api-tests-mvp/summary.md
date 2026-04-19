# iter-04 — API tests MVP: итоги

## Что реализовано

### Тесты (`backend/tests/`)
- **`conftest.py`** — `client` (session-scope TestClient), `auth_override` (dependency override для `get_current_user`), `reset_storage` (autouse — очистка in-memory перед каждым тестом)
- **`test_health.py`** — 1 тест: `GET /health` → 200
- **`test_slots.py`** — 6 тестов: рабочий день → список > 0; поля `starts_at`/`ends_at`; выходной → пустой список; отсутствие `date_to` → 422; отсутствие `service_ids` → 422; занятый слот исчезает из выдачи
- **`test_appointments.py`** — 6 тестов: happy path → 201 с корректным телом; `ends_at` = `starts_at` + длительность; второй запрос на тот же слот → 409 + `SLOT_NOT_AVAILABLE`; неизвестная услуга → 422; без токена → 401; два непересекающихся слота → оба 201

### Stub-реализация MVP-endpoint'ов
- **`api/v1/schemas.py`** — Pydantic-схемы: `AppointmentStatus(StrEnum)`, `ServiceLineItem`, `SlotWindow`, `SlotListResponse`, `AppointmentCreateRequest`, `Appointment`
- **`api/v1/deps.py`** — заглушка `get_current_user`: без токена → 401; с токеном → 401 до реализации JWT (переопределяется в тестах)
- **`storage/memory.py`** — in-memory хранилище: предзаполненная услуга `DEFAULT_SERVICE_ID` (60 мин, 2000 руб.), расписание Пн–Пт 09:00–18:00, функции `get_services()` / `get_appointments()` / `add_appointment()` / `reset_appointments()`
- **`services/slot_service.py`** — `get_free_slots()`: итерация по дням → генерация окон с шагом 30 мин → фильтрация занятых
- **`services/appointment_service.py`** — `create_appointment()`: валидация услуг → расчёт длительности и цены → проверка конфликта → сохранение
- **`api/v1/router.py`** — маршруты `GET /api/v1/slots` и `POST /api/v1/appointments`
- **`main.py`** — кастомный `http_exception_handler`: приводит `HTTPException.detail` к формату контракта `{"error": {"code": ..., "message": ...}}`

## Итог прогона

```
13 passed in 0.12s
ruff: All checks passed!
```

## Отклонения от плана

Нет. Реализация полностью соответствует `plan.md`.

## Принятые решения

- **In-memory stub явно помечен** комментариями `# iter-05: заменить на реальный storage` — видна точка расширения.
- **`AppointmentStatus(StrEnum)`** — вместо `(str, Enum)` по требованию ruff UP042 (Python 3.11+).
- **Кастомный exception handler** в `main.py` — преобразует `HTTPException.detail` в формат контракта без изменения кода сервисов; не затрагивает Pydantic validation (422 от `RequestValidationError` остаётся стандартным).
- **`auth_override` как отдельный pytest-fixture** — тесты, требующие авторизации, запрашивают его явно; тест на 401 использует только `client`.
- **`scope="session"` у `client`** — TestClient создаётся один раз за сессию.

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
