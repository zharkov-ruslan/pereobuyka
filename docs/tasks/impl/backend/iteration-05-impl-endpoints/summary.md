# iter-05 — Impl endpoints: итоги

Итерация в два слоя: **(A)** формализация базового среза и каталог услуг; **(B)** закрытие этапа 1 по backend — полный набор маршрутов для PostgreSQL, репозитории и сервисы (см. [`tasklist-backend.md`](../../../tasklist-backend.md), раздел iter-05).

## A. Базовая волна (исходный scope плана)

### Формализация временного слоя хранилища

In-memory зафиксирован как явный временный слой до полноценной работы только через БД. Комментарии `# iter-05: заменить на реальный storage` убраны; в docstring — явная пометка о роли слоя.

Затронутые файлы: `storage/memory.py`, `services/slot_service.py`, `services/appointment_service.py`.

### UTC-aware datetime

`datetime.now()` → `datetime.now(UTC)` в `appointment_service.py` (ruff UP017).

### GET /api/v1/services — каталог услуг

- Роут: `GET /api/v1/services` (сценарий **Клиент 3** iter-02)
- Ответ: `ServiceListResponse { items: ServiceItem[] }`; активные услуги; при полном режиме PG — также поля вроде `description` по контракту

Схемы в `api/v1/schemas.py`: `ServiceItem`, `ServiceListResponse` (и расширения под OpenAPI по мере этапа 1).

### Тесты каталога

`backend/tests/test_services.py` — 3 теста на публичный каталог.

## B. Завершение этапа 1 (PostgreSQL)

- **Роутинг:** `api/v1/router.py` (каталог, слоты, запись) + подключение [`routes_extended.py`](../../../../../backend/src/pereobuyka/api/v1/routes_extended.py); маршруты разнесены по [`api/v1/endpoints/`](../../../../../backend/src/pereobuyka/api/v1/endpoints/) (`auth`, `client`, `admin`, `consultation`, `common`).
- **Репозитории:** [`storage/repositories/postgres.py`](../../../../../backend/src/pereobuyka/storage/repositories/postgres.py) (`PostgresAppointmentRepository`, `PostgresServiceRepository`, `PostgresScheduleRepository` и связанная логика); слой [`postgres_repos.py`](../../../../../backend/src/pereobuyka/storage/postgres_repos.py) там, где он используется каркасом.
- **Сервисы:** подтверждение визита и бонусы — [`visit_commands.py`](../../../../../backend/src/pereobuyka/services/visit_commands.py); регистрация/пользователь в PG — [`auth_user_pg.py`](../../../../../backend/src/pereobuyka/services/auth_user_pg.py); маппинг ORM ↔ API — [`api_adapters.py`](../../../../../backend/src/pereobuyka/services/api_adapters.py).
- **Авторизация:** `deps.py` / [`deps_extra.py`](../../../../../backend/src/pereobuyka/api/v1/deps_extra.py) — клиентский Bearer-токен после auth, `BOT_SECRET` + `X-Telegram-User-Id`, админ — `ADMIN_API_TOKEN` и актёр админа из seed.
- **Seed:** пользователь-админ под `ADMIN_ACTOR_USER_ID` в [`scripts/seed.py`](../../../../../backend/src/pereobuyka/scripts/seed.py); переменные окружения — в [`backend/.env.example`](../../../../../backend/.env.example).

In-memory/SQLite остаётся для раннего базового среза (каталог/слоты/запись без полного набора); полный контракт — при `DATABASE_URL` на PostgreSQL.

## Итог прогона

```
16 passed
make backend-lint → All checks passed!
```

(В исходной базовой волне было меньше тестов и короче время без PG-фикстуры.)

## Отклонения от исходного `plan.md`

Исходный `plan.md` описывал только **волну A** (формализация in-memory, UTC, `GET /services`). **Волна B** зафиксирована в [`tasklist-backend.md`](../../../tasklist-backend.md) и в дополнении к [`plan.md`](plan.md) этой итерации.

## Принятые решения

- **`datetime.UTC`** — ruff UP017 (Python 3.11+).
- **Каталог услуг** без обязательной авторизации — соответствует vision §4 Клиент 3.
- **Разнесение эндпоинтов по пакету `endpoints/`** — читаемость и масштабирование при полном OpenAPI этапа 1.

## Артефакты (ключевые)

- [`backend/src/pereobuyka/api/v1/schemas.py`](../../../../../backend/src/pereobuyka/api/v1/schemas.py)
- [`backend/src/pereobuyka/api/v1/router.py`](../../../../../backend/src/pereobuyka/api/v1/router.py)
- [`backend/src/pereobuyka/api/v1/routes_extended.py`](../../../../../backend/src/pereobuyka/api/v1/routes_extended.py)
- [`backend/src/pereobuyka/api/v1/endpoints/`](../../../../../backend/src/pereobuyka/api/v1/endpoints/)
- [`backend/src/pereobuyka/storage/repositories/`](../../../../../backend/src/pereobuyka/storage/repositories/)
- [`backend/src/pereobuyka/services/visit_commands.py`](../../../../../backend/src/pereobuyka/services/visit_commands.py)
- [`backend/tests/test_services.py`](../../../../../backend/tests/test_services.py)
- Базовый слой: [`services/appointment_service.py`](../../../../../backend/src/pereobuyka/services/appointment_service.py), [`services/slot_service.py`](../../../../../backend/src/pereobuyka/services/slot_service.py), [`storage/memory.py`](../../../../../backend/src/pereobuyka/storage/memory.py)
