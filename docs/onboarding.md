# Онбординг нового участника «Переобуйка»

Пошаговый гайд: от клонирования до первых изменений. Краткая версия — в [README.md](../README.md); архитектура — [architecture.md](architecture.md).

---

## 1. Клонирование и первичная настройка

### Требования

| Инструмент | Версия / примечание |
|------------|---------------------|
| Python | 3.12+ |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | пакетный менеджер backend и bot |
| Node.js | 22+ |
| [pnpm](https://pnpm.io/installation) | только для `web/` |
| Docker Desktop | PostgreSQL локально, Testcontainers для backend-тестов |
| GNU Make | цели из корневого `Makefile` (Windows: Git Bash, WSL или отдельная установка) |

### Клонирование

```bash
git clone <url-репозитория> pereobuyka
cd pereobuyka
```

### Шаблоны окружения

Из **корня** репозитория (PowerShell):

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item bot\.env.example bot\.env
Copy-Item web\.env.example web\.env
```

Секреты не коммитить (`.env` в `.gitignore`).

---

## 2. Настройка каждого компонента

### База данных (PostgreSQL)

Рекомендуется для полного API, миграций и seed. В `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://pereobuyka:pereobuyka@127.0.0.1:5432/pereobuyka
```

```bash
make db-up
make db-migrate
make db-seed
```

Альтернатива без Docker: в `backend/.env.example` по умолчанию **SQLite** (`sqlite+aiosqlite:///./dev.db`) — быстрый прогон, но **без** Alembic/seed и с урезанным набором маршрутов (см. [backend/README.md](../backend/README.md)).

Проверка БД: `make db-psql` → `\dt` (список таблиц).

### Backend

```bash
make backend-install
```

В `backend/.env` при необходимости:

| Переменная | Назначение |
|------------|------------|
| `BOT_SECRET` | Общий секрет с ботом (одинаковое значение в `bot/.env`) |
| `ADMIN_API_TOKEN` | Bearer для маршрутов `/api/v1/admin/*` (локальная админка) |
| `OPENROUTER_API_KEY` | LLM-консультация (`/api/v1/consultation/messages`) |
| `SPEECH_TO_TEXT_*` | STT для голоса (ADR-005) |

Запуск:

```bash
make backend-run
```

Слушает `http://127.0.0.1:8000` (предпочитайте **127.0.0.1**, не `localhost`, на Windows — см. README).

### Web

```bash
make web-install
```

В `web/.env` по умолчанию:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Запуск (backend должен быть поднят):

```bash
make web-dev
```

Приложение: `http://localhost:3000`. Маршруты: `/admin`, `/client`, вход через формы (см. `web/components/auth/`).

### Bot

```bash
make bot-install
```

В `bot/.env`:

| Переменная | Обязательна | Примечание |
|------------|-------------|------------|
| `TELEGRAM_BOT_TOKEN` | да | от `@BotFather` |
| `BACKEND_BASE_URL` | да для API | `http://127.0.0.1:8000` |
| `BOT_SECRET` | да для защищённых вызовов | = `BOT_SECRET` в backend |

```bash
make bot-run
```

Точка входа: `run_bot.py` (как в `Makefile`).

---

## 3. Проверка, что всё работает

### Backend

| Проверка | Команда / URL | Ожидаемый результат |
|----------|---------------|---------------------|
| Health | `curl http://127.0.0.1:8000/health` | HTTP **200**, тело `{"status":"ok"}` |
| Swagger | браузер `http://127.0.0.1:8000/docs` | UI OpenAPI |
| Каталог услуг | `curl http://127.0.0.1:8000/api/v1/services` | HTTP **200**, JSON с массивом `services` (после seed на PostgreSQL — не пустой) |
| Тесты | `make backend-test` | **pytest**: все тесты passed (нужен **запущенный Docker**) |
| Линтер | `make backend-lint` | ruff: All checks passed |

### Web

| Проверка | Команда / URL | Ожидаемый результат |
|----------|---------------|---------------------|
| Dev-сервер | `make web-dev` | в логе `Ready`, страница открывается |
| Главная | `http://localhost:3000` | каркас с ссылками на разделы |
| Линт / сборка | `make web-lint` · `make web-build` | без ошибок |
| Тесты | `make web-test` | сообщение `web: no automated tests yet` и код выхода **0** (заглушка) |

### Bot

| Проверка | Действие | Ожидаемый результат |
|----------|----------|---------------------|
| Старт | `make bot-run` | в логе нет traceback, polling активен |
| Диалог | `/start` в Telegram | ответ бота, меню |
| API | при заданном `BOT_SECRET` | команды `/services`, `/book` не падают с ошибкой авторизации backend |

### Bot + LLM (опционально)

При `OPENROUTER_API_KEY` в backend: `/ask` в боте → ответ консультации или понятная ошибка 503 при недоступности провайдера.

---

## 4. Куда смотреть в первую очередь

### Карта репозитория

| Путь | Назначение |
|------|------------|
| [docs/vision.md](vision.md) | Границы системы, стек, слои, правила LLM |
| [docs/architecture.md](architecture.md) | Схема компонентов и потоков |
| [docs/tech/data-model.md](tech/data-model.md) | Сущности и связи |
| [docs/tech/api/openapi.yaml](tech/api/openapi.yaml) | Контракт HTTP API |
| [Makefile](../Makefile) | Все команды `make` |

### Точки входа в коде

| Компонент | Файл | Что внутри |
|-----------|------|------------|
| Backend app | `backend/src/pereobuyka/main.py` | FastAPI, lifespan, `/health`, роутер `/api/v1` |
| API v1 | `backend/src/pereobuyka/api/v1/router.py` | Публичные маршруты + `routes_extended` |
| Расширенные маршруты | `backend/src/pereobuyka/api/v1/routes_extended.py` | auth, admin, client, consultation |
| Сервисы | `backend/src/pereobuyka/services/` | Бизнес-правила |
| Хранилище | `backend/src/pereobuyka/storage/` | memory (SQLite dev), postgres_repos |
| Web layout | `web/app/layout.tsx` | корневой layout, тема |
| Web API-клиент | `web/lib/api.ts`, `web/lib/client-api.ts`, `web/lib/admin-api.ts` | вызовы backend |
| Bot | `bot/run_bot.py` → `bot/src/pereobuyka/main.py` | aiogram, polling |
| Handlers бота | `bot/src/pereobuyka/bot/handlers/` | `/start`, `/book`, `/ask`, … |
| HTTP-клиент бота | `bot/src/pereobuyka/client/backend.py` | запросы к backend |

### Документы по UI

- [docs/ui/ui-requirements.md](ui/ui-requirements.md) — экраны и поведение
- [docs/tasks/tasklist-frontend.md](tasks/tasklist-frontend.md) — итерации фронтенда

---

## 5. Рабочий процесс

Проект ведётся **спек-driven / итерационно** (см. [`.cursor/rules/workflow.mdc`](../.cursor/rules/workflow.mdc)):

1. **Область** — backend, frontend, bot, database, … → файл `docs/tasks/tasklist-<область>.md`.
2. **Итерация** — крупный инкремент → `docs/tasks/impl/<область>/iteration-N-*/plan.md` и `summary.md`.
3. **Задача** — атом внутри итерации → `tasks/task-*/plan.md` и `summary.md`.

Дорожная карта этапов продукта: [docs/plan.md](plan.md). Отложенные улучшения: [docs/backlog.md](backlog.md).

Для AI-агентов: [docs/AGENTS.md](AGENTS.md), skills в [`.agents/skills/`](../.agents/skills/).

---

## 6. Как готовить изменения

Перед PR (локально, из корня):

| Область | Команды |
|---------|---------|
| Backend | `make backend-lint` · `make backend-test` |
| Bot | `make bot-lint` · `make bot-test` |
| Web | `make web-lint` · `make web-build` · `make web-test` |

Подробности и источники истины: [CONTRIBUTING.md](../CONTRIBUTING.md).

Код-конвенции: [`.cursor/rules/convensions.mdc`](../.cursor/rules/convensions.mdc) (handlers/API тонкие, бизнес-логика в services, LLM не «придумывает» цены и слоты).

**CI в репозитории пока нет** — проверки выполняются локально.

---

## Связанные документы

- [README.md](../README.md) — быстрый старт и ключи
- [architecture.md](architecture.md) — архитектурная схема
- [doc-audit.md](doc-audit.md) — известные расхождения документации с кодом
