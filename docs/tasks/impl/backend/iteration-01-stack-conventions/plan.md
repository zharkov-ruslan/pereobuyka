# План: iter-01 — Stack & conventions

## Цель

Зафиксировать выбор **FastAPI** + **Pydantic** как стека HTTP, **SQLAlchemy 2** (async) + **Alembic** для данных, оформить **ADR-002** и **ADR-003**, синхронизировать `docs/vision.md` и `.cursor/rules/convensions.mdc`.

## Шаги

1. Сравнить FastAPI, Litestar, Django REST, Starlette (критерии: OpenAPI, async, экосистема, соответствие vision).
2. Добавить `docs/tech/adr/adr-002-backend-framework.md` и строку в `docs/tech/adr/README.md`.
3. Сравнить варианты доступа к БД (SQLAlchemy, SQLModel, Tortoise, только SQL); оформить `docs/tech/adr/adr-003-orm.md`, согласовать формулировку миграций в ADR-001.
4. Обновить таблицу стека и реестр ADR в `docs/vision.md`; убрать backend-фреймворк из открытых вопросов.
5. Расширить `convensions.mdc`: тонкий слой API (FastAPI), `Depends`, pytest для API.

## Артефакты

- `docs/tech/adr/adr-002-backend-framework.md`
- `docs/tech/adr/adr-003-orm.md`
- правки: `docs/vision.md`, `docs/tech/adr/README.md`, `docs/tech/adr/adr-001-database.md`, `.cursor/rules/convensions.mdc`, `docs/tasks/tasklist-backend.md`
