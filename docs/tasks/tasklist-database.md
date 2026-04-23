# Tasklist: Database (этап 1)

## Область: database

Слой данных «Переобуйка»: требования к данным для сценариев клиента и администратора, логическая и физическая модель PostgreSQL, миграции (Alembic), локальная инфраструктура БД, ORM-модели и репозитории в backend с заменой in-memory хранилища на персистентное. **Интеграционные тесты с БД** — через **Testcontainers** (PostgreSQL в Docker на время прогона pytest), чтобы совпадали движок и диалект с production без ручного поднятия Postgres для каждого прогона.

**Опорные документы:** [`docs/vision.md`](../vision.md) · [`docs/tech/data-model.md`](../tech/data-model.md) · [`docs/tech/api/api-contracts.md`](../tech/api/api-contracts.md) · [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml) · [`docs/plan.md`](../plan.md)

**Skill для ревью схемы:** [.agents/skills/postgresql-table-design/SKILL.md](../../.agents/skills/postgresql-table-design/SKILL.md)

---

## Связь с `docs/tasks/tasklist-backend.md`

| Зона ответственности | Tasklist database (этот документ) | Tasklist backend |
|----------------------|-----------------------------------|------------------|
| Схема БД, индексы, ограничения | Да | Нет |
| Миграции Alembic, структура `alembic/` | Да | Использует в коде |
| SQLAlchemy mapped classes, session, engine | Да (модели персистентности) | Роутеры, Pydantic, сервисы |
| Репозитории / `storage/` — реализация против БД | Да | Сервисы вызывают репозитории |
| Бизнес-правила (слоты, цены, бонусы) | Согласование полей и транзакций | Да — основная логика |
| OpenAPI / HTTP-контракты | Согласование идентификаторов и полей при расхождениях | Да — источник эндпоинтов |
| Интеграционные тесты с PostgreSQL (**pytest** + **Testcontainers**) | Да: фикстуры, dev-зависимость, Docker | Запуск тестов, поддержка conftest |
| Telegram-бот, aiogram | Нет | iter-07 и далее |

---

## Рекомендация по skills

- Проектирование таблиц и индексов: skill **postgresql-table-design** (см. путь выше).
- Подбор дополнительных skills под конкретный шаг: команда **`/find-skills`**.

---

## Связь с `docs/plan.md`

| Этап в [`docs/plan.md`](../plan.md) | Роль этого tasklist |
|-------------------------------------|----------------------|
| **1** — Фундамент: backend и модель данных | Основной фокус: требования к данным, физическая модель, миграции, Docker/local PostgreSQL, ORM, репозитории, интеграционные тесты с БД (**Testcontainers**), вывод in-memory из целевого пути API |
| **2+** | Расширение данных под новые сценарии бота/веб — после закрытия базового слоя здесь |

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

