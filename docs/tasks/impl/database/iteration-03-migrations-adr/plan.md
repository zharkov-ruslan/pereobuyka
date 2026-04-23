# iter-db-03 — План

## Цель

Зафиксировать workflow **Alembic** в репозитории отдельным **ADR-004**, обновить реестр ADR и связку ADR-001/003, добавить практическую справку [database-migrations.md](../../../../tech/database-migrations.md), обновить vision §8 и §11.

## Шаги

1. Написать [adr-004-database-migrations-workflow.md](../../../../tech/adr/adr-004-database-migrations-workflow.md) (каталог `backend/`, ревизии, autogenerate, downgrade, `DATABASE_URL`).
2. Добавить [database-migrations.md](../../../../tech/database-migrations.md) с командами `uv run alembic`, ссылками на ADR и Testcontainers (iter-db-05).
3. Обновить [README.md](../../../../tech/adr/README.md), [adr-001](../../../../tech/adr/adr-001-database.md), [adr-003](../../../../tech/adr/adr-003-orm.md), [vision.md](../../../../vision.md), [plan.md](../../../../plan.md), [tasklist-database.md](../../../tasklist-database.md).
