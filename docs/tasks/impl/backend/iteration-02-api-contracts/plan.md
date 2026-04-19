# План: iter-02 — API contract (vision scenarios)

## Цель

Зафиксировать полный HTTP-контракт `/api/v1` для сценариев клиента и администратора из [`docs/vision.md`](../../../../vision.md) §4, согласованный с [`docs/tech/data-model.md`](../../../../tech/data-model.md).

## Шаги

1. Описать общую модель ошибок и авторизации (Bearer JWT; публичные vs защищённые маршруты).
2. Собрать OpenAPI 3: ресурсы `User`, `Service`, `Schedule`, `Appointment`, `Visit`, бонусы, `FAQ`; клиентские и админские пути.
3. Отдельно задокументировать коды доменных ошибок и соответствие HTTP.
4. Связать с матрицей сценариев в [`docs/tasks/tasklist-backend.md`](../../../tasklist-backend.md) (iter-02).

## Артефакты

- [`docs/tech/api/openapi.yaml`](../../../../tech/api/openapi.yaml)
- [`docs/tech/api/errors.md`](../../../../tech/api/errors.md)
- [`docs/tech/api/README.md`](../../../../tech/api/README.md)
