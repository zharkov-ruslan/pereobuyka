# Итог iter-fe-01 — Backend API, миграции, seed

## Реализовано в коде

- **Миграция** [`backend/alembic/versions/0002_web_ui_extensions.py`](../../../../backend/alembic/versions/0002_web_ui_extensions.py): частичный уникальный индекс по `telegram_username`; у записей — `source`, `discount_percent`, `created_by_user_id`; у визитов — поля рейтингов; таблица `consultation_messages`.
- **Аутентификация:** `POST /api/v1/auth/web` (`WebAuthRequest`), в ответах `User` включает `telegram_username`.
- **Админ (веб):** `GET /admin/dashboard/today`, `/admin/dashboard/week-grid`, `/admin/analytics/week`, `/admin/clients`, `/admin/clients/{user_id}`, `/admin/users/{user_id}/appointments`; `PATCH /admin/appointments/{id}`, `/admin/visits/{id}`; `POST /admin/visits/{visit_id}/client-rating`.
- **Клиент:** `POST /api/v1/me/visits/{visit_id}/service-rating`; **Consultation:** персист сообщений после ответа LLM, `GET /consultation/messages` (история).

## Seed

Идемпотентное наполнение в [`backend/src/pereobuyka/scripts/seed.py`](../../../../backend/src/pereobuyka/scripts/seed.py): базовые loyalty/services/schedule/admin сохранены; добавлены демо-клиенты, записи на текущую календарную неделю (Europe/Moscow), смешанные источники и статусы, завершённые визиты с оценками при необходимости, сообщения консультации для одного клиента.

## Документы API

Обновлены [`docs/tech/api/api-contracts.md`](../../../../tech/api/api-contracts.md) и [`docs/tech/api/openapi.yaml`](../../../../tech/api/openapi.yaml) в соответствии с реализованными маршрутами и полями сущностей.

## Проверки

- `make backend-test` — зелёный.
- `make backend-lint` — зелёный.

## Зависимости для следующей итерации (iter-fe-02)

Каркас Next.js: переменные окружения для `API_BASE_URL`, использование Bearer из `POST /auth/web` или существующих потоков тестирования админа.
