# iter-05 — Impl endpoints: план

## Контекст

В iter-04 реализован базовый код эндпоинтов (слоты, запись) в виде "stub-реализации" с пометками `# iter-05`. Вся бизнес-логика уже находится в `services/`, обработка ошибок подключена, тесты зелёные. iter-05 верифицирует и формализует это как законченный базовый слой, исправляет оставшиеся замечания и расширяет каталогом услуг.

## Что будет сделано

### 1. Формализация временного слоя хранилища

`tasklist-database.md` не существует → БД-слой не планируется в текущем цикле. Временный in-memory storage фиксируется как **явная архитектурная позиция** (не "заглушка для iter-05", а "временный слой до появления database-tasklist"). Комментарии в коде обновляются соответственно.

### 2. Исправление UTC datetime

`datetime.now()` в `appointment_service.py` заменяется на `datetime.now(timezone.utc)` — timezone-aware, согласованно с лучшими практиками и будущим SQLAlchemy/PostgreSQL-слоем.

### 3. GET /api/v1/services — каталог услуг

Добавляется endpoint из сценария **Клиент 3** (`iter-02`): список активных услуг для UI и расчёта.

**Схема ответа:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "duration_minutes": 60,
      "price": "2000.00",
      "is_active": true
    }
  ]
}
```

Публичный endpoint (авторизация не требуется).

### 4. Тест GET /api/v1/services

- Возвращает 200 и список с хотя бы одной услугой
- Обязательные поля: `id`, `name`, `duration_minutes`, `price`, `is_active`
- Только активные услуги присутствуют

## Файлы к изменению / созданию

| Файл | Действие |
|------|----------|
| `backend/src/pereobuyka/api/v1/schemas.py` | Добавить `ServiceItem`, `ServiceListResponse` |
| `backend/src/pereobuyka/api/v1/router.py` | Добавить `GET /services` |
| `backend/src/pereobuyka/services/slot_service.py` | Обновить комментарий |
| `backend/src/pereobuyka/services/appointment_service.py` | UTC fix + обновить комментарий |
| `backend/src/pereobuyka/storage/memory.py` | Обновить docstring/комментарий |
| `backend/tests/test_services.py` | Создать новый файл с тестами |

## DoD

- `make backend-test`: все тесты зелёные (включая новые)
- `make backend-lint`: All checks passed
- Через `/docs` работает happy-path: слоты → запись, а также каталог услуг

---

## Дополнение — завершение этапа 1 (факт)

Исходный план выше описывает **первую волну** (базовый срез + `GET /services`). По [`tasklist-backend.md`](../../../tasklist-backend.md) итерация iter-05 дополнена **полным срезом API для PostgreSQL**:

- подроутеры и [`routes_extended`](../../../../../backend/src/pereobuyka/api/v1/routes_extended.py), модули [`api/v1/endpoints/`](../../../../../backend/src/pereobuyka/api/v1/endpoints/);
- репозитории в [`storage/repositories/`](../../../../../backend/src/pereobuyka/storage/repositories/), сервисы `visit_commands`, `auth_user_pg`, [`api_adapters`](../../../../../backend/src/pereobuyka/services/api_adapters.py);
- авторизация клиента/бота/админа (`deps`, `deps_extra`, `ADMIN_API_TOKEN`, seed админа);
- интеграционные тесты вместе с iter-04: **16 passed** при прогоне с PostgreSQL (Testcontainers).

Детали и перечень артефактов — в [`summary.md`](summary.md) (разделы A и B).
