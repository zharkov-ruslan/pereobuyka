# Tasklist: Frontend (веб) «Переобуйка»

## Область: frontend (веб)

Веб-клиент «Переобуйка» для ролей **администратор** и **клиент**: панель загрузки и статистики, клиенты, личный кабинет и запись, чат-ассистент **только у клиента** (плавающая панель в кабинете); доработки backend и данных под экраны; ревью качества, голосовой режим, ответы по данным БД (Text-to-SQL). Расчёты и бизнес-правила — в backend; фронт вызывает API и отображает состояние.

**Опорные документы:** [`docs/vision.md`](../vision.md) · [`docs/ui/ui-requirements.md`](../ui/ui-requirements.md) · [`docs/tech/data-model.md`](../tech/data-model.md) · [`docs/tech/api/api-contracts.md`](../tech/api/api-contracts.md) · [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml) · [`docs/plan.md`](../plan.md)

**Стек:** Next.js (App Router), React, TypeScript, shadcn/ui, Tailwind CSS, **pnpm**.

### Статус области ([`docs/plan.md`](../plan.md))

Этапы **4** (административный веб) и **5** (клиентский веб) — **⚪ planned**; пересечения с этапами **3** (LLM) и **6** (delivery) см. ниже. Итерации **iter-fe-00 … iter-fe-09**; по мере выполнения обновлять сводную таблицу и при необходимости [`docs/plan.md`](../plan.md).

---

## Связь с `docs/tasks/tasklist-backend.md`

| Зона ответственности | Tasklist frontend (этот документ) | Tasklist backend |
|----------------------|-----------------------------------|------------------|
| UI, `web/`, тема, layout | Да | Нет |
| Спека экранов → контракты; новые эндпоинты под UI | iter-fe-00 (спека), iter-fe-01 (реализация в `backend/`) | Источник сервисов, OpenAPI, репозитории |
| Бизнес-правила (слоты, цены, бонусы) | Нет | Да |

---

## Рекомендация по skills

Инициализация UI и ревью: **shadcn/ui**, **vercel-react-best-practices**, **nextjs-app-router-patterns** (см. `.agents/skills/`). Проектирование API (iter-fe-00 / iter-fe-01): **api-design-principles**, оформление контрактов — **api-contract-custom**. Подбор: **`/find-skills`**.

---

## Связь с `docs/plan.md`

| Этап в [`docs/plan.md`](../plan.md) | Роль этого tasklist |
|-------------------------------------|---------------------|
| **4** — Административный веб-интерфейс | iter-fe-00–02 (спека, API, каркас), iter-fe-03–04 (панель администратора, клиенты), iter-fe-06–07 (чат в UI, качество кода) |
| **5** — Клиентский веб-интерфейс | iter-fe-05 (личный кабинет и визард); общий каталог `web/` — iter-fe-02 |
| **3** — LLM-консультант | iter-fe-06 (чат), iter-fe-08–09 (голос, Text-to-SQL); эндпоинт консультации — в backend |
| **6** — Production-ready | iter-fe-07 (ревью frontend); CI/CD и инфра — [`tasklist-06-devops.md`](tasklist-06-devops.md) |

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

Идентификаторы **iter-fe-00** … **iter-fe-09**; порядок выполнения последовательный, если не оговорено иначе.

