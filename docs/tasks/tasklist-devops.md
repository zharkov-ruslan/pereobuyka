# Tasklist: DevOps и delivery «Переобуйка»

## Область: devops

Контейнеризация монорепозитория, локальный полный стек через Docker Compose, публикация образов в GitHub Container Registry (GHCR). Полноценный CI/CD (тесты, lint, деплой, мониторинг) — **следующие итерации** после iter-dev-01–02.

**Текущее состояние:** **iter-dev-01** ✅ done (локальный полный стек). **iter-dev-02** ✅ done (GHCR). CI pytest/lint — позже.

**Опорные документы:** [`docs/plan.md`](../plan.md) · [`docs/architecture.md`](../architecture.md) · [`docs/vision.md`](../vision.md) · [`docs/onboarding.md`](../onboarding.md) · [`README.md`](../../README.md)

### Статус области ([`docs/plan.md`](../plan.md))

**Этап 6 — «Production-ready и delivery»** — 🔄 in-progress (iter-dev-01 ✅, iter-dev-02 ✅; CI/deploy — позже).

---

## Рекомендация по skills

| Задача | Skill | Путь |
|--------|-------|------|
| Dockerfile, compose, ревью конфигурации | **docker-expert** | [`.agents/skills/docker-expert/SKILL.md`](../../.agents/skills/docker-expert/SKILL.md) |
| Workflow сборки и push в registry | **github-actions-templates** | [`.agents/skills/github-actions-templates/SKILL.md`](../../.agents/skills/github-actions-templates/SKILL.md) |
| Проверка workflow run, packages в GHCR | **gh-cli** | [`.agents/skills/gh-cli/SKILL.md`](../../.agents/skills/gh-cli/SKILL.md) |

---

## Связь с `docs/plan.md`

| Этап в [`docs/plan.md`](../plan.md) | Роль этого tasklist |
|-------------------------------------|---------------------|
| **6** — Production-ready и delivery | iter-dev-01 (локальный полный стек), iter-dev-02 (GHCR); CI тестов/lint, prod-deploy, мониторинг — позже |

---

## Легенда статусов

| Иконка | Статус | Значение |
|--------|--------|----------|
| ⚪ | `planned` | Запланировано, работа не начата |
| 🔄 | `in-progress` | Итерация в работе |
| 🔴 | `blocked` | Заблокировано внешней зависимостью |
| ✅ | `done` | Итерация завершена и верифицирована |

---

## Сводная таблица итераций

