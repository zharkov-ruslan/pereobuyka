# iter-db-05 — план

1. Пакет `pereobuyka.db`: `Base`, ORM-модели под таблицы MVP (`users`, `services`, `schedule_rules`, `appointments`, `appointment_services`), async `create_engine` / `async_sessionmaker`, зависимость `get_db_session` (commit/rollback на запрос).
2. `lifespan` в `main.py`: `init_db_engine` / `dispose_db_engine` для PostgreSQL.
3. `storage/postgres_repos.py`: функции репозитория (каталог, расписание по `schedule_rules`, список записей, вставка записи, `ensure_user_exists` для FK).
4. Сервисы `slot_service` / `appointment_service`: общая логика слотов; ветка `session is None` → `memory.py` (SQLite), иначе PostgreSQL.
5. Роутеры v1: async + `Depends(get_db_session)`.
6. `tests/conftest.py`: Testcontainers PostgreSQL, Alembic + seed, `TRUNCATE` между тестами; при необходимости отключение Ryuk для Windows.
7. Документация: README, `plan.md`, tasklist.
