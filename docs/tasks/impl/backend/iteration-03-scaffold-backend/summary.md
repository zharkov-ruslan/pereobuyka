# iter-03 — Каркас backend: итоги

## Что реализовано

- **`backend/pyproject.toml`** — отдельный `uv`-проект с зависимостями:
  FastAPI, uvicorn[standard], pydantic-settings, SQLAlchemy[asyncio], asyncpg, alembic, python-dotenv.
  Dev-зависимости: pytest, pytest-asyncio, httpx, ruff, aiosqlite.
- **`backend/src/pereobuyka/`** — пакет по структуре из `docs/vision.md`:
  `main.py`, `config.py`, `api/v1/router.py`, заглушки `services/`, `storage/`, `models/`, `llm/`.
- **`GET /health`** — возвращает `{"status": "ok"}`, проверено вручную.
- **`backend/.env.example`** — переменные окружения с комментариями (DATABASE_URL, LOG_LEVEL, OpenRouter).
- **Корневой `Makefile`** — добавлены цели: `backend-install`, `backend-run`, `backend-test`, `backend-lint`.

## Отклонения от плана

Нет. Реализация полностью соответствует `plan.md`.

## Принятые решения

- `GET /health` размещён на корневом уровне (`/health`), а не под `/api/v1/` — стандартная практика для infrastructure-эндпоинтов без авторизации.
- SQLAlchemy, asyncpg, alembic добавлены в зависимости уже сейчас (по ADR-003), хотя в iter-03 не используются — избегает повторной правки `pyproject.toml` в iter-05.
- `config.py` использует `pydantic-settings` v2 (`SettingsConfigDict`); `DATABASE_URL` имеет дефолт `sqlite+aiosqlite:///./dev.db` только для dev.

## Проверка

| Проверка | Результат |
|----------|-----------|
| `uv sync` | ✅ 38 пакетов установлено |
| `uvicorn pereobuyka.main:app` | ✅ стартует, `Application startup complete` |
| `GET /health` | ✅ `{"status": "ok"}` |
| `ruff check .` | ✅ `All checks passed!` |

## Артефакты

- [`backend/pyproject.toml`](../../../../../backend/pyproject.toml)
- [`backend/src/pereobuyka/main.py`](../../../../../backend/src/pereobuyka/main.py)
- [`backend/src/pereobuyka/config.py`](../../../../../backend/src/pereobuyka/config.py)
- [`backend/src/pereobuyka/api/v1/router.py`](../../../../../backend/src/pereobuyka/api/v1/router.py)
- [`backend/.env.example`](../../../../../backend/.env.example)
- [`Makefile`](../../../../../Makefile)
