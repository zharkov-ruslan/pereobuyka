# DevOps-артефакты «Переобуйка»

Контейнеризация вынесена из прикладных каталогов: Dockerfile и `.dockerignore` лежат здесь, **build context** — соседний сервис (`backend/`, `bot/`, `web/`).

| Каталог | Сервис | Контекст сборки |
|---------|--------|-----------------|
| [`backend/`](backend/) | FastAPI, Alembic | `backend/` |
| [`bot/`](bot/) | aiogram | `bot/` |
| [`web/`](web/) | Next.js | `web/` |

Корневой [`docker-compose.yml`](../docker-compose.yml) — полный локальный стек. Override для GHCR: [`docker-compose.registry.yml`](../docker-compose.registry.yml). Инструкция: [`docs/tech/docker-compose-local.md`](../docs/tech/docker-compose-local.md).

**Примечание:** Docker читает `.dockerignore` только из корня build context; файлы в `devops/*/` дублируются в `backend/.dockerignore`, `bot/.dockerignore`, `web/.dockerignore`.
