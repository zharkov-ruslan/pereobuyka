# Tasklist: DevOps и delivery «Переобуйка»

## Область: devops / production-ready

Соответствует **этапу 6** в [`docs/plan.md`](../plan.md): CI/CD, полный compose всех сервисов, мониторинг, воспроизводимый деплой.

**Текущее состояние:** область **запланирована**, отдельные итерации с `plan.md` / `summary.md` пока не ведутся. Локально уже есть [`docker-compose.yml`](../../docker-compose.yml) только для PostgreSQL и цели `db-*` в корневом [`Makefile`](../../Makefile); CI (`.github/workflows/`) в репозитории пока нет.

**Опорные документы:** [`docs/plan.md`](../plan.md) · [`docs/backlog.md`](../backlog.md) · [`README.md`](../../README.md)

### Что делать дальше

- Завести итерации в `docs/tasks/impl/devops/` по мере старта работ (шаблон процесса — [`.cursor/rules/workflow.mdc`](../../.cursor/rules/workflow.mdc)).
- Идеи и отложенные задачи без итерации — в [`docs/backlog.md`](../backlog.md).
