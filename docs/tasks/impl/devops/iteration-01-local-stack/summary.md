# iter-dev-01: summary

## Реализовано

- `devops/` с Dockerfile и .dockerignore для backend, bot, web
- `backend/docker-entrypoint.sh` — миграции Alembic перед uvicorn
- `docker-compose.yml` — postgres, backend, bot, web
- `.env.docker.example`, цели `compose-*` в Makefile
- `web/next.config.ts` — `output: "standalone"` для контейнера
- [`docs/tech/docker-compose-local.md`](../../../tech/docker-compose-local.md)
- Обновлены README, onboarding, architecture

## Отклонения

- `.dockerignore` продублирован в `backend/`, `bot/`, `web/` (Docker читает ignore только из build context)
- `!README.md` в `.dockerignore` — нужен для `uv_build` у bot
- pnpm **10.33.2** в Dockerfile и `packageManager` (pnpm 11 → `ERR_PNPM_IGNORED_BUILDS`)
- `docker-entrypoint.sh`: strip CRLF в Dockerfile (Windows)
- `make compose-health` — через `curl.exe`

## Ревью docker-expert (task-05)

| Проверка | Статус |
|----------|--------|
| Multi-stage builds (backend, bot, web) | ✅ |
| Non-root USER в runtime-образах | ✅ |
| HEALTHCHECK backend/web | ✅ |
| Pin базовых образов (python:3.12-slim-bookworm, node:22-bookworm-slim, postgres:16-alpine) | ✅ |
| .dockerignore (venv, .env, tests) | ✅ |
| Секреты только через env_file, не COPY | ✅ |
| depends_on + condition: service_healthy | ✅ |
| uv/pnpm cache mounts в build | ✅ |

## Верификация (2026-06-02)

- `docker compose up -d --wait` — postgres, backend, bot, web **healthy**
- `compose-seed` — OK
- `GET /health` → `{"status":"ok"}`
- `GET :3000` → 200
- bot — `Start polling` без restart loop
