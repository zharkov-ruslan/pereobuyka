# iter-be-04 — API tests: план

## Цель

Написать автотесты на базовые endpoint'ы (`/health`, `GET /api/v1/slots`, `POST /api/v1/appointments`) и обеспечить их зелёный прогон. Логика реализована в in-memory хранилище (stub), не в БД — это явная временная точка, которую iter-be-05 заменит на реальный storage.

## Подход

TDD-наоборот: endpoint'ов ещё нет → одновременно добавляем минимальную реализацию + тесты. Бизнес-правила (расчёт слотов, конфликт записей) проверяются через HTTP-контракт. Зависимость `get_current_user` оверрайдится в тестах через `app.dependency_overrides`.

## Файлы: создаются

| Файл | Назначение |
|------|-----------|
| `backend/src/pereobuyka/api/v1/schemas.py` | Pydantic-схемы по контракту iter-be-02 (SlotWindow, Appointment, …) |
| `backend/src/pereobuyka/api/v1/deps.py` | `get_current_user` — заглушка для авторизации |
| `backend/src/pereobuyka/storage/memory.py` | In-memory репозиторий услуг, расписания, записей |
| `backend/src/pereobuyka/services/slot_service.py` | Расчёт свободных слотов |
| `backend/src/pereobuyka/services/appointment_service.py` | Создание записи с проверкой конфликта |
| `backend/tests/__init__.py` | Пустой init |
| `backend/tests/conftest.py` | Фикстуры: `client`, `auth_override`, `reset_storage` |
| `backend/tests/test_health.py` | Тест `/health` |
| `backend/tests/test_slots.py` | Тесты `GET /api/v1/slots` |
| `backend/tests/test_appointments.py` | Тесты `POST /api/v1/appointments` |

## Файлы: изменяются

| Файл | Изменение |
|------|-----------|
| `backend/src/pereobuyka/api/v1/router.py` | Добавить маршруты `/slots` и `/appointments` |

## In-memory stub: ключевые допущения

- **Услуги** — предзасеяны одной записью: `DEFAULT_SERVICE_ID`, 60 мин, 2000 руб.
- **Расписание** — Пн–Пт 09:00–18:00, шаг слота 30 мин.
- **Записи** — список в памяти, очищается между тестами.
- **Авторизация** — `get_current_user` возвращает 401 без токена; тесты оверрайдят на `FAKE_USER_ID`.

Эти допущения явно помечены в коде (`# iter-be-05: заменить на реальный storage`).

## Сценарии тестов

### `/health`
- `GET /health` → 200, `{"status": "ok"}`

### `GET /api/v1/slots`
- Рабочий день (пн) + существующая услуга → 200, список > 0 слотов; каждый слот содержит `starts_at`, `ends_at`
- Выходной день → 200, пустой список
- Отсутствие обязательных параметров → 422

### `POST /api/v1/appointments`
- Happy path (свободный слот, есть токен) → 201, корректное тело `Appointment`
- Повторная запись на тот же слот → 409, `{"error": {"code": "SLOT_NOT_AVAILABLE", …}}`
- Несуществующая услуга → 422
- Без Authorization → 401

## Definition of Done

- `make backend-test` проходит без ошибок
- `make backend-lint` без предупреждений

---

## Дополнение (актуализация под этап 1)

После расширения backend ([`tasklist-backend.md`](../../../tasklist-backend.md), iter-be-04–iter-be-05) прогон тестов включает **PostgreSQL** (Testcontainers) в [`backend/tests/conftest.py`](../../../../../backend/tests/conftest.py), файл `test_visit_confirm.py` и **16** успешных тестов на сессию. Исходная цель итерации (базовый срез: health, слоты, запись на stub) сохраняется; интеграционные проверки визита/бонусов добавлены как следующий слой покрытия.
