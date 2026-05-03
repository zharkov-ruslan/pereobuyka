# Architecture Decision Records

ADR — короткие документы, фиксирующие архитектурные решения: что выбрано, почему, какие альтернативы рассматривались.

## Принципы

- Одно решение — один файл.
- Статус фиксируется и обновляется при пересмотре.
- Решение не удаляется при отмене — статус меняется на `Superseded`, добавляется ссылка на новый ADR.
- Формат: контекст → варианты → решение → обоснование → последствия.

## Статусы

| Статус | Значение |
|--------|----------|
| `Proposed` | Вынесено на согласование |
| `Accepted` | Принято |
| `Superseded` | Отменено, заменено другим ADR |
| `Deprecated` | Устарело, пересмотр не планируется |

## Список решений

| # | Решение | Статус |
|---|---------|--------|
| [ADR-001](adr-001-database.md) | Выбор СУБД | Accepted |
| [ADR-002](adr-002-backend-framework.md) | HTTP-фреймворк backend (FastAPI) | Accepted |
| [ADR-003](adr-003-orm.md) | ORM и миграции (SQLAlchemy 2 async, Alembic) | Accepted |
| [ADR-004](adr-004-database-migrations-workflow.md) | Workflow миграций Alembic в `backend/` | Accepted |
| [ADR-005](adr-005-speech-to-text.md) | Серверный STT для голосовых консультаций (Telegram) | Accepted |
| [ADR-006](adr-006-text-to-sql.md) | Админские вопросы к БД: NL→SQL с валидацией AST и белым списком таблиц | Accepted |
