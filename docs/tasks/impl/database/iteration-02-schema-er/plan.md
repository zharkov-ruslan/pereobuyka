# iter-db-02 — План

## Цель

Привести логическую модель в соответствие с [user_scenarios.md](../../../../tech/user_scenarios.md) и с контрактом API ([openapi.yaml](../../../../tech/api/openapi.yaml)); описать целевую **физическую** схему PostgreSQL (таблицы, типы, ограничения, индексы); добавить ER-диаграмму; зафиксировать ревью по правилам postgresql-table-design.

## Шаги

1. Заменить объединённую сущность «Schedule» на **ScheduleRule** и **ScheduleException** (как в OpenAPI).
2. Уточнить связи M:N записей и визитов с услугами через строки с `quantity` (`ServiceLineItem`).
3. Добавить разделы «Физическая модель» и «ER-диаграмма (физическая)» в [data-model.md](../../../../tech/data-model.md).
4. Сверить идентификаторы и поля с OpenAPI; вынести расхождения в summary.
5. Обновить [plan.md](../../../../plan.md), [tasklist-database.md](../../../tasklist-database.md), добавить summary итерации.
