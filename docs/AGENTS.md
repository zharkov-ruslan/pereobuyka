# Подсказки для AI-агентов и автоматизации

## С чего начать

1. [`README.md`](../README.md) — установка, env, `make`, smoke.
2. [`docs/onboarding.md`](onboarding.md) — пошаговый гайд для нового участника.
3. [`docs/architecture.md`](architecture.md) — схема компонентов.
4. [`docs/vision.md`](vision.md) — границы системы, стек, правила LLM и слоёв.
5. Задача по области — соответствующий [`docs/tasks/tasklist-*.md`](tasks/) и `docs/tasks/impl/.../plan.md` при наличии.

## Skills

В корне репозитория файл [`skills-lock.json`](../skills-lock.json) фиксирует **какие** навыки из внешних репозиториев подключены и их **хэши** (воспроизводимость окружения агента).

Каталог локальных копий/обёрток правил: [`.agents/skills/`](../.agents/skills/). Под тип задачи читайте `SKILL.md` целиком; при конфликте приоритет у [`docs/vision.md`](vision.md) и [`.cursor/rules/convensions.mdc`](../.cursor/rules/convensions.mdc).

## Правила Cursor

- [`.cursor/rules/workflow.mdc`](../.cursor/rules/workflow.mdc) — tasklist, plan/summary.
- [`.cursor/rules/convensions.mdc`](../.cursor/rules/convensions.mdc) — код-конвенции проекта.
