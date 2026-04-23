# iter-db-03 — Summary

## Результат

- Принят [ADR-004](../../../../tech/adr/adr-004-database-migrations-workflow.md): Alembic в `backend/`, `alembic.ini`, `alembic/versions/`, политика ревизий и downgrade, связь с `DATABASE_URL`, отсылки к iter-db-04/05.
- Добавлена справка [database-migrations.md](../../../../tech/database-migrations.md): предпосылки, таблица команд, autogenerate vs ручные правки, Testcontainers.
- Реестр ADR и перекрёстные ссылки в ADR-001, ADR-003; vision §8 и §11 дополнены ADR-004 и ссылкой на справку.
- [plan.md](../../../../plan.md) и [tasklist-database.md](../../../tasklist-database.md) отражают выполнение iter-db-03.

## DoD

| Критерий | Статус |
|----------|--------|
| ADR в реестре, статус Accepted | Да |
| Справка даёт порядок действий до появления реального `alembic/` в коде | Да |
| ADR-001 ↔ ADR-003 ↔ ADR-004 согласованы | Да |

## Примечание

Команды `uv run alembic` станут исполнимы после **iter-db-04** (инициализация Alembic и инфраструктуры БД).
