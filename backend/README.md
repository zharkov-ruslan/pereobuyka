# Переобуйка — Backend

FastAPI-сервис: бизнес-логика записи, расписания, прайса и лояльности для шиномонтажного сервиса «Переобуйка».

## Требования

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) — пакетный менеджер

## Быстрый старт

### 1. Установка зависимостей

```bash
make backend-install
```

Либо вручную из папки `backend/`:

```bash
cd backend
uv sync
```

### 2. Настройка окружения

Скопировать `.env.example` в `.env` и заполнить переменные:

```powershell
Copy-Item backend/.env.example backend/.env
```

- **SQLite (по умолчанию в `.env.example`):** `sqlite+aiosqlite:///./dev.db` — файл создаётся автоматически; **Alembic и seed** на SQLite не запускаются (см. `alembic/env.py`).
- **PostgreSQL:** задайте `DATABASE_URL=postgresql+asyncpg://pereobuyka:pereobuyka@127.0.0.1:5432/pereobuyka` и поднимите БД из **корня** репозитория (`make db-up`).

Переменные окружения имеют приоритет над `.env`.

## База данных (PostgreSQL в Docker)

Нужны **Docker** и **Make** из корня монорепозитория (рядом с `docker-compose.yml`). В корневом [Makefile](../Makefile) задано `COMPOSE_PROJECT_NAME=pereobuyka`, чтобы `docker compose` не падал с пустым именем проекта на путях с не-ASCII (типично Windows).

| Команда | Действие |
|---------|----------|
| `make db-up` | Запустить PostgreSQL 16 и дождаться healthcheck |
| `make db-down` | Остановить контейнер (данные в volume сохраняются) |
| `make db-migrate` | `alembic upgrade head` из `backend/` (нужен `DATABASE_URL` на PostgreSQL в `.env`) |
| `make db-seed` | Идемпотентный seed (`loyalty_settings`, `schedule_rules`, одна услуга с UUID как в `memory.py`) |
| `make db-psql` | Интерактивный `psql` внутри контейнера |
| `make db-reset` | **`docker compose down -v`** — удаляет volume с данными, затем `up --wait`, миграции и seed |

Типовой цикл после клонирования:

```bash
make db-up
# в backend/.env — postgresql+asyncpg://...
make db-migrate
make db-seed
make db-psql
```

Справка по миграциям: [`docs/tech/database-migrations.md`](../docs/tech/database-migrations.md).

### 3. Запуск сервера

```bash
make backend-run
```

Сервер стартует на `http://localhost:8000`.

- **Health check:** `http://localhost:8000/health`
- **OpenAPI (Swagger UI):** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Остановить сервер:

```bash
make backend-stop
```

## Переменные окружения

Все переменные описаны в `backend/.env.example`.

| Переменная | Обязательна | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `DATABASE_URL` | нет | `sqlite+aiosqlite:///./dev.db` | URL БД: SQLite для быстрых прогонов; PostgreSQL — `postgresql+asyncpg://...` (локально см. `make db-up`) |
| `LOG_LEVEL` | нет | `INFO` | Уровень логирования: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `OPENROUTER_API_KEY` | нет | *(пусто)* | API-ключ OpenRouter — нужен только для LLM-консультации (этап 3) |
| `OPENROUTER_MODEL` | нет | `openai/gpt-4o-mini` | Идентификатор модели OpenRouter |
| `OPENROUTER_BASE_URL` | нет | `https://openrouter.ai/api/v1` | Base URL OpenRouter API |
| `CONSULTATION_LLM_TIMEOUT_SECONDS` | нет | `45` | Таймаут HTTP к OpenRouter (секунды) |
| `CONSULTATION_MAX_TOOL_ROUNDS` | нет | `6` | Максимум раундов function-calling на один запрос консультации |
| `CONSULTATION_SYSTEM_PROMPT` | нет | *(пусто)* | Полный системный промпт; если пусто — используется дефолт из кода |

> Не публикуй `.env` в репозиторий — он добавлен в `.gitignore`.

## Команды Make

| Команда | Описание |
|---------|----------|
| `make backend-install` | Установить зависимости (`uv sync`) |
| `make backend-run` | Запустить сервер с `--reload` на порту 8000 |
| `make backend-stop` | Остановить процесс на порту 8000 (Windows/PowerShell) |
| `make backend-test` | Запустить тесты (`pytest`) |
| `make backend-lint` | Проверить стиль кода (`ruff check` + `ruff format --check`) |
| `make db-up` / `db-migrate` / … | См. раздел «База данных» (из **корня** репозитория) |

## Тесты и линтер

```bash
make backend-test   # pytest — должно быть: N passed
make backend-lint   # ruff — должно быть: All checks passed
```

**pytest и БД:** сессия поднимает **PostgreSQL** через [Testcontainers](https://testcontainers.com/) (`postgres:16-alpine`), выполняет `alembic upgrade head` и `seed`, затем **TestClient**. Перед каждым тестом таблицы записей очищаются (`TRUNCATE …`). Нужен **запущенный Docker**. На части установок Windows контейнер reaper Ryuk даёт сбой порта 8080 — в [`tests/conftest.py`](tests/conftest.py) по умолчанию задано `TESTCONTAINERS_RYUK_DISABLED=true`.

## Структура пакета

```
backend/
├── src/pereobuyka/
│   ├── api/v1/          # Роутеры и Pydantic-схемы
│   ├── db/              # SQLAlchemy DeclarativeBase, ORM-модели, async session
│   ├── services/        # Бизнес-логика (слоты, записи)
│   ├── storage/         # memory.py (SQLite dev), postgres_repos.py (PostgreSQL)
│   ├── scripts/         # seed и др. обслуживание
│   ├── models/          # Доменные модели
│   ├── config.py        # Настройки из env
│   ├── main.py          # FastAPI app, lifespan, обработчики ошибок
│   └── utils.py         # Вспомогательные функции
└── tests/               # pytest (Testcontainers + API)
```

## API-контракт

Полная спецификация: [`docs/tech/api/openapi.yaml`](../docs/tech/api/openapi.yaml)  
Описание контрактов: [`docs/tech/api/api-contracts.md`](../docs/tech/api/api-contracts.md)  
Модель ошибок: [`docs/tech/api/errors.md`](../docs/tech/api/errors.md)
