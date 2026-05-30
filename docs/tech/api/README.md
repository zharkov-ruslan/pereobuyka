# HTTP API «Переобуйка»

Каноническое описание контракта: **[openapi.yaml](openapi.yaml)** (OpenAPI 3.0.3).

- Префикс версии: **`/api/v1`**
- Формат данных: **JSON**, кодировка UTF-8
- Идентификаторы в JSON: **UUID в строках** (см. [summary iter-be-02](../../tasks/impl/backend/iteration-02-api-contracts/summary.md) при расхождении с числовыми id в [`tech/data-model.md`](../data-model.md))

Дополнительно:

- [Контракты (текст)](api-contracts.md) — полное описание эндпоинтов и соглашений
- [Ошибки](errors.md) — обёртка `error`, статусы, доменные коды
- Пользовательские сценарии: [`docs/vision.md`](../../vision.md) §4
- Модель данных: [`tech/data-model.md`](../data-model.md)

## Swagger UI и ReDoc

При запущенном backend (см. [`backend/README.md`](../../../backend/README.md)):

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

OpenAPI в репозитории ([`openapi.yaml`](openapi.yaml)) и схема в рантайме должны совпадать; при расхождениях приоритет у актуального ответа `/openapi.json` после деплоя, в разработке — синхронизировать YAML с кодом.
