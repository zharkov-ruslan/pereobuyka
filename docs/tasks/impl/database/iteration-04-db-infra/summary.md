# iter-db-04 — summary

## Результат

- **Compose:** [docker-compose.yml](../../../../../docker-compose.yml) — `postgres:16-alpine`, порт `5432`, пользователь/БД `pereobuyka`, volume `pgdata`, healthcheck `pg_isready`.
- **Make:** в [Makefile](../../../../../Makefile) добавлены `db-up` (`up -d --wait`), `db-down`, `db-reset` (`down -v` → `up --wait` → `alembic upgrade head` → seed), `db-migrate`, `db-seed`, `db-psql`.
- **Миграция:** [backend/alembic/versions/0001_initial_schema.py](../../../../../backend/alembic/versions/0001_initial_schema.py) — схема из физической модели в [data-model.md](../../../../../docs/tech/data-model.md).
- **Seed:** [backend/src/pereobuyka/scripts/seed.py](../../../../../backend/src/pereobuyka/scripts/seed.py), запуск `uv run python -m pereobuyka.scripts.seed` из `backend/` (или `make db-seed` из корня).
- **Документация:** [backend/.env.example](../../../../../backend/.env.example), [backend/README.md](../../../../../backend/README.md), [database-migrations.md](../../../../../docs/tech/database-migrations.md), корневой [README.md](../../../../../README.md) (краткая отсылка к БД).

## Зависимости

- `psycopg[binary]` в [backend/pyproject.toml](../../../../../backend/pyproject.toml) для Alembic и seed.

## Примечания

- `db-reset` **разрушительный** для данных локального dev (`docker compose down -v`).
- Для `make db-migrate` / seed в `backend/.env` нужен `DATABASE_URL` на PostgreSQL (`postgresql+asyncpg://…`); SQLite остаётся вариантом для API без Docker.
- Следующий шаг по дорожной карте БД: **iter-db-05** (ORM, репозитории, Testcontainers, замена in-memory).
