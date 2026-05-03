# iter-be-03 — Каркас backend: план реализации

## Цель

Поднять воспроизводимый каркас сервиса по [`docs/vision.md`](../../../../vision.md): структура `backend/`, конфигурация, health-эндпоинт, `Makefile`.

---

## Стек

| Компонент | Пакет |
|-----------|-------|
| HTTP-фреймворк | `fastapi>=0.115` |
| ASGI-сервер | `uvicorn[standard]>=0.30` |
| Конфигурация | `pydantic-settings>=2.0` |
| ORM | `sqlalchemy[asyncio]>=2.0` (заготовка) |
| Драйвер БД | `asyncpg>=0.29` (заготовка) |
| Миграции | `alembic>=1.13` (заготовка) |
| Линтер | `ruff>=0.5` (dev) |
| Тесты | `pytest>=8.0`, `pytest-asyncio>=0.23`, `httpx>=0.27` (dev) |
| SQLite dev | `aiosqlite>=0.19` (dev) |

---

## Структура файлов

```
backend/
├── pyproject.toml
├── .env.example
└── src/
    └── pereobuyka/
        ├── __init__.py
        ├── main.py          # FastAPI app + lifespan + /health
        ├── config.py        # pydantic-settings
        ├── api/
        │   ├── __init__.py
        │   └── v1/
        │       ├── __init__.py
        │       └── router.py    # пустой APIRouter (заготовка)
        ├── services/
        │   └── __init__.py
        ├── storage/
        │   └── __init__.py
        ├── models/
        │   └── __init__.py
        └── llm/
            └── __init__.py
```

---

## Ключевые решения

- `backend/` — отдельный `uv`-проект (`pyproject.toml`), независимый от корневого.
- `GET /health` — на корневом уровне (`/health`), не под `/api/v1/`, чтобы не требовать авторизации и не зависеть от версии API.
- `config.py` — `pydantic-settings`; `DATABASE_URL` по умолчанию `sqlite+aiosqlite:///./dev.db` (только dev); при пустом значении сервер стартует, но предупреждает о необходимости настройки перед подключением к БД.
- SQLAlchemy, asyncpg, alembic — добавляются в зависимости уже сейчас (по ADR-003), но не используются в iter-be-03; это избегает повторного изменения `pyproject.toml` в iter-be-05.
- Логирование: `logging.basicConfig` из `log_level` конфига при старте lifespan.

---

## Makefile (корневой)

**Примечание:** в корневом `Makefile` цели `install` и `run` — алиасы на **бота** (`bot-install` / `bot-run`). Для каркаса backend используются только цели с префиксом `backend-` (согласовано с таблицей проверки iter-be-03 в [`tasklist-backend.md`](../../../tasklist-backend.md)).

Добавляются цели с префиксом `backend-`:

| Цель | Команда |
|------|---------|
| `backend-install` | `cd backend && uv sync` |
| `backend-run` | `cd backend && uv run uvicorn pereobuyka.main:app --reload --port 8000` |
| `backend-test` | `cd backend && uv run pytest` |
| `backend-lint` | `cd backend && uv run ruff check .` |

---

## Definition of Done

- `make backend-install` завершается без ошибок
- `make backend-run` стартует; `GET /health` возвращает `{"status": "ok"}`
- `make backend-lint` — без ошибок
- Нет секретов в репозитории
