# Участие в разработке «Переобуйка»

## Источники истины

- Продукт и стек: [`docs/vision.md`](docs/vision.md) · архитектура: [`docs/architecture.md`](docs/architecture.md)
- Онбординг: [`docs/onboarding.md`](docs/onboarding.md)
- Публичный API: [`docs/tech/api/openapi.yaml`](docs/tech/api/openapi.yaml) и [`docs/tech/api/api-contracts.md`](docs/tech/api/api-contracts.md)
- План итераций: [`docs/plan.md`](docs/plan.md), tasklists в [`docs/tasks/`](docs/tasks/)

## Локальная проверка перед PR

Из **корня** репозитория (после настройки `.env`, при необходимости Docker для backend-тестов):

| Область | Команды |
|---------|---------|
| Backend | `make backend-lint` · `make backend-test` |
| Bot | `make bot-lint` · `make bot-test` |
| Web | `make web-lint` · `make web-build` · `make web-test` |

`make web-test` сейчас — заглушка (реальных тестов `web/` нет); команда нужна, чтобы единообразно «прогонять» фронт в скриптах и CI.

## Процесс и документация итераций

Для задач в репозитории принят спек-подход: план и summary по итерациям и задачам — см. [`.cursor/rules/workflow.mdc`](.cursor/rules/workflow.mdc).

Код-стиль и слои backend/handlers: [`.cursor/rules/convensions.mdc`](.cursor/rules/convensions.mdc).

## Cursor и AI-агенты

Список подключаемых skills и их хэши: [`skills-lock.json`](skills-lock.json), каталог инструкций: [`.agents/skills/`](.agents/skills/). Краткая навигация для агентов: [`docs/AGENTS.md`](docs/AGENTS.md).

## Ветки и PR

Конкретные правила ветвления (имена веток, обязательные ревью) зафиксируйте по договорённости команды; минимум — осмысленные сообщения коммитов и прохождение линтеров/тестов из таблицы выше. CI в репозитории пока нет — проверки локальны или через внешний пайплайн по решению команды.
