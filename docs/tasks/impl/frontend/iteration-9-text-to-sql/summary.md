# Summary: iter-fe-09 — Text-to-SQL / ответы по данным БД

## Результат

- **[ADR-006](../../../tech/adr/adr-006-text-to-sql.md):** зафиксированы угрозы и решение (NL→SQL только для админа, sqlglot, whitelist таблиц `public`, обёртка LIMIT, `statement_timeout`, аудит в логах, второй вызов LLM для резюме).
- **Backend:** `sqlglot`; модули `services/safe_nl_sql.py`, `services/admin_nl_sql_service.py`; эндпоинт `POST /api/v1/admin/analytics/data-insight`; расширен `OpenRouterChatClient.create_chat_completion_text` для JSON/text completions без tools.
- **Конфиг:** `admin_nl_sql_max_rows`, `admin_nl_sql_statement_timeout_ms` ([`config.py`](../../../../../backend/src/pereobuyka/config.py)).
- **Контракты:** обновлены [`api-contracts.md`](../../../tech/api/api-contracts.md), [`openapi.yaml`](../../../tech/api/openapi.yaml).
- **Web:** карточка «Вопрос к данным» на [`web/app/admin/page.tsx`](../../../../../web/app/admin/page.tsx); [`postAdminDataInsight`](../../../../../web/lib/admin-api.ts).
- **Тесты:** [`tests/test_safe_nl_sql.py`](../../../../../backend/tests/test_safe_nl_sql.py), [`tests/test_admin_data_insight.py`](../../../../../backend/tests/test_admin_data_insight.py).

## Ручная проверка

1. PostgreSQL + seed, `ADMIN_API_TOKEN`, `OPENROUTER_API_KEY`.
2. Войти в админку web, открыть панель, ввести вопрос (например: «Сколько записей в статусе scheduled?» или "Какой процент подтвержденных визитов и отмен от общего количества записей отдельно за прошлую и текущую недели?"), отправить.
3. Убедиться, что опасные формулировки дают **400** `NL_SQL_REJECTED`, без DDL/DML в ответе.

## Отклонения от изначального черновика tasklist

- Отдельный read-only DSN не вводился (опционально по ADR позже).