| ID | Итерация | Статус | Зависимости | Ключевые артефакты |
|----|----------|--------|-------------|-------------------|
| [iter-db-01](#iter-db-01--user-scenarios-сценарии-и-требования-к-данным) | Сценарии и требования к данным | ✅ done | — | [`docs/tech/user_scenarios.md`](../tech/user_scenarios.md), [`docs/plan.md`](../plan.md), примечание в [`docs/tech/data-model.md`](../tech/data-model.md) |
| [iter-db-02](#iter-db-02--schema--er-логическая-и-физическая-модель) | Логическая и физическая модель + ER | ✅ done | iter-db-01 | [`docs/tech/data-model.md`](../tech/data-model.md), [summary iter-db-02](impl/database/iteration-02-schema-er/summary.md) |
| [iter-db-03](#iter-db-03--migrations--access-adr-и-практическая-справка) | ADR и практическая справка по миграциям/доступу | ✅ done | iter-db-02* | [ADR-004](../tech/adr/adr-004-database-migrations-workflow.md), [database-migrations.md](../tech/database-migrations.md), реестр ADR |
| [iter-db-04](#iter-db-04--infra-локальный-postgresql-migrations-seed) | Инфраструктура БД, seed, команды | ✅ done | iter-db-03 | [docker-compose.yml](../../docker-compose.yml), [Makefile](../../Makefile), `backend/alembic/versions/`, seed, README |
| [iter-db-05](#iter-db-05--orm-repos-backend-замена-in-memory) | ORM, репозитории, интеграция backend | ✅ done | iter-db-04 | [`backend/src/pereobuyka/db/`](../../backend/src/pereobuyka/db/), [`postgres_repos.py`](../../backend/src/pereobuyka/storage/postgres_repos.py), pytest + **Testcontainers** |

\*Схема в `data-model.md` может уточняться параллельно с ADR; миграции не стартуют без зафиксированной целевой физической модели.

---

## Итерации

### iter-db-01 — User scenarios (сценарии и требования к данным)

**Шаг дорожной карты:** 1 (продуктовый фундамент под данные)

**Цель:** Зафиксировать для **базовых сценариев** из [`docs/vision.md`](../vision.md) §4 (без технической «простыни»), что **видит и что может клиент**, что **видит и может администратор**, и какие **сущности, поля и связи** минимально нужны для будущего frontend и для согласования с [`docs/tech/data-model.md`](../tech/data-model.md).

**Ценность:** Единое понимание «какие данные обязаны жить в системе» до финализации физической схемы и миграций.

**Состав работ**

- [x] Выделить **несколько базовых сквозных сценариев** (регистрация/профиль, каталог и цены, запись, список/отмена записей, подтверждение визита админом, баланс и история бонусов) и для каждого описать **экраны/действия** с точки зрения клиента и админа
- [x] Для каждого сценария — таблица или список: **какие сущности** (`User`, `Service`, `Schedule`, `Appointment`, `Visit`, `BonusAccount`, `BonusTransaction`, `FAQ` и др.) и **какие связи/поля** нужны минимум для отображения и действий (без привязки к SQL)
- [x] Явно отметить различия **каналов** (бот / будущий веб): что хранится одинаково в БД, что является представлением в канале
- [x] Добавить документ [`docs/tech/user_scenarios.md`](../tech/user_scenarios.md) со ссылками на vision §4 и матрицей «сценарий → данные»
- [x] При необходимости: короткая отсылка в [`docs/plan.md`](../plan.md) (этап 1) или в [`docs/tech/data-model.md`](../tech/data-model.md) — **источник сценариев** для последующей доработки модели

**Артефакты**

- `docs/tech/user_scenarios.md` — сценарии клиент/админ и требования к данным
- При изменениях: [`docs/plan.md`](../plan.md), примечание в [`docs/tech/data-model.md`](../tech/data-model.md)

**Документы**

- [plan.md](impl/database/iteration-01-user-scenarios/plan.md)
- [summary.md](impl/database/iteration-01-user-scenarios/summary.md)

**Definition of Done — агент**

- Документ покрывает минимум: идентификация/профиль пользователя, просмотр прайса, запись (слоты + услуги), список/отмена записей, подтверждение визита администратором, бонусы (баланс + история)
- Сценарии **клиента** и **администратора** разделены явно; для каждого есть связь с сущностями из vision/data-model
- Нет противоречий с [`docs/vision.md`](../vision.md) §4 без явного открытого вопроса

**Definition of Done — пользователь**

- Прочитать `docs/tech/user_scenarios.md` и сверить полноту базовых сценариев с vision §4
- Убедиться, что документ читается как продуктовая спецификация данных, без необходимости открывать код

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Ссылки vision ↔ user_scenarios ↔ data-model согласованы | Чтение `user_scenarios.md` | — | `docs/tech/user_scenarios.md` |

---

### iter-db-02 — Schema & ER (логическая и физическая модель)

**Шаг дорожной карты:** 1

**Цель:** Актуализировать **логическую** модель (сущности, связи, кардинальности) и **физическую** модель под **PostgreSQL** в [`docs/tech/data-model.md`](../tech/data-model.md); добавить **физическую ER-диаграмму** (рекомендуется Mermaid `erDiagram` в том же файле или отдельный `.md` в `docs/tech/` — выбор зафиксировать в summary).

**Ценность:** Однозначная целевая схема для миграций, ORM и ревью качества таблиц.

**Состав работ**

- [x] Обновить разделы логической модели в [`docs/tech/data-model.md`](../tech/data-model.md) по результатам iter-db-01
- [x] Описать **физический** уровень: таблицы, PK/FK, типы PostgreSQL, `NOT NULL`, `CHECK`, индексы под запросы из сценариев и контракта API
- [x] Добавить **ER-диаграмму** физического уровня (согласовать именование `snake_case`, связи FK)
- [x] Выполнить **ревью по skill** [.agents/skills/postgresql-table-design/SKILL.md](../../.agents/skills/postgresql-table-design/SKILL.md): `timestamptz`, `numeric` для денег, `text`, индексы на FK, политика NULL/UNIQUE и т.д.; краткий итог — в [summary.md](impl/database/iteration-02-schema-er/summary.md)
- [x] Сверить с [`docs/tech/api/api-contracts.md`](../tech/api/api-contracts.md) и [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml): идентификаторы (UUID в JSON), поля сущностей; зафиксировать расхождения и план правок (iter-db-05 или отдельная задача)

**Артефакты**

- [`docs/tech/data-model.md`](../tech/data-model.md) — логика + физика + ER
- При необходимости: отдельный файл диаграммы в `docs/tech/`
- [summary.md](impl/database/iteration-02-schema-er/summary.md) — чеклист postgresql-table-design и выводы

**Документы**

- [plan.md](impl/database/iteration-02-schema-er/plan.md)
- [summary.md](impl/database/iteration-02-schema-er/summary.md)

**Definition of Done — агент**

- `data-model.md` отражает целевую схему; ER согласована с текстом таблиц и FK
- Пройден чеклист по postgresql-table-design; открытые компромиссы описаны
- Явно указано, нужны ли правки контрактов API — и ссылка на задачу/итерацию

**Definition of Done — пользователь**

- Открыть `data-model.md` и ER; пройти по сценариям из `user_scenarios.md` и убедиться, что данные для них находятся в модели

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| ER ↔ таблицы; контракты ↔ поля | Навигация по ER и сценариям | — | `docs/tech/data-model.md` |

---

### iter-db-03 — Migrations & access (ADR и практическая справка)

**Шаг дорожной карты:** 1

**Цель:** Зафиксировать **договорённости по использованию** уже принятого стека ([ADR-001](../tech/adr/adr-001-database.md) PostgreSQL, [ADR-003](../tech/adr/adr-003-orm.md) SQLAlchemy 2 async + asyncpg + Alembic): workflow миграций, структура проекта, подключение к БД из backend. **Не переизбирать** ORM/мигратор без веских причин; при отклонении — отдельное обоснование в ADR.

**Ценность:** Любой разработчик воспроизводит шаги миграций и понимает границу ORM ↔ Pydantic из ADR-003.

**Состав работ**

- [x] Подготовить **отдельный ADR** (следующий номер в [реестре](../tech/adr/README.md), например `adr-004-database-migrations-workflow.md`): структура каталога `alembic/`, именование ревизий, autogenerate vs ручные правки, политика downgrade, связь с метаданными SQLAlchemy, соответствие ADR-001/003
- [x] Добавить запись в [`docs/tech/adr/README.md`](../tech/adr/README.md)
- [x] Написать **короткую практическую справку** [`docs/tech/database-migrations.md`](../tech/database-migrations.md) (или `database-tooling.md`): типовые команды (`revision`, `upgrade`, `current`, проверка heads), где лежат модели, как запускать из `backend/` через `uv`, напоминание о слоях (репозитории, не Pydantic в ORM); кратко указать, что **прогон интеграционных тестов с БД** в iter-db-05 опирается на **Testcontainers** (отдельный подраздел или ссылка на backend README после появления фикстур)
- [x] При необходимости обновить [`docs/vision.md`](../vision.md) §8 (стек) и §11 (таблица ADR) — ссылки на новый ADR и справку

**Артефакты**

- [`docs/tech/adr/adr-004-database-migrations-workflow.md`](../tech/adr/adr-004-database-migrations-workflow.md)
- [`docs/tech/adr/README.md`](../tech/adr/README.md)
- [`docs/tech/database-migrations.md`](../tech/database-migrations.md)
- [`docs/vision.md`](../vision.md) — при необходимости

**Документы**

- [plan.md](impl/database/iteration-03-migrations-adr/plan.md)
- [summary.md](impl/database/iteration-03-migrations-adr/summary.md)

**Definition of Done — агент**

- ADR принят (`Accepted`) и в реестре; справка позволяет пройти сценарий миграций без чтения исходников
- Ссылки ADR-001 ↔ ADR-003 ↔ новый ADR согласованы

**Definition of Done — пользователь**

- Прочитать новый ADR и `docs/tech/database-migrations.md`; выполнить описанные команды в пустом клоне после появления каталога `alembic/` (на iter-db-04)

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Реестр ADR, перекрёстные ссылки | Читаемость справки | — | `docs/tech/adr/`, `docs/tech/database-migrations.md` |

---

### iter-db-04 — Infra (локальный PostgreSQL, миграции, seed, проверка)

**Шаг дорожной карты:** 1

**Цель:** Воспроизводимый **локальный** PostgreSQL, переменные окружения, **поднятие / остановка / пересоздание** окружения (включая volume), применение миграций, **начальное наполнение** (seed), команды **просмотра данных**.

**Ценность:** Одинаковый старт для разработки и ручной проверки. Автоматические тесты с БД в iter-db-05 идут через **Testcontainers** (отдельный ephemeral Postgres), а не через обязательный запуск этого compose — compose остаётся для **ручного** dev и отладки.

**Состав работ**

- [x] Добавить описание инфраструктуры (предпочтительно **Docker Compose** в корне репозитория или в `backend/` — зафиксировать в артефактах и README)
- [x] Задать переменные (`DATABASE_URL` или раздельные `POSTGRES_*` + сборка URL в `backend` — согласовать с [`backend/.env.example`](../../backend/.env.example))
- [x] Включить в [Makefile](../../Makefile) цели: например `db-up`, `db-down`, `db-reset` (пересоздание volume + миграции + seed — явно описать опасность потери данных)
- [x] Команды/скрипты **просмотра данных**: например `psql` через `docker compose exec`, или `make db-psql` / `make db-shell`
- [x] Реализовать **первую миграцию** (скелет схемы по iter-db-02) и **seed** (скрипт Python/`uv` или data-fixture в миграции — выбрать один подход и описать в справке)
- [x] Обновить документацию запуска: [`backend/README.md`](../../backend/README.md) и/или корневой [`README.md`](../../README.md); не коммитить секреты

**Артефакты**

- `docker-compose.yml` (или эквивалент) — путь зафиксировать в summary
- [Makefile](../../Makefile) — цели `db-*` и при необходимости обновление существующих целей
- [`backend/.env.example`](../../backend/.env.example)
- README — раздел «База данных»

**Документы**

- [plan.md](impl/database/iteration-04-db-infra/plan.md)
- [summary.md](impl/database/iteration-04-db-infra/summary.md)

**Definition of Done — агент**

- Из **документированного** «чистого» состояния последовательность поднимает PostgreSQL, накатывает миграции, выполняет seed
- Команды сброса либо идемпотентны в рамках сценария, либо явно помечены как разрушительные для данных локального dev

**Definition of Done — пользователь**

- Выполнить сценарий из README/Makefile: поднять БД, применить миграции, проверить seed через команду просмотра данных

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Makefile и README согласованы | Полный цикл up → migrate → seed → просмотр | `make db-up`, и др. по документации | Docker, `psql`/обёртка |

---

### iter-db-05 — ORM, repos, backend (замена in-memory)

**Шаг дорожной карты:** 1

**Цель:** Реализовать **SQLAlchemy**-модели по схеме, слой **репозиториев** в [`backend/src/pereobuyka/storage/`](../../backend/src/pereobuyka/storage/), подключение **session/engine** (FastAPI `Depends`), замена **in-memory** хранилища на **PostgreSQL** для согласованного набора маршрутов (минимум — уже реализованный MVP: услуги, слоты, создание записи; расширение по мере готовности схемы и контракта).

**Ценность:** API опирается на персистентные данные; совпадение с [`docs/plan.md`](../plan.md) (этап 1) по «миграции БД» и репозиториям.

**Состав работ**

- [x] Объявить mapped classes / `Table` метаданные в согласованном пакете (например `backend/src/pereobuyka/db/` или под `storage/` — зафиксировать в коде и summary)
- [x] Реализовать репозитории с явными методами; **не** возвращать ORM-объекты из роутеров — маппинг в Pydantic в сервисах или репозиториях ([ADR-003](../tech/adr/adr-003-orm.md))
- [x] Подключить async engine и session scope (lifespan, тестовые переопределения)
- [x] Заменить использование [`memory.py`](../../backend/src/pereobuyka/storage/memory.py) на реализацию БД для целевых эндпоинтов; оставить fallback только если явно задокументировано как временное
- [x] Обновить/добавить **интеграционные тесты** с БД на базе **Testcontainers** (`testcontainers`, контейнер PostgreSQL совместимый с asyncpg): фикстура(и) в [`backend/tests/conftest.py`](../../backend/tests/conftest.py) (например `session`-scope на контейнер + применение миграций Alembic к выданному URL), изоляция данных между тестами (транзакции с откатом, truncate или отдельная БД в том же инстансе — зафиксировать в summary)
- [x] Добавить зависимость **`testcontainers`** (и при необходимости доп. пакет для PostgreSQL) в dev-группу [`backend/pyproject.toml`](../../backend/pyproject.toml); задокументировать требование **запущенного Docker** для полного прогона тестов с БД
- [x] При изменении поведения или полей API: [`docs/tech/api/api-contracts.md`](../tech/api/api-contracts.md), [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml)
- [x] Обновить [`docs/plan.md`](../plan.md) — раздел «Факт реализации» этапа 1 при закрытии персистентности

**Артефакты**

- Код backend: storage, модели, `main.py`, `deps`, сервисы
- [`backend/tests/`](../../backend/tests/) — фикстуры БД на Testcontainers; опционально маркер `@pytest.mark.integration` для выборочного прогона
- Контракты при изменениях: [`docs/tech/api/api-contracts.md`](../tech/api/api-contracts.md), OpenAPI

**Документы**

- [plan.md](impl/database/iteration-05-orm-repos-backend/plan.md)
- [summary.md](impl/database/iteration-05-orm-repos-backend/summary.md)

**Definition of Done — агент**

- `make backend-lint` и `make backend-test` проходят при **доступном Docker** (Testcontainers поднимает Postgres для интеграционных тестов); стратегия изоляции данных в тестах описана в коде или summary
- Создание записи и чтение каталога/слотов работают против PostgreSQL: в CI/локально — через контейнер Testcontainers; ручная проверка — по сценарию iter-db-04 при необходимости
- In-memory не остаётся единственным хранилищем для целевых MVP endpoint’ов без явного ADR/заметки о временном исключении

**Definition of Done — пользователь**

- Убедиться, что Docker запущен; выполнить `make backend-test`; при необходимости — ручные запросы к API и просмотр данных через команды iter-db-04

**Проверка после итерации**

| Агент проверяет | Пользователь проверяет | Команды | Где результат |
|-----------------|-------------------------|---------|---------------|
| Интеграция с миграциями, Testcontainers стартует Postgres, отсутствие утечки секретов | Прогон pytest с Docker; при желании E2E вручную | `make backend-test`; при ручной проверке: `make db-up`, `make backend-run` | терминал, контейнеры Docker |

---

## Риски и зависимости

- **Параллельно с ботом:** расширение сценариев бота опирается на готовые маршруты и персистентность; приоритет — согласованные идентификаторы и поля с OpenAPI
- **Контракты:** UUID и имена полей в JSON должны совпадать с колонками/маппингом; расхождения выявлять в iter-db-02 и закрывать в iter-db-05
- **Миграции и CI:** интеграционные тесты с Testcontainers требуют **Docker в CI** (или отдельный job с сервисом Postgres и явная политика пропуска/альтернативы — задокументировать в README)
- **Testcontainers:** первый прогон может скачивать образ Postgres; на Windows нужен рабочий Docker (например Docker Desktop); опционально маркер `integration` и пропуск без Docker с предупреждением

---

## Качество (сквозное)

- Изменения в database-итерациях **не ломают** `ruff` и pytest в backend без явной причины
- Секреты только в `.env` (не в git); `.env.example` без реальных паролей
- Зависимость **`testcontainers`** в dev-группе backend; документировано, что полный набор тестов с БД требует **Docker**
- Новые команды локального запуска и обслуживания БД — в [Makefile](../../Makefile) и в [`docs/tech/database-migrations.md`](../tech/database-migrations.md) / [`backend/README.md`](../../backend/README.md)

---

## Папки артефактов итераций

Для каждой итерации создаётся каталог под план и summary:

```
docs/tasks/impl/database/
├── iteration-01-user-scenarios/
├── iteration-02-schema-er/
├── iteration-03-migrations-adr/
├── iteration-04-db-infra/
└── iteration-05-orm-repos-backend/
```

Файлы `plan.md` и `summary.md` добавляются по мере выполнения соответствующей итерации.
