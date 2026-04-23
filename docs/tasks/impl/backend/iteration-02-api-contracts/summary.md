# Итог: iter-02 — API contract (vision scenarios)

## Сделано

- Добавлен контракт **OpenAPI 3.0.3** в [`docs/tech/api/openapi.yaml`](../../../../tech/api/openapi.yaml) — пути под префиксом `/api/v1`, схемы сущностей и операций для клиента, администратора и консультации (LLM).
- Добавлено описание **ошибок** в [`docs/tech/api/errors.md`](../../../../tech/api/errors.md): обёртка `error`, HTTP-статусы, доменные коды.
- Индекс и навигация в [`docs/tech/api/README.md`](../../../../tech/api/README.md).
- Текстовая спецификация в [`docs/tech/api/api-contracts.md`](../../../../tech/api/api-contracts.md) — детализация эндпоинтов и соглашений поверх YAML (как в **iter-02** [`tasklist-backend.md`](../../../tasklist-backend.md)).

## Отклонения от черновых оформлений

- Идентификаторы в JSON — **строки UUID** (единый стиль для клиентов); в БД допускается int по data-model — согласование при реализации (iter-05).
- Расписание в API разделено на **`/admin/schedule/rules`** и **`/admin/schedule/exceptions`** для ясности контракта; обе сущности отражают поля `Schedule` из data-model.
- Уведомления Telegram вне тела публичного API (см. [`docs/tech/integrations.md`](../../../../tech/integrations.md)).

## Следующие шаги

- iter-03: каркас FastAPI; `docs/tech/api/openapi.yaml` — эталон контракта.
- iter-05: реализация endpoint’ов по волнам (базовый срез → полный срез этапа 1 для PostgreSQL; см. [`tasklist-backend.md`](../../../tasklist-backend.md) iter-05).