| ID | Итерация | Статус | Зависимости | Ключевые артефакты |
|----|----------|--------|-------------|-------------------|
| [iter-dev-01](#iter-dev-01-локальный-полный-стек) | Локальный полный стек | ✅ done | этапы 1–5 (код сервисов) | `devops/`, `docker-compose.yml`, `Makefile` compose-*, [`docs/tech/docker-compose-local.md`](../tech/docker-compose-local.md) |
| [iter-dev-02](#iter-dev-02-сборка-образов-в-ghcr) | Сборка образов в GHCR | ✅ done | iter-dev-01 | `.github/workflows/docker-publish.yml`, `docker-compose.registry.yml` |

Папки реализации (создаются по мере работ):

```
docs/tasks/impl/devops/
├── iteration-01-local-stack/
│   ├── plan.md
│   ├── summary.md
│   └── tasks/
│       ├── task-01-devops-layout/
│       ├── task-02-dockerfiles/
│       ├── task-03-compose/
│       ├── task-04-makefile/
│       ├── task-05-docker-review/
│       ├── task-06-compose-guide/
│       └── task-07-docs-sync/
└── iteration-02-ghcr-pipeline/
    ├── plan.md
    ├── summary.md
    └── tasks/
        ├── task-01-gh-actions/
        ├── task-02-compose-registry/
        └── task-03-registry-smoke/
```

---

## Итерации

### iter-dev-01 — Локальный полный стек

**Шаг дорожной карты:** 6 (подготовка delivery)

### Цель

Один воспроизводимый способ поднять **postgres + backend + bot + web** через корневой `docker compose up` без ручного `make backend-run` / `bot-run` / `web-dev`.

### Ценность

Команда и агенты получают единую точку входа для smoke всей системы; задел под registry-образы и будущий деплой.

### Состав работ

- [x] **task-01 — Структура `devops/`:** каталоги `devops/backend/`, `devops/bot/`, `devops/web/`, `devops/README.md`; обоснование layout в [plan.md](impl/devops/iteration-01-local-stack/tasks/task-01-devops-layout/plan.md)
- [x] **task-02 — Dockerfile и .dockerignore:** multi-stage для backend/bot (uv, Python 3.12) и web (pnpm, Next.js output/standalone); минимальные образы, non-root где уместно
- [x] **task-03 — Корневой `docker-compose.yml`:** сервисы `postgres`, `backend`, `bot`, `web`; `depends_on` + healthcheck; backend на PostgreSQL; entrypoint с `alembic upgrade head` + uvicorn; env через `.env.docker.example`; порты 5432, 8000, 3000
- [x] **task-04 — Makefile:** цели `compose-up`, `compose-down`, `compose-ps`, `compose-logs`, `compose-logs-<service>`, `compose-health`; адаптация или алиасы для `db-*`
- [x] **task-05 — Ревью docker-expert:** прочитать skill целиком; чеклист (слои, .dockerignore, секреты, healthchecks, pin базовых image); правки и выводы в summary
- [x] **task-06 — Инструкция:** [`docs/tech/docker-compose-local.md`](../tech/docker-compose-local.md) — prerequisites, env, команды, типовые сбои (Windows, кириллица в пути)
- [x] **task-07 — Синхронизация docs:** [`README.md`](../../README.md), [`docs/onboarding.md`](../onboarding.md), [`docs/architecture.md`](../architecture.md), [`docs/plan.md`](../plan.md)

### Целевая структура артефактов

```
devops/
├── README.md
├── backend/
│   ├── Dockerfile
│   └── .dockerignore
├── bot/
│   ├── Dockerfile
│   └── .dockerignore
└── web/
    ├── Dockerfile
    └── .dockerignore
docker-compose.yml              # полный стек (build → devops/*/Dockerfile)
.env.docker.example             # шаблон env для compose
docs/tech/docker-compose-local.md
```

| Решение | Обоснование |
|---------|-------------|
| `devops/<service>/` | Infra отдельно от прикладного кода; единый паттерн для трёх сервисов |
| Dockerfile в `devops/`, build context — каталог сервиса | Один «шлюз» для контейнеризации; не раздувает `backend/`, `bot/`, `web/` |
| Один корневой `docker-compose.yml` | Заменяет текущий compose «только БД» — полный стек в одном файле |
| `COMPOSE_PROJECT_NAME=pereobuyka` | Уже в Makefile; нужен на Windows при пути с кириллицей |

### Артефакты

- `devops/` — Dockerfile и .dockerignore по сервисам
- [`docker-compose.yml`](../../docker-compose.yml) — полный стек
- [`.env.docker.example`](../../.env.docker.example) — шаблон переменных
- [`Makefile`](../../Makefile) — секция `compose-*`
- [`docs/tech/docker-compose-local.md`](../tech/docker-compose-local.md)

### Документы

- [plan.md](impl/devops/iteration-01-local-stack/plan.md)
- [summary.md](impl/devops/iteration-01-local-stack/summary.md)

| Задача | План | Summary |
|--------|------|---------|
| task-01 devops-layout | [plan](impl/devops/iteration-01-local-stack/tasks/task-01-devops-layout/plan.md) | [summary](impl/devops/iteration-01-local-stack/tasks/task-01-devops-layout/summary.md) |
| task-02 dockerfiles | [plan](impl/devops/iteration-01-local-stack/tasks/task-02-dockerfiles/plan.md) | [summary](impl/devops/iteration-01-local-stack/tasks/task-02-dockerfiles/summary.md) |
| task-03 compose | [plan](impl/devops/iteration-01-local-stack/tasks/task-03-compose/plan.md) | [summary](impl/devops/iteration-01-local-stack/tasks/task-03-compose/summary.md) |
| task-04 makefile | [plan](impl/devops/iteration-01-local-stack/tasks/task-04-makefile/plan.md) | [summary](impl/devops/iteration-01-local-stack/tasks/task-04-makefile/summary.md) |
| task-05 docker-review | [plan](impl/devops/iteration-01-local-stack/tasks/task-05-docker-review/plan.md) | [summary](impl/devops/iteration-01-local-stack/tasks/task-05-docker-review/summary.md) |
| task-06 compose-guide | [plan](impl/devops/iteration-01-local-stack/tasks/task-06-compose-guide/plan.md) | [summary](impl/devops/iteration-01-local-stack/tasks/task-06-compose-guide/summary.md) |
| task-07 docs-sync | [plan](impl/devops/iteration-01-local-stack/tasks/task-07-docs-sync/plan.md) | [summary](impl/devops/iteration-01-local-stack/tasks/task-07-docs-sync/summary.md) |

**Definition of Done — агент**

- `docker compose up -d --build` из корня поднимает все сервисы; `GET http://127.0.0.1:8000/health` → 200; web доступен на `:3000`
- Backend в compose использует PostgreSQL (не SQLite); seed доступен (make-цель или documented one-shot)
- Makefile: up / down / ps / logs / logs по сервису / health работают
- Ревью **docker-expert** задокументировано в task-05 summary (замечания + исправления)
- Инструкция и README / onboarding / architecture согласованы

**Definition of Done — пользователь**

- По [`docs/tech/docker-compose-local.md`](../tech/docker-compose-local.md) с нуля поднять стек на машине с Docker
- Открыть web, убедиться что API отвечает; при заданном `TELEGRAM_BOT_TOKEN` — bot без crash-loop в `docker compose ps`
- `make compose-logs-backend` показывает осмысленные логи

---

### iter-dev-02 — Сборка образов в GHCR

**Шаг дорожной карты:** 6 (подготовка delivery)

### Цель

GitHub Actions собирает и публикует образы **backend**, **bot**, **web** в GitHub Container Registry; локально стек поднимается на опубликованных образах без `build`.

### Ценность

Воспроизводимые артефакты доставки; задел под deploy без ручной сборки на сервере.

**Scope (не входит):** деплой на VPS/K8s, CI pytest/eslint, автодеплой, мониторинг — следующие итерации.

### Состав работ

- [x] **task-01 — Workflow GH Actions:** `.github/workflows/docker-publish.yml` — matrix или отдельные job для backend/bot/web; `docker/build-push-action`; push в `ghcr.io/<owner>/pereobuyka-<service>`; теги `latest` + `sha`; `permissions: packages: write`; триггеры push master + `workflow_dispatch`; skill **github-actions-templates**
- [x] **task-02 — Compose для registry:** `docker-compose.registry.yml` — `image:` вместо `build:`; переменные `REGISTRY`, `IMAGE_TAG`; те же depends_on / env / health, что в local
- [x] **task-03 — Smoke на registry:** документировать pull/run; проверка health + web; зафиксировать команды и image names в summary

### Артефакты

- [`.github/workflows/docker-publish.yml`](../../.github/workflows/docker-publish.yml)
- [`docker-compose.registry.yml`](../../docker-compose.registry.yml)
- Раздел в [`docs/tech/docker-compose-local.md`](../tech/docker-compose-local.md) или отдельный подраздел про registry

### Документы

- [plan.md](impl/devops/iteration-02-ghcr-pipeline/plan.md)
- [summary.md](impl/devops/iteration-02-ghcr-pipeline/summary.md)

| Задача | План | Summary |
|--------|------|---------|
| task-01 gh-actions | [plan](impl/devops/iteration-02-ghcr-pipeline/tasks/task-01-gh-actions/plan.md) | [summary](impl/devops/iteration-02-ghcr-pipeline/tasks/task-01-gh-actions/summary.md) |
| task-02 compose-registry | [plan](impl/devops/iteration-02-ghcr-pipeline/tasks/task-02-compose-registry/plan.md) | [summary](impl/devops/iteration-02-ghcr-pipeline/tasks/task-02-compose-registry/summary.md) |
| task-03 registry-smoke | [plan](impl/devops/iteration-02-ghcr-pipeline/tasks/task-03-registry-smoke/plan.md) | [summary](impl/devops/iteration-02-ghcr-pipeline/tasks/task-03-registry-smoke/summary.md) |

**Definition of Done — агент**

- Workflow валиден (review по **github-actions-templates**); образы собираются при push или `workflow_dispatch`
- `docker compose -f docker-compose.yml -f docker-compose.registry.yml` поднимает стек без локального `build`
- Summary содержит пример команд pull/run и ожидаемые имена образов

**Definition of Done — пользователь**

- После успешного run workflow локально поднять стек через registry compose; smoke: health + web
- В GHCR видны три package с актуальными тегами (`latest`, commit sha)

---

## Дальнейшие итерации (вне scope iter-dev-01–02)

- CI: pytest, ruff, eslint, `pnpm build` на PR
- Deploy на production-среду, секреты, мониторинг, откаты
- Webhook для бота вместо long polling в prod

Идеи без итерации — [`docs/backlog.md`](../backlog.md).
