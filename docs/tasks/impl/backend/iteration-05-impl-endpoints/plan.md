# iter-05 — Impl endpoints: план

## Контекст

В iter-04 реализован MVP-код эндпоинтов (слоты, запись) в виде "stub-реализации" с пометками `# iter-05`. Вся бизнес-логика уже находится в `services/`, обработка ошибок подключена, тесты зелёные. iter-05 верифицирует и формализует это как законченный MVP-слой, исправляет оставшиеся замечания и расширяет каталогом услуг.

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