| ID | Итерация | Статус | Зависимости | Ключевые артефакты |
|----|----------|--------|-------------|-------------------|
| [iter-fe-00](#iter-fe-00-ui-требования-и-api-для-frontend) | UI-требования и API для frontend | ✅ done | — | [`docs/ui/ui-requirements.md`](../ui/ui-requirements.md), [`docs/tech/api/api-contracts.md`](../tech/api/api-contracts.md), [plan.md](impl/frontend/iteration-0-ui-api-spec/plan.md), [summary.md](impl/frontend/iteration-0-ui-api-spec/summary.md) |
| [iter-fe-01](#iter-fe-01-backend-api-миграции-seed-админ-в-бд) | Backend API + миграции/seed + админ в БД | ✅ done | iter-fe-00 | `backend/`, Alembic, seed, [`openapi.yaml`](../tech/api/openapi.yaml), [plan](impl/frontend/iteration-1-backend-api-seed/plan.md), [summary](impl/frontend/iteration-1-backend-api-seed/summary.md) |
| [iter-fe-02](#iter-fe-02-каркас-web-nextjs-shadcn-тема-layout-вход) | Каркас web (Next.js, shadcn, тема, layout, вход) | ✅ done | iter-fe-01 | `web/`, [`Makefile`](../../Makefile), [`docs/vision.md`](../vision.md), [plan](impl/frontend/iteration-2-web-skeleton/plan.md), [summary](impl/frontend/iteration-2-web-skeleton/summary.md) |
| [iter-fe-03](#iter-fe-03-экран-панель-администратора) | Экран «Панель администратора» | ✅ done | iter-fe-02 | `web/app/...`, KPI, сетка слотов, [plan](impl/frontend/iteration-3-admin-dashboard/plan.md), [summary](impl/frontend/iteration-3-admin-dashboard/summary.md) |
| [iter-fe-04](#iter-fe-04-экран-клиенты-сервиса) | Экран «Клиенты сервиса» | ✅ done | iter-fe-03 | Таблица клиентов, карточка, [plan](impl/frontend/iteration-4-clients/plan.md), [summary](impl/frontend/iteration-4-clients/summary.md) |
| [iter-fe-05](#iter-fe-05-личный-кабинет-клиента-визард-записи) | Личный кабинет клиента + визард записи | ✅ done | iter-fe-04 | Кабинет, LocalStorage черновика, [plan](impl/frontend/iteration-5-client-cabinet/plan.md), [summary](impl/frontend/iteration-5-client-cabinet/summary.md) |
| [iter-fe-06](#iter-fe-06-чат-с-ассистентом-плавающий-виджет) | Чат с ассистентом (плавающий виджет) | ✅ done | iter-fe-05 | Глобальная панель чата, консультация API |
| [iter-fe-07](#iter-fe-07-ревью-качества-frontend-best-practices) | Ревью качества frontend (best practices) | ✅ done | iter-fe-06 | ESLint, `pnpm build`, [plan](impl/frontend/iteration-7-frontend-quality-review/plan.md), [summary](impl/frontend/iteration-7-frontend-quality-review/summary.md) |
| [iter-fe-08](#iter-fe-08-голосовой-режим-чата-web-telegram) | Голосовой режим чата (web + Telegram) | ✅ done | iter-fe-07 | Web Speech / STT, `bot/`, [plan](impl/frontend/iteration-8-voice-chat/plan.md), [summary](impl/frontend/iteration-8-voice-chat/summary.md) |
| [iter-fe-09](#iter-fe-09-text-to-sql-ответы-по-данным-бд) | Text-to-SQL / ответы по данным БД | ✅ done | iter-fe-08 | ADR-006, безопасный read-only слой, тесты, UI админки |

---

## Итерации

### iter-fe-00 — UI-требования и API для frontend

**Шаг дорожной карты:** 4–5 (подготовка веб), опора на этап 1 (контракты backend)

### Цель

Согласованно зафиксировать **что рисует** веб-интерфейс и **какие** HTTP-контракты нужны экранам (включая новые, если текущих в [api-contracts.md](../tech/api/api-contracts.md) не хватает).

### Ценность

Один набор согласованных спек до кодирования снижает переделки backend и web.

### Состав работ

- Сжать [ui-requirements.md](../ui/ui-requirements.md) в **краткие функциональные** требования per-экран: админ-панель, клиенты, кабинет, чат **только для клиента** (не отдельная страница), вход.
- Сопоставить с [api-contracts.md](../tech/api/api-contracts.md) / [openapi.yaml](../tech/api/openapi.yaml): отметить **покрытие** и **дыры** (KPI, сетка слотов, статистика недели, список клиентов, рейтинг, скидки, источник записи LLM/бот/админ, история вопросов к боту, история чата и т.д.).
- Зафиксировать **черновик** эндпоинтов/схем per экран (таблицы, query/path, роли) в отдельном артефакте итерации; при сомнениях — сверка со skill `api-design-principles` (читать `.agents/skills/api-design-principles/SKILL.md`).
- Зафиксировать стратегию **входа** для веб: «Telegram username» из [ui-requirements.md](../ui/ui-requirements.md) vs `POST /api/v1/auth/telegram` (сейчас `telegram_id`) — **решение** и миграция контракта/экрана.
- Список файлов к обновлению после утверждения: [api-contracts.md](../tech/api/api-contracts.md), [openapi.yaml](../tech/api/openapi.yaml), [data-model.md](../tech/data-model.md) при появлении новых сущностей, при необходимости [vision.md](../vision.md) (стек web), [plan.md](../plan.md) (связь этапов 4–5 с этим tasklist).

### Артефакты (ожидаемые)

- `web/` — *ещё нет*; в итерации 0 — только **док-артефакты** в `docs/tasks/impl/frontend/iteration-0-ui-api-spec/`.
- Документация: [ui-requirements.md](../ui/ui-requirements.md) (при уточнениях), [api-contracts.md](../tech/api/api-contracts.md), [openapi.yaml](../tech/api/openapi.yaml), [data-model.md](../tech/data-model.md), [vision.md](../vision.md), [plan.md](../plan.md).

**Документы**

- [plan.md](impl/frontend/iteration-0-ui-api-spec/plan.md)
- [summary.md](impl/frontend/iteration-0-ui-api-spec/summary.md)

**Definition of Done — агент**

- Есть **карта экранов → требуемые данные → эндпоинты/схемы**; явно отмечено **где контракта нет** и что добавить.
- Решение по **входу/идентификации** веб-пользователя задокументировано и согласовано с [api-contracts.md](../tech/api/api-contracts.md) (или вынесено в ADR).
- Ссылки на релевантные skill’ы: `api-design-principles` (и при правках контракта в последующем — `api-contract-custom` в `.agents/skills/api-contract-custom/SKILL.md`).

**Definition of Done — пользователь**

- Открыть [tasklist-frontend.md](tasklist-frontend.md) и [summary.md](impl/frontend/iteration-0-ui-api-spec/summary.md): проверить, что **все экраны** из [ui-requirements.md](../ui/ui-requirements.md) покрыты и список **новых/изменённых** API понятен без чтения кода.

---

### iter-fe-01 — Backend API + миграции/seed + админ в БД

**Шаг дорожной карты:** 4–5 (API, миграции, seed под UI)

### Цель

Довести backend и БД до состояния, в котором **все** экраны веб (по ит. 0) могут **надёжно** получать данные; наполнить **seed/mock** и **пользователя-админа** для локальной демо.

### Ценность

Frontend-итерации 2+ не блокируются на «дырах» в данных и API.

### Состав работ

- Сверка с [data-model.md](../tech/data-model.md): **достаточно ли** полей для UI (KPI, рейтинг клиента, скидка на визит, `source` записи, логи консультаций и т.д.); **список требований к данным** — отдельный подпункт в `plan.md` итерации.
- Реализовать **новые/расширенные** маршруты в `backend/` (роли `client` / `admin`), сервисы, репозитории, тесты.
- **Alembic:** миграции под новую структуру; **seed** (или расширение `pereobuyka.scripts.seed`) с наглядными данными для сетки слотов, статистики, списка клиентов, чатов.
- **Миграция/скрипт** с явным **администратором** в БД (см. существующий подход `ADMIN_ACTOR` / plan этапа 1 в [plan.md](../plan.md)); не дублировать секреты в документах.
- Самопроверка REST: resource-oriented маршруты, коды ошибок, пагинация — skill `api-design-principles`.
- Обновить [api-contracts.md](../tech/api/api-contracts.md) и [openapi.yaml](../tech/api/openapi.yaml) в синхроне с кодом; при необходимости — [errors.md](../tech/api/errors.md).

### Артефакты

- `backend/src/pereobuyka/` — эндпоинты, сервисы, storage.
- `backend/alembic/versions/` — миграции; seed-скрипт(ы).
- [api-contracts.md](../tech/api/api-contracts.md), [openapi.yaml](../tech/api/openapi.yaml), [data-model.md](../tech/data-model.md) (при смене схемы), [user_scenarios.md](../tech/user_scenarios.md) при сценарных правках, [plan.md](../plan.md) — краткое **«факт API»** по этапу web при необходимости.

**Документы**

- [plan.md](impl/frontend/iteration-1-backend-api-seed/plan.md)
- [summary.md](impl/frontend/iteration-1-backend-api-seed/summary.md)

**Definition of Done — агент**

- `make backend-test` и `make backend-lint` проходят; новые/изменённые сценарии покрыты тестами.
- `make db-migrate` / `make db-seed` (или `make db-reset` в среде с Docker) поднимают **демо-данные**; вход админа в БД подтверждён.
- [api-contracts.md](../tech/api/api-contracts.md) и [openapi.yaml](../tech/api/openapi.yaml) соответствуют коду (при сомнениях — `api-contract-custom`).

**Definition of Done — пользователь**

- Запустить backend (`make backend-run` или `make db-up` + `make db-migrate` + `make db-seed` по [README среды](../..)).
- Проверить новые/ключевые маршруты через OpenAPI/HTTP-клиент; убедиться, что **seed** визуально насыщен (несколько дней, записи, визиты, клиенты).

### Make / автоматизация (добавить при появлении `web/`)

- В [Makefile](../../Makefile) по мере ввода `web/`: цели `web-install`, `web-dev`, `web-lint`, `web-build` (pnpm). До создания `web/` — **запланировано** в ит. 2.

---

### iter-fe-02 — Каркас web (Next.js, shadcn, тема, layout, вход)

**Шаг дорожной карты:** 4–5 (каркас приложения `web/`)

### Цель

Создать `web/`: **Next.js App Router** + **pnpm**, **shadcn/ui** + **Tailwind**, базовая **тема**, **layout** (навигация), **вход** (профиль + выход), чат-виджет **только для клиента** (оболочка), соглашения по **env** (URL backend).

### Ценность

Повторяемый фундамент для экранов 3–6 и для последующих quality/voice/ SQL фич.

### Состав работ

- Инициализация: `web/` (pnpm), TypeScript, ESLint, структура `app/`, `components/`, `lib/`.
- Подключить **shadcn/ui** + **Tailwind**; читать и следовать skills: **shadcn**, **vercel-react-best-practices**, **nextjs-app-router-patterns** (пути в user rules / skills — уточнить в репозитории; при отсутствии файла — зафиксировать в `plan.md` итерации источник).
- **Тема** (тёмные акценты для чата, светлая/тёмная по желанию): токены, `next-themes` при необходимости.
- **Вход:** отображение текущего пользователя, кнопка «Выйти»; интеграция с решением по auth из ит. 0/1.
- **Layout:** бок/верх навигация по разделам (админ / клиент — по роли); **плавающая** кнопка чата **для клиента** (панель-заглушка → ит. 6); у админа виджет не показываем.
- [Makefile](../../Makefile): `web-install`, `web-dev`, `web-lint`, `web-build`; **корневой** [README.md](../../README.md) — как поднять backend + web.
- [vision.md](../vision.md): **frontend-стек** (закрыть open question); при необходимости **ADR** `docs/tech/adr/adr-0XX-frontend.md`.

### Артефакты

- `web/` (полный скелет).
- `web/.env.example` — `NEXT_PUBLIC_`* / `API_BASE_URL` и т.д. (без секретов).
- [Makefile](../../Makefile), [README.md](../../README.md), [vision.md](../vision.md), ADR (опционально).

**Документы**

- [plan.md](impl/frontend/iteration-2-web-skeleton/plan.md)
- [summary.md](impl/frontend/iteration-2-web-skeleton/summary.md)

**Definition of Done — агент**

- `pnpm` команды (или `make web-`*) выполняют dev/build/lint без ошибок.
- Единый **HTTP-клиент** (fetch/обёртка) с базовой обработкой ошибок; **не** хранить секреты в клиентском бандле.
- Роуты App Router **разделены** по ролям там, где требуется (middleware или server checks по контракту ит. 0/1).

**Definition of Done — пользователь**

- `make web-dev` (или `cd web && pnpm dev`) — открыть в браузере, увидеть **layout** и **заглушку** чата; проверить **вход/выход** с тестовым пользователем.

---

### iter-fe-03 — Экран «Панель администратора»

**Шаг дорожной карты:** 4 (админ-панель)

### Цель

Реализовать [Экран 1](../ui/ui-requirements.md#экран-1-панель-администратора-сервиса): KPI, сетка слотов недели, тултипы/модалки, вкладка статистики.

### Ценность

Оперативный обзор загрузки и быстрые действия по записи/визиту.

### Состав работ

- Верхние **метрики** (записи/визиты/отмены, каналы, вопросы к боту за неделю) — из API ит. 1.
- **Сетка** пн–вс × слоты; цвета и тултипы; клик → модалка (детали, отмена, подтверждение визита).
- **Модалка оценки** клиента (5★ + комментарий) после подтверждения.
- Вкладка **статистика** недели: графики/таблицы (библиотека по минимальному KISS).
- Актуализация [ui-requirements.md](../ui/ui-requirements.md) при отклонениях; скрин/описание в `summary` итерации.

### Артефакты

- `web/app/...` — маршрут админ-панели; компоненты графиков/сетки.
- Доки при необходимости: [ui-requirements.md](../ui/ui-requirements.md).

**Документы**

- [plan.md](impl/frontend/iteration-3-admin-dashboard/plan.md)
- [summary.md](impl/frontend/iteration-3-admin-dashboard/summary.md)

**Definition of Done — агент**

- Нет **хардкода** бизнес-чисел: всё с API; обработка loading/empty/error.
- Соответствие роли **admin**; некорректный токен → понятный UX.

**Definition of Done — пользователь**

- Под админом: открыть панель — KPI и сетка **без** лишних кликов для «сегодня»; клик по слоту, отмена/подтверждение, оценка; вкладка статистики отображается.

---

### iter-fe-04 — Экран «Клиенты сервиса»

**Шаг дорожной карты:** 4 (список и карточка клиента)

### Цель

[Экран 2](../ui/ui-requirements.md#экран-2-клиенты-сервиса): таблица всех клиентов; **карточка клиента** (админ) с вкладками записей/визитов и правками по контракту.

### Ценность

Единая точка для работы с клиентской базой и визитами.

### Состав работ

- Таблица: сортировка, колонки (визиты, сумма, бонусы, **рейтинг**).
- Клик по строке → **карточка** на той же странице; ссылка «К списку».
- Вкладки: предстоящие записи (отмена скрыта по умолчанию; подтверждение, правка услуг/скидки, пересчёт), подтверждённые визиты (редактирование линий, бонусов).
- **Telegram**: иконка + deep link, если есть `telegram_id` (см. UI spec).
- Правки в [api-contracts.md](../tech/api/api-contracts.md) отражены в UI (PATCH/детализации с ит. 1).

### Артефакты

- `web/app/...` — таблица и карточка клиента.
- При необходимости: [ui-requirements.md](../ui/ui-requirements.md).

**Документы**

- [plan.md](impl/frontend/iteration-4-clients/plan.md)
- [summary.md](impl/frontend/iteration-4-clients/summary.md)

**Definition of Done — агент**

- Формы **валидации** (zod + UI), оптимистичные обновления только где безопасно; после PATCH — **согласованное** состояние с сервером.
- Re-fetch или инвалидация списка после правок.

**Definition of Done — пользователь**

- Список → карточка → правка записи/визита; проверить сценарии отмены и подтверждения с модалкой оценки; Telegram-ссылка при наличии id.

---

### iter-fe-05 — Личный кабинет клиента + визард записи

**Шаг дорожной карты:** 5 (клиентский веб)

### Цель

[Экран 3](../ui/ui-requirements.md#экран-3-личный-кабинет-клиента): приветствие, CTA, списки записей/визитов, **визард** выбора услуг, слот, **LocalStorage** черновика до подтверждения.

### Ценность

Паритет с ботом для ключевого сценария «запись + история».

### Состав работ

- Главная кабинета: имя, кнопки «Запись», переход в Telegram-бот (URL из конфига).
- **Визард** на той же странице: услуги (мультивыбор) → длительность/цена/баллы (из [GET /loyalty/rules](../tech/api/api-contracts.md) + каталог) → выбор слота [GET /slots](../tech/api/api-contracts.md) → **POST** запись; ссылка «На главную»; **черновик** в `localStorage`, очистка после успешного **201**.
- Списки: предстоящие записи, отменённые (скрыты по умолчанию), визиты.
- [ui-requirements.md](../ui/ui-requirements.md) / [data-model.md](../tech/data-model.md) — согласованы поля (бонусы, статусы).

**Документы**

- [plan.md](impl/frontend/iteration-5-client-cabinet/plan.md)
- [summary.md](impl/frontend/iteration-5-client-cabinet/summary.md)

**Definition of Done — агент**

- Клиент **не** видит админ-маршруты; защита на уровне маршрутов/данных.
- LocalStorage: ключ(и) с **префиксом** проекта, восстановление черновика, отсутствие мигания при гидрации (паттерн nextjs — см. skill).

**Definition of Done — пользователь**

- Пройти визард до подтверждения; обновить страницу — черновик остаётся; после успешной записи черновик очищен; отмена записи из списка.

---

### iter-fe-06 — Чат с ассистентом (плавающий виджет)

**Шаг дорожной карты:** 4–5 (чат в UI), пересечение с этапом 3 (LLM)

### Цель

[Чат с AI-ассистентом (только роль: клиент)](../ui/ui-requirements.md#чат-с-ai-ассистентом-только-роль-клиент): плавающая кнопка, панель, **история** прокрутки, **POST** консультации с обновлением ленты (задержка/стриминг — по минимальному UX).

### Ценность

Контекстная помощь клиенту в кабинете без смены маршрута и без отдельной страницы «Чат».

### Состав работ

- **Только** плавающая панель в клиентском layout поверх маршрутов `/client`; отдельная страница «Чат» **не** делаем ([ui-requirements.md](../ui/ui-requirements.md) — длинный диалог через скролл в панели).
- UI «терминальный» стиль: тёмная панель, пользователь справа, ассистент слева + иконка.
- История: загрузка с backend (ит. 1); локальный optimistic message по необходимости.
- Обработка ошибок LLM (503 и т.д.) — **без** утечки внутренних деталей.
- [api-contracts.md](../tech/api/api-contracts.md) — согласовать, если появляется `GET` истории / пагинация.

**Документы**

- [plan.md](impl/frontend/iteration-6-chat-widget/plan.md)
- [summary.md](impl/frontend/iteration-6-chat-widget/summary.md)

**Definition of Done — агент**

- Панель **не** ломает layout; фокус и scroll к последнему сообщению; доступность (focus trap, Esc — по договорённости в `plan.md`).

**Definition of Done — пользователь**

- Войти как клиент, открыть кабинет, открыть чат, отправить вопрос, увидеть ответ; перезайти — история на месте (если требуется сессия по контракту). Убедиться, что под админом плавающего чата нет.

---

### iter-fe-07 — Ревью качества frontend (best practices)

**Шаг дорожной карты:** 6 (качество кода), сквозное по `web/`

### Цель

Проверить `web/` на соответствие **vercel-react-best-practices** и **nextjs-app-router-patterns**; устранить **критические** замечания.

### Ценность

Снижение техдолга до усложнения (голос, SQL).

### Состав работ

- Чек-лист по skills (прочитать `SKILL.md` целиком); зафиксировать находки в `impl/.../summary.md`.
- **ESLint/Prettier/типизация** — 0 критичных; при необходимости `pnpm` скрипты + [Makefile](../../Makefile).
- **Мелкие** non-critical — в общий [`docs/backlog.md`](../backlog.md); архитектурные темы — при необходимости `docs/tech/adr/`.

**Документы**

- [plan.md](impl/frontend/iteration-7-frontend-quality-review/plan.md)
- [summary.md](impl/frontend/iteration-7-frontend-quality-review/summary.md)

**Definition of Done — агент**

- `make web-lint` / `pnpm run build` зелёные; нет `any` без обоснования; нет токенов в логах клиента.

**Definition of Done — пользователь**

- Прогнать команды из [README.md](../../README.md); smoke-тест сценариев 3–6.

---

### iter-fe-08 — Голосовой режим чата (web + Telegram)

**Шаг дорожной карты:** 3–5 (голос в каналах клиента)

### Цель

**Голосовой ввод/вывод** в веб-чате и аналог в **Telegram-боте** (голосовые сообщения → текст/ответ), согласованно с backend.

### Ценность

Hands-free сценарий для клиента и владельца.

### Состав работ

- **Web:** Web Speech API или серверный STT — **проектное решение** в `plan.md` (KISS, лимиты браузеров, HTTPS); UI: запись, индикатор, ошибки микрофона.
- **Telegram:** обработка voice в `bot/` + вызовы существующего consultation API при необходимости.
- Backend: **новые** маршруты (напр. presigned, STT) — если выбран серверный путь; обновить [api-contracts.md](../tech/api/api-contracts.md), [openapi.yaml](../tech/api/openapi.yaml), [integrations.md](../tech/integrations.md).
- [data-model.md](../tech/data-model.md) / логи — при хранении метаданных консультаций.

**Документы**

- [plan.md](impl/frontend/iteration-8-voice-chat/plan.md)
- [summary.md](impl/frontend/iteration-8-voice-chat/summary.md)

**Definition of Done — агент**

- Понятные **фолбэки** при отсутствии микрофона/прав; не хранить сырой **звук** в логах.
- E2E ручного сценария описан в `summary`.

**Definition of Done — пользователь**

- Web: вручную проверить голос в поддерживаемом браузере; Bot: голосовое сообщение → ответ.

---

### iter-fe-09 — Text-to-SQL / ответы по данным БД

**Шаг дорожной карты:** 3–6 (расширенные ответы по данным)

### Цель

Зафиксировать **варианты** (Text-to-SQL, RAG с метаданными, read-only role, whitelists), выбрать **архитектуру** в [vision.md](../vision.md) / **ADR**; реализовать в backend + минимум UI при необходимости; **сценарии тестирования** (безопасность: только SELECT / ограниченный пул).

### Ценность

Расширенные вопросы к операционным данным под контролем.

### Состав работ

- Док: сравнение вариантов, угрозы (SQL injection, утечки PII) — [adr/](../tech/adr/) новый `adr-0XX` при необходимости.
- Реализация: слой **ограниченного** чтения, промпт + валидация, при необходимости отдельный read-only DSN.
- **Тесты** backend: сценарии заранее подготовленных вопросов и негативные кейсы.
- UI: точка входа (чат / админ) — согласно выбранной модели; [api-contracts.md](../tech/api/api-contracts.md) обновлён.

**Документы**

- [plan.md](impl/frontend/iteration-9-text-to-sql/plan.md)
- [summary.md](impl/frontend/iteration-9-text-to-sql/summary.md)

**Definition of Done — агент**

- Нет **произвольного** DDL/DML; аудит запросов; отказы с понятным сообщением.
- `make backend-test` зелёный; ручной чек-лист в `summary`.

**Definition of Done — пользователь**

- Прогнать **подготовленные** вопросы из `summary`; убедиться, что опасные запросы **не** выполняются.

---

## Папки артефактов итераций

Для каждой итерации создаётся каталог под `plan.md` и `summary.md`:

```
docs/tasks/impl/frontend/
├── iteration-0-ui-api-spec/
├── iteration-1-backend-api-seed/
├── iteration-2-web-skeleton/
├── iteration-3-admin-dashboard/
├── iteration-4-clients/
├── iteration-5-client-cabinet/
├── iteration-6-chat-widget/
├── iteration-7-frontend-quality-review/
├── iteration-8-voice-chat/
└── iteration-9-text-to-sql/
```

Файлы добавляются по мере выполнения итерации ([workflow](../../.cursor/rules/workflow.mdc)).

---

## Команды (текущие и план)


| Среда             | Команда                                             | Назначение                   |
| ----------------- | --------------------------------------------------- | ---------------------------- |
| Backend           | `make backend-test`                                 | pytest                       |
| Backend           | `make backend-lint`                                 | ruff                         |
| Backend           | `make backend-run`                                  | API :8000                    |
| DB                | `make db-up` / `make db-migrate` / `make db-seed`   | PostgreSQL + миграции + seed |
| Web               | `make web-install` / `make web-dev` / `make web-lint` / `make web-build` | Next.js + pnpm               |


---

_Обновлять этот tasklist: статусы в колонке «Статус» сводной таблицы (**iter-fe-00** … **iter-fe-09**) и ссылки на `plan.md` / `summary.md` по мере выполнения (см. [workflow.mdc](../../.cursor/rules/workflow.mdc)); якоря `#iter-fe-NN-…` должны совпадать со заголовками `### iter-fe-NN — …` в рендерере Markdown._