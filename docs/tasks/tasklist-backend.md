# Tasklist: Backend

## Область: backend

Backend — ядро системы «Переобуйка»: бизнес-правила, расписание, прайс, записи, лояльность, API для каналов. Telegram-бот и веб — клиенты backend и не содержат бизнес-логики.

**Опорные документы:** [`docs/vision.md`](../vision.md) · [`docs/tech/data-model.md`](../tech/data-model.md) · [`docs/tech/integrations.md`](../tech/integrations.md)

**Базовая реализация** (итерации реализации и тестов ниже): изначально — **свободные слоты** и **создание записи** (см. [`docs/tech/data-model.md`](../tech/data-model.md): `Schedule`, расчёт длительности, `Appointment`). **Проектирование контрактов** в **iter-be-02** — **полный охват** сценариев клиента и администратора из [`docs/vision.md`](../vision.md) §4, согласованный с `data-model`.

### Статус этапа 1 ([`docs/plan.md`](../plan.md))

**Этап 1 — «Фундамент: backend и модель данных» по области backend закрыт:** реализованы маршруты из [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml) для режима **PostgreSQL** (клиент: регистрация Telegram, профиль, записи, визиты, лояльность; админ: услуги, расписание, исключения, журнал, подтверждение визита, бонусы). In-memory/SQLite сохраняют ранний базовый срез (каталог, слоты, запись без полного набора). Репозитории: [`backend/src/pereobuyka/storage/repositories/`](../../backend/src/pereobuyka/storage/repositories/); эндпоинты разнесены по [`backend/src/pereobuyka/api/v1/endpoints/`](../../backend/src/pereobuyka/api/v1/endpoints/). Отложенные улучшения (DDD, mypy в CI, расширение тестов) — [`docs/backlog.md`](../backlog.md).

---

## Рекомендация по skills

На этапах **выбора стека** и **проектирования API** уместно подбирать Cursor skills под задачу (тесты, OpenAPI, конкретный фреймворк). Подбор: команда **`/find-skills`** и уточнение по формулировке сценария.

---

## Связь с `docs/plan.md`

| Этап в [`docs/plan.md`](../plan.md) | Роль этого tasklist |
|-------------------------------------|---------------------|
| **1** — Фундамент: backend и модель данных | ✅ Закрыт по backend: стек, контракт iter-be-02, каркас, **полная реализация API этапа 1** (PostgreSQL), репозитории, тесты, документация; см. статус этапа 1 выше |
| **2** — Telegram-бот | Пересечение: **iter-be-07** — бот переводится на HTTP к backend; остальное — отдельные tasklist’ы по боту/интеграциям |
| **3+** | Контракты и сервисы расширяются; см. раздел «Дальнейшие итерации» |

---

## Легенда статусов

| Иконка | Статус | Значение |
|--------|--------|----------|
| ⚪ | `planned` | Запланировано, работа не начата |
| 🔄 | `in-progress` | Итерация в работе |
| 🔴 | `blocked` | Заблокировано внешней зависимостью |
| ✅ | `done` | Итерация завершена и верифицирована |

---

## Сводная таблица итераций

Соответствие шагам дорожной работы: **1 → 2 → 4 → 5 → 6 → 7 → 8 → 9** (п.3 в исходном списке отсутствует — нумерация ниже явная).

