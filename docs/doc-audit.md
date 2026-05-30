# Аудит документации: расхождения с кодом

Журнал известных несоответствий между документами и фактическим состоянием репозитория. При исправлении кода или docs — обновляйте эту таблицу.

| ID | Где | Проблема | Статус / действие |
|----|-----|----------|-------------------|
| DA-01 | [docs/plan.md](plan.md) этапы 4–5 | В обзоре этапов статус **⚪ planned**, тогда как [tasklist-frontend.md](tasks/tasklist-frontend.md) фиксирует **iter-fe-00 … iter-fe-09** как ✅ done | **Исправлено** в plan.md (статусы и блок «Факт реализации») |
| DA-02 | [docs/tasks/tasklist-frontend.md](tasks/tasklist-frontend.md) § «Статус области» | Текст «этапы 4–5 — ⚪ planned» противоречит таблице итераций | **Исправлено** в tasklist-frontend.md |
| DA-03 | [docs/plan.md](plan.md) этап 5 | В DoD указана «регистрация по телефону»; реализация MVP — `POST /api/v1/auth/web` по **`telegram_username`** ([auth.py](../backend/src/pereobuyka/api/v1/endpoints/auth.py)) | **Зафиксировано**: вход по телефону — будущее улучшение; см. [backlog.md](backlog.md) |
| DA-04 | [web/app/page.tsx](../web/app/page.tsx) | Текст «следующие итерации» на главной устарел относительно выполненных iter-fe-03+ | **Открыто**: правка UI-копирайта в отдельной задаче |
| DA-05 | CI | [CONTRIBUTING.md](../CONTRIBUTING.md) и plan этап 6: автопроверок в `.github/workflows/` нет | **Открыто**: ожидается tasklist devops |
| DA-06 | Web-тесты | `make web-test` / `pnpm test` — заглушка, реальных тестов UI нет | **Зафиксировано** в README, CONTRIBUTING, [web/README.md](../web/README.md) |
| DA-07 | SQLite vs PostgreSQL | В `.env.example` по умолчанию SQLite; полный функционал и pytest backend требуют PostgreSQL (Docker / Testcontainers) | **Документировано** в onboarding, backend/README |
| DA-08 | OpenAPI drift | Канонический [openapi.yaml](tech/api/openapi.yaml) может отставать от `/openapi.json` рантайма | **Риск**: при изменении API синхронизировать YAML и контракты |

Последнее обновление журнала: при создании onboarding/architecture (2026-05).
