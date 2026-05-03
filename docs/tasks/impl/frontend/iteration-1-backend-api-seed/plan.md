# План iter-fe-01 — Backend API, миграции, seed, админ в БД

## Цель

Подготовить backend и PostgreSQL к экранам веба (iter-fe-00): новые поля и таблица `consultation_messages`, агрегаты админ-панели, мутации записей/визитов и оценок, вход `POST /api/v1/auth/web`, расширить seed для локальной демо.

## Шаги (факт выполнения)

1. Alembic `0002_web_ui`: `users.telegram_username`, расширение `appointments`/`visits`, таблица `consultation_messages`.
2. ORM, адаптеры, `insert_appointment` с источником и скидкой; `POST /auth/web`.
3. Сервисы `admin_web_dashboard.py`, мутации `admin_mutations_pg.py`, эндпоинты в `admin_web.py`, клиентские рейтинги и история консультаций.
4. Тесты, `make backend-lint`; `conftest`: `TRUNCATE consultation_messages`.
5. Seed: клиенты с `telegram_username`, записи на несколько будних дней, источники, завершённые визиты с рейтингами, пара сообщений консультации.
6. Документация: синхронизация `api-contracts.md`, `openapi.yaml`; этот план и `summary.md`.

## Результат

См. [`summary.md`](summary.md).
