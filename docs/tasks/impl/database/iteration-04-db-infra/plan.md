# iter-db-04 — план

1. Зафиксировать PostgreSQL в Docker в корне (`docker-compose.yml`, healthcheck, volume `pgdata`).
2. Добавить цели `Makefile`: `db-up`, `db-down`, `db-reset` (с предупреждением о `down -v`), `db-migrate`, `db-seed`, `db-psql`.
3. Первая ревизия Alembic: DDL по [data-model.md](../../../../../tech/data-model.md) (таблицы, FK, CHECK по длине, индексы на FK).
4. Seed-скрипт на `psycopg`: `loyalty_settings`, `schedule_rules` (0–4 рабочие часы как в `memory.WORKING_HOURS`, 5–6 выходные), услуга с `DEFAULT_SERVICE_ID`; идемпотентность через `ON CONFLICT DO NOTHING`.
5. Обновить `backend/.env.example`, `backend/README.md`, при необходимости корневой `README.md`, [database-migrations.md](../../../../../tech/database-migrations.md).
