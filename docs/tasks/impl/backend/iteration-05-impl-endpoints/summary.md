# iter-05 — Impl endpoints: итоги

## Что реализовано

### Формализация временного слоя хранилища

`tasklist-database.md` отсутствует → in-memory хранилище зафиксировано как **явный временный MVP-слой** (не «заглушка»). Комментарии вида `# iter-05: заменить на реальный storage` убраны из всех файлов; добавлена явная пометка о переходе в рамках database-tasklist.

Затронутые файлы:
- `storage/memory.py` — обновлён docstring
- `services/slot_service.py` — обновлён docstring
- `services/appointment_service.py` — обновлён docstring

### UTC-aware datetime

`datetime.now()` → `datetime.now(UTC)` в `appointment_service.py`; импорт изменён на `from datetime import UTC, datetime, timedelta` (требование ruff UP017).

### GET /api/v1/services — каталог услуг

Новый публичный endpoint (сценарий **Клиент 3** из iter-02):

- **Роут:** `GET /api/v1/services`
- **Ответ:** `ServiceListResponse { items: ServiceItem[] }`
- **ServiceItem:** `id`, `name`, `duration_minutes`, `price`, `is_active`
- Возвращает только активные услуги (`is_active == True`)

Новые схемы в `api/v1/schemas.py`: `ServiceItem`, `ServiceListResponse`.

### Тесты GET /api/v1/services

`backend/tests/test_services.py` — 3 теста:
1. Возвращает 200 со списком, содержащим хотя бы одну услугу
2. Элемент содержит все обязательные поля
3. Все элементы активны (`is_active == true`)

## Итог прогона

```
All checks passed!
15 passed in 0.11s
```

## Отклонения от плана

Нет. Реализация соответствует `plan.md`.

## Принятые решения

- **`datetime.UTC`** вместо `timezone.utc` — требование ruff UP017 для Python 3.11+.
- **Временный слой** явно задокументирован без привязки к номеру итерации — точка расширения видна в docstring, не в артефакте планирования.
- **Каталог услуг** реализован как публичный endpoint (без `Depends(get_current_user)`) — соответствует vision §4 Клиент 3: просмотр прайса доступен без авторизации.

## Артефакты

- [`backend/src/pereobuyka/api/v1/schemas.py`](../../../../../backend/src/pereobuyka/api/v1/schemas.py) — добавлены `ServiceItem`, `ServiceListResponse`
- [`backend/src/pereobuyka/api/v1/router.py`](../../../../../backend/src/pereobuyka/api/v1/router.py) — добавлен `GET /services`
- [`backend/src/pereobuyka/services/appointment_service.py`](../../../../../backend/src/pereobuyka/services/appointment_service.py) — UTC fix, обновлён docstring
- [`backend/src/pereobuyka/services/slot_service.py`](../../../../../backend/src/pereobuyka/services/slot_service.py) — обновлён docstring
- [`backend/src/pereobuyka/storage/memory.py`](../../../../../backend/src/pereobuyka/storage/memory.py) — обновлён docstring
- [`backend/tests/test_services.py`](../../../../../backend/tests/test_services.py) — новый файл, 3 теста
