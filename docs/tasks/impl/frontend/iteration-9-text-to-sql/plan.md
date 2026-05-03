# План: iter-fe-09 — Text-to-SQL / ответы по данным БД

## Цель

Безопасный канал для администратора: вопрос на естественном языке → один проверенный SELECT → строки + краткое резюме через LLM.

## Архитектура

- **ADR-006:** сравнение вариантов, выбор NL→SQL с AST-валидацией и whitelist таблиц.
- **Backend:** `safe_nl_sql.py` (sqlglot), `admin_nl_sql_service.py`, `POST /api/v1/admin/analytics/data-insight` под `AdminActor`.
- **Конфиг:** `admin_nl_sql_max_rows`, `admin_nl_sql_statement_timeout_ms`.
- **Тесты:** юнит валидатора + интеграция эндпоинта с подменой LLM.
- **Web:** карточка на странице админ-панели с формулировкой вопроса и выводом результата.

## Задачи

1. ADR + обновление `vision.md`, `api-contracts.md`, `openapi.yaml`.
2. Реализация сервиса и эндпоинта, зависимость `sqlglot`.
3. UI админки + клиент `postAdminDataInsight`.
4. Тесты, прогон `make backend-test` / lint.
