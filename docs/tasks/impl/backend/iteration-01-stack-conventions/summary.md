# Summary: iter-be-01 — Stack & conventions

## Результат

- Принят **ADR-002**: HTTP-backend на **FastAPI**, валидация/схемы — **Pydantic**, OpenAPI из кода; в ADR зафиксированы альтернативы (Litestar, Django REST, Starlette, Flask/Quart) и последствия для зависимостей при появлении `backend/`.
- Принят **ADR-003**: **SQLAlchemy 2.x** (async, **asyncpg**), миграции — **Alembic**; граница Pydantic (API) и ORM-моделей (персистентность); [ADR-001](../../../../tech/adr/adr-001-database.md) обновлён — инструмент миграций отсылает к ADR-003.
- **`docs/vision.md`**: строки стека «Backend-фреймворк» и «ORM / доступ к БД», таблица ADR в §11; пункт про выбор фреймворка убран из §12 «Открытые вопросы».
- **`convensions.mdc`**: явно описан тонкий слой API (роутеры, Pydantic, `Depends`) и ориентиры по **pytest** для API-тестов.
- **`tasklist-backend.md`**: iter-be-01 отмечен выполненным; артефакты включают ADR-002 и ADR-003.

## Отклонения от плана

Нет.

## Связь с tasklist

Критерии и артефакты совпадают с разделом **iter-be-01** в [`tasklist-backend.md`](../../../tasklist-backend.md) (ADR-002/003, vision, `convensions.mdc`).

## Зависимости для следующих итераций

- iter-be-02: контракт API (схемы Pydantic / OpenAPI-описание).
- iter-be-03: каркас `backend/` с `fastapi`, ASGI-сервером (например `uvicorn`), зависимости ORM/миграций по ADR-003 в `pyproject.toml`.