| ID | Итерация | Статус | Зависимости | Ключевые артефакты |
|----|----------|--------|-------------|-------------------|
| [iter-be-01](#iter-be-01-стек-и-соглашения) | Стек и соглашения | ✅ done | — | [ADR-002](../tech/adr/adr-002-backend-framework.md), [ADR-003](../tech/adr/adr-003-orm.md), `.cursor/rules/convensions.mdc`, `docs/vision.md` |
| [iter-be-02](#iter-be-02-контракты-api-vision-клиент-админ) | Контракты API (vision: клиент + админ) | ✅ done | iter-be-01 | [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml), [`docs/tech/api/errors.md`](../tech/api/errors.md), матрица в секции iter-be-02 |
| [iter-be-03](#iter-be-03-каркас-backend) | Каркас backend | ✅ done | iter-be-02* | `backend/`, health, `Makefile` |
| [iter-be-04](#iter-be-04-тесты-api) | Тесты API | ✅ done | iter-be-03 | `tests/`: базовый срез (слоты, запись) + интеграция **визит/бонусы** на PostgreSQL |
| [iter-be-05](#iter-be-05-реализация-endpoints) | Реализация endpoints | ✅ done | iter-be-04 | базовый срез → **полный срез этапа 1** (PG): роутеры, сервисы, репозитории, ORM |
| [iter-be-06](#iter-be-06-документация-backend) | Документация backend | ✅ done | iter-be-05 | README, `.env.example`, OpenAPI, `docs/plan.md` (ссылки) |
| [iter-be-07](#iter-be-07-бот-через-api) | Бот через API | ✅ done | iter-be-06 | Тонкие handlers, HTTP-клиент |
| [§ Качество](#качество-и-инженерные-практики) | Качество (сквозное) | — | весь цикл | ruff, pytest, Makefile |

\*Каркас технически может начаться после iter-be-01; контракт iter-be-02 должен быть согласован до стабилизации путей и схем в коде.

---

## Итерации

### iter-be-01 — Стек и соглашения

**Шаг дорожной карты:** 1

**Цель:** Зафиксировать backend-стек (фреймворк, валидация, OpenAPI, ORM и миграции), ключевые архитектурные решения и обновить проектные соглашения.

**Ценность:** Снимается неопределённость по стеку; агенты и люди опираются на одинаковые правила в `.cursor/rules` и vision.

**Состав работ**

- [x] Сравнить варианты (например FastAPI / Litestar / др.) по зрелости, OpenAPI, `uv`/Python 3.12
- [x] Оформить ADR (например `docs/tech/adr/adr-00X-backend-framework.md`) и добавить в [`docs/tech/adr/README.md`](../tech/adr/README.md)
- [x] Обновить [`.cursor/rules/convensions.mdc`](../../.cursor/rules/convensions.mdc): слой API/роутеров, зависимости, тесты — без противоречия [`docs/vision.md`](../vision.md)
- [x] Обновить строку «Backend-фреймворк» в [`docs/vision.md`](../vision.md)
- [x] Оформить ADR по ORM и миграциям ([`docs/tech/adr/adr-003-orm.md`](../tech/adr/adr-003-orm.md)), связать с [ADR-001](../tech/adr/adr-001-database.md) и реестром ADR; обновить строку стека в [`docs/vision.md`](../vision.md)

**Артефакты**

- [`docs/tech/adr/adr-002-backend-framework.md`](../tech/adr/adr-002-backend-framework.md) — ADR по HTTP-фреймворку
- [`docs/tech/adr/adr-003-orm.md`](../tech/adr/adr-003-orm.md) — ADR по ORM и миграциям
- [`docs/tech/adr/adr-001-database.md`](../tech/adr/adr-001-database.md) — обновлён (миграции ↔ ADR-003)
- [`docs/vision.md`](../vision.md) — строки стека, таблица ADR, §12
- [`.cursor/rules/convensions.mdc`](../../.cursor/rules/convensions.mdc)

**Документы**

- [plan.md](impl/backend/iteration-01-stack-conventions/plan.md)
- [summary.md](impl/backend/iteration-01-stack-conventions/summary.md)

**Definition of Done — агент**

- ADR по стеку приняты и связаны с реестром ADR (в т.ч. HTTP-фреймворк и ORM/миграции); в `docs/vision.md` отражены фреймворк и доступ к БД
- `convensions.mdc` отражает стек и границы слоёв (handlers / services / storage / llm) согласно vision

**Definition of Done — пользователь**

- Открыть ADR и раздел стека в `docs/vision.md` — решение явное и воспроизводимое
- Убедиться, что правила в `.cursor/rules/convensions.mdc` читаются без противоречий с vision

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Согласованность ссылок vision ↔ ADR ↔ rules | Чтение ADR и vision | — | `docs/tech/adr/`, `docs/vision.md`, `.cursor/rules/convensions.mdc` |

---

### iter-be-02 — Контракты API (vision: клиент + админ)

**Шаг дорожной карты:** 2

**Цель:** Зафиксировать **полный набор** публичных API-контрактов (клиент и администратор), покрывающий сценарии из [`docs/vision.md`](../vision.md) §4, в согласованности с [`docs/tech/data-model.md`](../tech/data-model.md).

**Ценность:** Бот, веб и админка могут проектироваться против единого контракта; изменения — осознанные. Реализация endpoint’ов шла поэтапно (**iter-be-05**: базовый срез → полный срез этапа 1 для PostgreSQL).

**Опора на сущности:** `User`, `Service`, `Schedule`, `Appointment`, `Visit`, `BonusAccount`, `BonusTransaction`, `FAQ` — уточнение полей под контракт при необходимости в `data-model`.

**Матрица «сценарий vision → сущности / фокус контракта»**

| Vision | Сущности и фокус |
|--------|------------------|
| Клиент 1 — Регистрация | `User`; идентификация по каналу (`telegram_id` / веб), поля профиля; при необходимости upsert при первом контакте |
| Клиент 2 — Консультация (LLM) | Эндпоинт с сообщением пользователя; сервер подмешивает контекст (прайс, слоты, бонусы, `FAQ`) по vision §6; контракт **не заменяет** эндпоинты фактов (каталог, слоты) |
| Клиент 3 — Услуги и цены | `Service` — каталог активных услуг для отображения и расчёта |
| Клиент 4 — Запись | `Schedule`, `Service`, `Appointment` — свободные окна + создание записи |
| Клиент 5 — Просмотр / отмена записей | `Appointment` — список, фильтры, отмена |
| Клиент 6 — После визита | `Appointment`, `Visit`, транзакции — история для клиента; push в Telegram — см. [`docs/tech/integrations.md`](../tech/integrations.md), не обязательно отдельный API |
| Клиент 7 — Лояльность | `BonusAccount`, `BonusTransaction`, правила списания/начисления |
| Админ 1 — Прайс | `Service` — CRUD |
| Админ 2 — Расписание | `Schedule` — шаблоны и исключения |
| Админ 3 — Журнал записей | `Appointment` — список, фильтры, загрузка |
| Админ 4 — Подтверждение услуг | `Visit`, связь с `Appointment`, услуги визита, бонусы |
| Админ 5 — Бонусы | `BonusAccount`, `BonusTransaction` (`adjust`, комментарий) |

**Состав работ — клиент** ([`docs/vision.md`](../vision.md) §4)

- [x] **1. Регистрация:** запрос/ответ/ошибки — создание или upsert профиля `User`, связка канала (Telegram / веб) согласно data-model
- [x] **2. Консультация (LLM):** запрос/ответ; явно: сервер не отдаёт «придуманные» цены/слоты; описать источники контекста (прайс, слоты, бонусы, FAQ) и отличие от прямых эндпоинтов фактов
- [x] **3. Услуги и цены:** каталог `Service` (активные услуги, поля для UI и расчёта)
- [x] **4. Запись:** запрос/ответ для **свободных слотов** — дата или диапазон, идентификаторы услуг, суммарная длительность, формат окон (начало/конец); запрос/ответ для **создания записи** — клиент, слот, список услуг, `starts_at` / `ends_at` / `total_price`, статусы
- [x] **5. Просмотр / отмена записей:** список записей клиента, отмена (`status` или иной согласованный способ), коды ошибок
- [x] **6. После визита:** чтение истории (записи, визиты, суммы, бонусы); при необходимости зафиксировать, что уведомления — канал бота/integrations, не отдельный публичный API
- [x] **7. Лояльность:** баланс, правила (лимиты списания, начисление), история `BonusTransaction` (read-only для клиента)

**Состав работ — администратор** ([`docs/vision.md`](../vision.md) §4)

- [x] **1. Прайс:** CRUD `Service` (цена, длительность, активность), список с фильтрами
- [x] **2. Расписание:** CRUD `Schedule` (шаблон по дням недели + исключения: дата, выходной, особые часы)
- [x] **3. Журнал записей:** выборка `Appointment` с фильтрами (дата, статус и т.д.), параметры для «загрузки» без привязки к конкретному UI
- [x] **4. Подтверждение услуг:** фиксация `Visit` по записи — итог, фактические услуги, начисление/списание бонусов
- [x] **5. Бонусы:** просмотр счёта, ручная корректировка с типом `adjust`, комментарием и аудитопригодными полями

**Состав работ — сквозное**

- [x] **Авторизация и роли:** зафиксировать подход (заголовки, токен, Telegram-initData и т.д.) и разделение публичных vs защищённых эндпоинтов — без обязательной реализации в iter-be-02
- [x] **Единая модель ошибок:** HTTP 401/403/404/409/422 и доменные коды (занят слот, недоступна услуга, недостаточно бонусов и т.д.)
- [x] **Версионирование:** префикс (`/api/v1/...`) и правила изменения контракта
- [x] **Текстовая спецификация контрактов:** [`docs/tech/api/api-contracts.md`](../tech/api/api-contracts.md) — полное описание эндпоинтов и соглашений (дополняет OpenAPI)

**Артефакты**

- [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml) — OpenAPI 3.0.3
- [`docs/tech/api/errors.md`](../tech/api/errors.md) — модель ошибок
- [`docs/tech/api/README.md`](../tech/api/README.md) — индекс API-документации
- [`docs/tech/api/api-contracts.md`](../tech/api/api-contracts.md) — текстовое описание контрактов

**Документы**

- [plan.md](impl/backend/iteration-02-api-contracts/plan.md)
- [summary.md](impl/backend/iteration-02-api-contracts/summary.md)

**Definition of Done — агент**

- Однозначные схемы (Pydantic/OpenAPI или YAML) для **каждого пункта** чеклистов выше (или явное исключение с обоснованием — только для некритичных границ, согласованных с vision)
- Контракт согласован с перечисленными сущностями data-model; матрица сценариев vision покрыта документом или OpenAPI
- Спот-чек: каждый сценарий vision §4 (клиент и админ) имеет отражение в OpenAPI/доке контракта

**Definition of Done — пользователь**

- По контракту понятно, какие запросы/ответы и ошибки соответствуют каждому пользовательскому сценарию из vision §4

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Матрица vision §4 ↔ разделы контракта; отсутствие противоречий с data-model | Просмотр схем/дока API | — | [`docs/tech/api/`](../tech/api/README.md), [`impl/backend/iteration-02-api-contracts/`](impl/backend/iteration-02-api-contracts/) |

---

### iter-be-03 — Каркас backend

**Шаг дорожной карты:** 4

**Цель:** Поднять воспроизводимый каркас сервиса по [`docs/vision.md`](../vision.md) (структура `backend/`, config, health).

**Ценность:** Следующие итерации добавляют логику в готовый каркас.

**Состав работ**

- [x] Инициализировать `backend/` с `pyproject.toml` (`uv`), зависимостями, точкой входа
- [x] Структура пакета: `services/`, `storage/`, `models/` (и заготовка под роутеры по выбранному фреймворку)
- [x] `config.py`: загрузка и валидация env на старте
- [x] `GET /health` (или эквивалент) возвращает успех
- [x] Базовые цели **Makefile**: `backend-install` / `backend-run` / `backend-test` / `backend-lint`

**Артефакты**

- [`backend/pyproject.toml`](../../backend/pyproject.toml) — uv-проект с FastAPI, SQLAlchemy, Alembic и dev-зависимостями
- [`backend/src/pereobuyka/main.py`](../../backend/src/pereobuyka/main.py) — FastAPI app, lifespan, `/health`
- [`backend/src/pereobuyka/config.py`](../../backend/src/pereobuyka/config.py) — pydantic-settings конфигурация
- [`backend/src/pereobuyka/api/v1/router.py`](../../backend/src/pereobuyka/api/v1/router.py) — заготовка APIRouter
- [`backend/.env.example`](../../backend/.env.example) — переменные окружения с комментариями
- [`Makefile`](../../Makefile) — добавлены цели `backend-*`

**Документы**

- [plan.md](impl/backend/iteration-03-scaffold-backend/plan.md)
- [summary.md](impl/backend/iteration-03-scaffold-backend/summary.md)

**Definition of Done — агент**

- Сервер стартует без ручных костылей; health отвечает 200
- `make` (или документированные команды) покрывают установку и запуск

**Definition of Done — пользователь**

- По README можно установить зависимости и запустить backend; health проверяется вручную (curl/браузер)

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Линтер/импорты, отсутствие секретов в репо | Запуск и GET health | `make backend-install`, `make backend-run` (и/или `cd backend && uv run …`) | терминал, `http://…/health` |

---

### iter-be-04 — Тесты API

**Шаг дорожной карты:** 5

**Цель:** Автотесты на **реализованные** в коде endpoint’ы; базовый срез — **слоты + запись**; после закрытия этапа 1 — также сценарий **auth → запись → подтверждение визита → бонусы** на PostgreSQL (Testcontainers).

**Ценность:** Регрессии контракта видны до ручной проверки в Telegram.

**Состав работ**

- [x] Интеграционные или API-тесты: успешный запрос слотов (с фикстурами расписания/услуг)
- [x] Тест создания записи; негативные кейсы (конфликт слота и т.д. по контракту)
- [x] Покрыть то, что бот уже делает сообщениями (при наличии бота — выровнять с реальными handler’ами); при появлении новых реализованных маршрутов — расширять тесты
- [x] Интеграционный тест цепочки этапа 1: `POST /auth/telegram` → запись → `POST /admin/visits` → баланс бонусов ([`backend/tests/test_visit_confirm.py`](../../backend/tests/test_visit_confirm.py)); фикстура PostgreSQL + Alembic + seed, расширенный `TRUNCATE` между тестами

**Артефакты**

- [`backend/src/pereobuyka/api/v1/schemas.py`](../../backend/src/pereobuyka/api/v1/schemas.py) — Pydantic-схемы: `AppointmentStatus`, `ServiceLineItem`, `SlotWindow`, `SlotListResponse`, `AppointmentCreateRequest`, `Appointment`
- [`backend/src/pereobuyka/api/v1/deps.py`](../../backend/src/pereobuyka/api/v1/deps.py) — заглушка `get_current_user` (→ 401; переопределяется в тестах)
- [`backend/src/pereobuyka/api/v1/router.py`](../../backend/src/pereobuyka/api/v1/router.py) — `GET /api/v1/slots`, `POST /api/v1/appointments`
- [`backend/src/pereobuyka/storage/memory.py`](../../backend/src/pereobuyka/storage/memory.py) — in-memory хранилище с предзаполненной услугой и расписанием Пн–Пт 09:00–18:00
- [`backend/src/pereobuyka/services/slot_service.py`](../../backend/src/pereobuyka/services/slot_service.py) — `get_free_slots()`: генерация окон, фильтрация занятых
- [`backend/src/pereobuyka/services/appointment_service.py`](../../backend/src/pereobuyka/services/appointment_service.py) — `create_appointment()`: валидация, расчёт, конфликт-чек
- [`backend/src/pereobuyka/utils.py`](../../backend/src/pereobuyka/utils.py) — `overlaps()`: утилита проверки пересечения интервалов
- [`backend/src/pereobuyka/main.py`](../../backend/src/pereobuyka/main.py) — кастомный `http_exception_handler` → формат контракта `{"error": {…}}`
- [`backend/tests/conftest.py`](../../backend/tests/conftest.py) — `client` (session), `auth_override`, PostgreSQL (Testcontainers) + Alembic + seed, `TRUNCATE` визитов/бонусов/записей между тестами, `ADMIN_API_TOKEN` для админ-сценариев
- [`backend/tests/test_health.py`](../../backend/tests/test_health.py) — 1 тест: `GET /health`
- [`backend/tests/test_slots.py`](../../backend/tests/test_slots.py) — 5 тестов: рабочий/выходной день, 422, исключение занятого слота
- [`backend/tests/test_appointments.py`](../../backend/tests/test_appointments.py) — 6 тестов: happy path, ends_at, 409, 422, 401, два непересекающихся слота
- [`backend/tests/test_visit_confirm.py`](../../backend/tests/test_visit_confirm.py) — 1 тест: полный сценарий визита и начисления бонусов (этап 1)

**Документы**

- [plan.md](impl/backend/iteration-04-api-tests-mvp/plan.md)
- [summary.md](impl/backend/iteration-04-api-tests-mvp/summary.md)

**Definition of Done — агент**

- ✅ Тесты падают при нарушении контракта для покрытых endpoint’ов; CI/локально воспроизводимо
- ✅ `make backend-test`: **16 passed** (на момент закрытия этапа 1); `make backend-lint`: All checks passed

**Definition of Done — пользователь**

- `make backend-test` выполняется и понятен по README

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Зелёные тесты на чистом клоне | Прогон тестов локально | `make backend-test` | вывод pytest |

**Принятые решения**

- In-memory stub явно помечен `# iter-be-05: заменить на реальный storage` во всех затронутых файлах
- `auth_override` — отдельный pytest-фикстур с явным `UUID`-типом; тест на 401 использует только `client`
- `overlaps()` вынесен в `utils.py` — устранено дублирование между сервисами (ревью кода)
- `B008` в `ruff ignore` — ложный позитив для FastAPI-паттерна `Depends`/`Query` в дефолтах

---

### iter-be-05 — Реализация endpoints

**Шаг дорожной карты:** 6

**Цель:** Реализовать серверные endpoint’ы по **контракту iter-be-02**. **Исходная волна (базовый срез):** слоты, запись, каталог услуг, in-memory/SQLite. **Завершение этапа 1:** при `DATABASE_URL` PostgreSQL — **все маршруты OpenAPI** для клиента и администратора (см. матрицу iter-be-02), репозитории SQLAlchemy, подтверждение визита и лояльность, разнесение роутов по модулям.

**Ценность:** Backend — единая точка правды для записи, расписания, прайса и бонусов; бот и следующие каналы подключаются к готовому API без доработки доменной логики в рамках этапа 1.

**Состав работ**

- [x] Реализовать расчёт слотов (учёт расписания, исключений по дате при PG, занятых записей)
- [x] Реализовать создание записи с расчётом длительности и стоимости
- [x] Подключить обработку ошибок API (422/409/404/503 по контракту) для реализованных маршрутов
- [x] Временный in-memory слой для локального запуска без Docker; полный функционал — через PostgreSQL ([`tasklist-database.md`](tasklist-database.md))
- [x] `GET /api/v1/services` (каталог; query `active_only`), поле `description` в каталоге
- [x] **Этап 1 (PostgreSQL):** `POST /auth/telegram`, `GET /me`, `GET /loyalty/rules`, клиентские `me/appointments`, `me/visits`, бонусы; админские CRUD услуг и расписания (правила + исключения), журнал записей, `POST /admin/visits`, бонусы пользователя; заглушка `POST /consultation/messages` (503 без LLM)
- [x] Авторизация: клиентский Bearer-токен после auth; `BOT_SECRET` + `X-Telegram-User-Id`; админ — `ADMIN_API_TOKEN` + [`deps_extra`](../../backend/src/pereobuyka/api/v1/deps_extra.py) (`SessionPg`, `AdminActor`)
- [x] Репозитории: [`PostgresAppointmentRepository`](../../backend/src/pereobuyka/storage/repositories/postgres.py), `PostgresServiceRepository`, `PostgresScheduleRepository`; маппинг ORM → схемы — [`api_adapters.py`](../../backend/src/pereobuyka/services/api_adapters.py)
- [x] Сервисы: [`visit_commands.py`](../../backend/src/pereobuyka/services/visit_commands.py) (подтверждение визита, бонусы), [`auth_user_pg.py`](../../backend/src/pereobuyka/services/auth_user_pg.py)
- [x] Seed: пользователь-админ под `ADMIN_ACTOR_USER_ID` ([`seed.py`](../../backend/src/pereobuyka/scripts/seed.py))

**Артефакты (ключевые)**

- [`backend/src/pereobuyka/api/v1/router.py`](../../backend/src/pereobuyka/api/v1/router.py) — каталог, слоты, запись; подключение [`routes_extended`](../../backend/src/pereobuyka/api/v1/routes_extended.py)
- [`backend/src/pereobuyka/api/v1/routes_extended.py`](../../backend/src/pereobuyka/api/v1/routes_extended.py) — сборка подроутеров
- [`backend/src/pereobuyka/api/v1/endpoints/`](../../backend/src/pereobuyka/api/v1/endpoints/) — `auth`, `client`, `admin`, `consultation`, `common`
- [`backend/src/pereobuyka/api/v1/schemas.py`](../../backend/src/pereobuyka/api/v1/schemas.py) — схемы по OpenAPI (в т.ч. визиты, лояльность, админ)
- [`backend/src/pereobuyka/storage/repositories/`](../../backend/src/pereobuyka/storage/repositories/) — репозитории PostgreSQL
- [`backend/src/pereobuyka/db/models.py`](../../backend/src/pereobuyka/db/models.py) — ORM под миграции (визиты, бонусы, исключения расписания и др.)
- [`backend/.env.example`](../../backend/.env.example) — в т.ч. `ADMIN_API_TOKEN`, `ADMIN_ACTOR_USER_ID`
- [`backend/tests/test_services.py`](../../backend/tests/test_services.py) — каталог услуг

**Артефакты (базовая волна — сохранены)**

- [`backend/src/pereobuyka/services/appointment_service.py`](../../backend/src/pereobuyka/services/appointment_service.py) — создание записи
- [`backend/src/pereobuyka/services/slot_service.py`](../../backend/src/pereobuyka/services/slot_service.py) — слоты
- [`backend/src/pereobuyka/storage/memory.py`](../../backend/src/pereobuyka/storage/memory.py) — stub без PostgreSQL

**Документы**

- [plan.md](impl/backend/iteration-05-impl-endpoints/plan.md)
- [summary.md](impl/backend/iteration-05-impl-endpoints/summary.md)

**Definition of Done — агент**

- Тесты iter-be-04 зелёные; логика слотов/записи/визитов/бонусов в `services/` и `storage/repositories/`, не в handlers бота
- При поднятом PostgreSQL и seed доступны сценарии OpenAPI этапа 1; `pytest` включает интеграционный тест визита

**Definition of Done — пользователь**

- Через OpenAPI/`/docs` или curl: happy-path слоты → запись; при PG — полный набор маршрутов этапа 1 по контракту

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Соответствие OpenAPI реализации | Ручной сценарий API | `make test`, `make run` | `/docs`, ответы JSON |

---

### iter-be-06 — Документация backend

**Шаг дорожной карты:** 7

**Цель:** Документировать backend: запуск, переменные окружения, OpenAPI, команды; **исправить ссылки в [`docs/plan.md`](../plan.md)** на канонический путь `docs/tasks/...`.

**Ценность:** Новый участник и агенты воспроизводят окружение без устных инструкций.

**Состав работ**

- [x] README: быстрый старт backend, ссылка на OpenAPI
- [x] `.env.example`: все обязательные переменные с комментариями
- [x] Зафиксировать команды в **Makefile** (run, test, lint, при необходимости migrate)
- [x] Просканировать [`docs/plan.md`](../plan.md): заменить `docs/tasklists/`, `tasklists/` на **`docs/tasks/`** и корректные имена файлов tasklist

**Артефакты**

- [`backend/README.md`](../../backend/README.md) — быстрый старт: требования, установка, env, run, OpenAPI, Make-команды, структура пакета
- [`backend/.env.example`](../../backend/.env.example) — SQLite по умолчанию, PostgreSQL в комментарии; все переменные из `config.py`
- [`Makefile`](../../Makefile) — без изменений; все команды актуальны
- [`docs/plan.md`](../plan.md) — без изменений; пути уже корректны (`tasks/`)

**Документы**

- [plan.md](impl/backend/iteration-06-backend-docs/plan.md)
- [summary.md](impl/backend/iteration-06-backend-docs/summary.md)

**Definition of Done — агент**

- README + `.env.example` согласованы с кодом; `docs/plan.md` не содержит битых путей к tasklist

**Definition of Done — пользователь**

- По README поднять backend и открыть OpenAPI; проверить таблицу этапов в `plan.md` — ссылки ведут в `docs/tasks/`

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Линтер, отсутствие секретов в example | Чтение README, клики по ссылкам в plan.md | `make run`, `make test` | README, `.env.example`, `docs/plan.md`, `/docs` |

---

### iter-be-07 — Бот через API

**Шаг дорожной карты:** 8

**Цель:** Рефакторинг Telegram-бота: тонкие handlers, вызовы backend HTTP API для сценариев слотов и записи (базовый срез), а по мере появления реализации — для остальных сценариев, покрытых API iter-be-05.

**Ценность:** Бот не дублирует бизнес-правила; единая точка правды в backend.

**Состав работ**

- [x] HTTP-клиент к backend (базовый URL из env)
- [x] Перевести сценарии «слоты» и «запись» на API iter-be-05; расширять на новые endpoint’ы по мере их реализации
- [x] Обработка ошибок API пользователю дружелюбно, без утечки стектрейсов
- [x] При появлении новых команд запуска бота — добавить в **Makefile**

**Артефакты**

**Backend (авторизация бота для `POST /appointments`):**

- [`backend/src/pereobuyka/config.py`](../../backend/src/pereobuyka/config.py) — `bot_secret`
- [`backend/src/pereobuyka/api/v1/deps.py`](../../backend/src/pereobuyka/api/v1/deps.py) — `Bearer` + `X-Telegram-User-Id` → детерминированный `user_id` (временная схема до auth-tasklist)
- [`backend/.env.example`](../../backend/.env.example) — `BOT_SECRET`

**Бот (проект [`bot/`](../../bot/), пакет `bot/src/pereobuyka/`):**

- [`bot/src/pereobuyka/client/backend.py`](../../bot/src/pereobuyka/client/backend.py) — `BackendClient`, `_UserClient`, `BackendError` / `BackendUnavailableError`
- [`bot/src/pereobuyka/client/__init__.py`](../../bot/src/pereobuyka/client/__init__.py)
- [`bot/src/pereobuyka/bot/handlers/services.py`](../../bot/src/pereobuyka/bot/handlers/services.py) — `/services` → `GET /api/v1/services`
- [`bot/src/pereobuyka/bot/handlers/book.py`](../../bot/src/pereobuyka/bot/handlers/book.py) — `/book` (FSM): услуга → дата → слот → `POST /api/v1/appointments`
- [`bot/src/pereobuyka/bot/handlers/start.py`](../../bot/src/pereobuyka/bot/handlers/start.py) — приветствие и список команд
- [`bot/src/pereobuyka/bot/router.py`](../../bot/src/pereobuyka/bot/router.py) — подключение handlers
- [`bot/src/pereobuyka/main.py`](../../bot/src/pereobuyka/main.py) — `MemoryStorage`, жизненный цикл `BackendClient`
- [`bot/src/pereobuyka/config.py`](../../bot/src/pereobuyka/config.py) — `backend_base_url`, `bot_secret` (снят merge-конфликт)
- [`bot/pyproject.toml`](../../bot/pyproject.toml) — зависимости (`httpx` и др.), dev `ruff`
- [`bot/.env.example`](../../bot/.env.example) — `BACKEND_BASE_URL`, `BOT_SECRET`
- [`.env.example`](../../.env.example) в корне — указатель на `bot/.env.example`
- [`Makefile`](../../Makefile) — `bot-install`, `bot-run`, `bot-lint`

**Документы**

- [plan.md](impl/backend/iteration-07-bot-via-api/plan.md)
- [summary.md](impl/backend/iteration-07-bot-via-api/summary.md)

**Принятые решения**

- Временная авторизация бота: один и тот же `BOT_SECRET` в backend и в `bot/.env`; при пустом секрете в backend поведение `deps` как до итерации (тесты с `auth_override` не ломаются).
- Один `httpx.AsyncClient` на процесс бота; закрытие в `finally` в `main.py`.

**Definition of Done — агент**

- Нет бизнес-логики слотов/записи в коде Telegram-бота (`bot/src/pereobuyka/`); `make backend-test` зелёный (**16 passed** после расширения тестов этапа 1)

**Definition of Done — пользователь**

- В Telegram работают `/services` и `/book`; при недоступном backend — короткое сообщение без стектрейса

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| `make backend-test`, `make backend-lint`; логи без токенов | Сценарий записи в Telegram; отключение backend | `make backend-run` + `make bot-run` (в `.env` бота и backend задать одинаковый `BOT_SECRET`) | Telegram, терминал |

---

## Качество и инженерные практики

**Шаг дорожной карты:** 9 (сквозной)

Не отдельная итерация, а требование на всём цикле и финальное закрепление.

- **Линтер / формат:** `ruff` в `pyproject.toml`; цель `make lint`
- **Тесты:** pytest; цель `make test`; новые сценарии — новые тесты
- **Контракт:** изменения публичного API — через осознанное обновление контракта iter-be-02 и матрицы сценариев vision §4
- **Логи:** [`docs/vision.md`](../vision.md), раздел про логирование
- **Makefile:** любая новая команда локального запуска, проверки или обслуживания — отражается в [`Makefile`](../../Makefile)

**Definition of Done — агент:** перед завершением крупного PR — `make lint` и `make test` зелёные (если уже заведены).

**Definition of Done — пользователь:** в README перечислены команды качества; можно повторить локально.

**Проверка:** `make lint`, `make test` — ожидаемый успех; при добавлении CI — зелёный пайплайн.

---

## Дальнейшие итерации (после закрытия этапа 1 по backend)

По [`docs/plan.md`](../plan.md): **этап 2** — Telegram-бот на всех сценариях API (регистрация через `POST /auth/telegram`, записи, визиты, бонусы); **этап 3** — LLM-консультация (реализация вместо заглушки `503`); **этапы 4–6** — админка/клиентский веб, production-ready. Отдельные tasklist в `docs/tasks/` — по мере появления.

Ориентиры:

- Бот: перевести сценарии с `BOT_SECRET` на пользовательский Bearer-токен там, где нужен профиль в БД; вызовы новых endpoint’ов этапа 1
- Backend: доработки из [`docs/backlog.md`](../backlog.md) (DDD/use cases, mypy в CI, негативные тесты) — по приоритету, не блокируют этап 2
- Модуль LLM в `backend/.../llm/` и полноценный `POST /consultation/messages` — этап 3 плана
- Локальный полный стек — см. этап 6 и tasklist devops

---

## Список задач (план/summary по workflow)

По [workflow](../../.cursor/rules/workflow.mdc) для отдельных задач создаются каталоги с `plan.md` / `summary.md` под [`docs/tasks/impl/backend/`](../tasks/impl/backend/) — по мере дробления итераций.

| Задача | Описание | Статус | Документы |
|--------|----------|--------|-----------|
| iter-be-01 (целиком) | Стек и соглашения: ADR-002, ADR-003, vision, convensions | ✅ | [`impl/backend/iteration-01-stack-conventions/`](impl/backend/iteration-01-stack-conventions/) |
| iter-be-02 (целиком) | Контракты API vision: OpenAPI, ошибки, plan/summary | ✅ | [`impl/backend/iteration-02-api-contracts/`](impl/backend/iteration-02-api-contracts/) |
| iter-be-03 (целиком) | Каркас backend: pyproject, структура пакета, health, Makefile | ✅ | [`impl/backend/iteration-03-scaffold-backend/`](impl/backend/iteration-03-scaffold-backend/) |
| iter-be-04 (целиком) | Тесты API: health, слоты, запись; PG + сценарий визита/бонусов | ✅ | [`impl/backend/iteration-04-api-tests-mvp/`](impl/backend/iteration-04-api-tests-mvp/) |
| iter-be-05 (целиком) | Реализация endpoints: базовый срез → **полный API этапа 1 (PG)**, репозитории, endpoints-пакет | ✅ | [`impl/backend/iteration-05-impl-endpoints/`](impl/backend/iteration-05-impl-endpoints/) |
| iter-be-06 (целиком) | Документация backend: README, .env.example, проверка Makefile и plan.md | ✅ | [`impl/backend/iteration-06-backend-docs/`](impl/backend/iteration-06-backend-docs/) |
| iter-be-07 (целиком) | Бот через API: BackendClient, handlers /services и /book FSM, bot_secret auth | ✅ | [`impl/backend/iteration-07-bot-via-api/`](impl/backend/iteration-07-bot-via-api/) |


