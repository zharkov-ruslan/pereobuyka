# iter-db-02 — Summary

## Результат

- Обновлён [docs/tech/data-model.md](../../../../tech/data-model.md): логическая модель с **ScheduleRule** и **ScheduleException** (как в OpenAPI), явные связи M:N через `appointment_services` и `visit_lines` с `quantity`, поле `confirmed_by_user_id` для визита, блок про singleton **loyalty_settings**.
- Добавлены разделы **Физическая модель (PostgreSQL)** с таблицами, типами (`TIMESTAMPTZ`, `NUMERIC`, `TEXT`, `UUID`), PK/FK, ключевыми CHECK и индексами на FK/запросы.
- Добавлена **физическая ER** (Mermaid) для основной графа FK; расписание и FAQ вынесены в примечание (нет прямых FK к записям).
- Таблица **Согласование с OpenAPI** и примечание про FAQ без путей в OpenAPI.

## Ревью postgresql-table-design (чеклист)

| Правило | Решение |
|---------|---------|
| PK для ссылочных таблиц | UUID + `gen_random_uuid()` |
| TIMESTAMPTZ для событий | `starts_at`, `ends_at`, `registered_at`, `confirmed_at`, `created_at` |
| Без `timestamp` без TZ | Соблюдено |
| Деньги — NUMERIC | `NUMERIC(12,2)`, не float |
| Строки — TEXT | Да |
| FK индексируются вручную | Указано в тексте для колонок FK |
| ENUM в БД vs TEXT+CHECK | Статусы/роли — TEXT + CHECK (гибче эволюция) |
| Уникальность `telegram_id` | Упомянут частичный UNIQUE для не-null |

## Открытые моменты

- Один сегмент на `weekday` vs несколько — зафиксировано как проектное решение (UNIQUE по `weekday` опционален).
- Семантика `amount` в `bonus_transactions` относительно типа `earn`/`spend`/`adjust` — уточнять в сервисном слое при реализации и при необходимости усилить CHECK.

## Согласование контрактов

Исправления OpenAPI **не требуются** для закрытия iter-db-02: расхождения старой объединённой сущности Schedule устранены в пользу схемы API. Отдельные эндпоинты FAQ при появлении — итерации backend/контрактов.
