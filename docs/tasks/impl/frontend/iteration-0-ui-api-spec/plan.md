# План выполнения iter-fe-00 — UI-требования и API для frontend

## Цель итерации

Зафиксировать до кодирования: функциональные требования по экранам веба, соответствие текущим контрактам [`docs/tech/api/api-contracts.md`](../../../../tech/api/api-contracts.md), пробелы и **черновик** новых эндпоинтов для [`iter-fe-01`](../../../tasklist-frontend.md#iter-fe-01-backend-api-миграции-seed-админ-в-бд).

## Ограничения

- Без каталога `web/` и без изменений в `backend/`.
- OpenAPI ([`openapi.yaml`](../../../../tech/api/openapi.yaml)) синхронизировать в **iter-fe-01** вместе с кодом.

## Шаги выполнения

1. **Сжать UI-требования** из [`docs/ui/ui-requirements.md`](../../../../ui/ui-requirements.md) в краткие per-экран блоки в [`summary.md`](summary.md).
2. **Построить матрицу** «экран → данные UI → существующие эндпоинты → пробел» по [`api-contracts.md`](../../../../tech/api/api-contracts.md).
3. **Черновик REST** для пробелов: ресурсно-ориентированные пути, роли `admin` / `client`, query/path — с опорой на `.agents/skills/api-design-principles/SKILL.md`.
4. **Вход в веб:** зафиксировать решение — отдельный контракт от `POST /api/v1/auth/telegram` (бот и тесты не ломаем); MVP — [`summary.md`](summary.md) § «Вход».
5. **Сверка с доменом:** перечислить изменения для [`docs/tech/data-model.md`](../../../../tech/data-model.md) в summary (новые поля/сущности для iter-fe-01).
6. **Артефакты:** этот файл (`plan.md`) + [`summary.md`](summary.md); при необходимости — точечные правки [`ui-requirements.md`](../../../../ui/ui-requirements.md) и блок «планируемые расширения» в [`api-contracts.md`](../../../../tech/api/api-contracts.md).

## Результат

Итог и проверка DoD — в [`summary.md`](summary.md).
