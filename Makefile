.PHONY: install run backend-install backend-run backend-stop backend-test backend-lint bot-install bot-run bot-stop bot-test bot-lint
.PHONY: web-install web-dev web-lint web-build web-test
.PHONY: db-up db-down db-reset db-migrate db-seed db-psql
.PHONY: compose-up compose-down compose-ps compose-logs compose-health compose-seed
.PHONY: compose-registry-up compose-registry-down compose-registry-pull
.PHONY: compose-logs-backend compose-logs-bot compose-logs-web compose-logs-postgres

# Удобные алиасы для бота (корневого pyproject больше нет)
install: bot-install

run: bot-run

# ── Backend ────────────────────────────────────────────────────────────────

backend-install:
	cd backend && uv sync

backend-run:
	cd backend && uv run uvicorn pereobuyka.main:app --reload --port 8000

backend-stop:
	-powershell -NoProfile -Command '$$pids = (Get-NetTCPConnection -LocalPort 8000 -EA SilentlyContinue).OwningProcess | Sort-Object -Unique; $$pids | ForEach-Object { Stop-Process -Id $$_ -Force -EA SilentlyContinue }'

backend-test:
	cd backend && uv run pytest

backend-lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

# ── Bot ────────────────────────────────────────────────────────────────────

bot-install:
	cd bot && uv sync

bot-run:
	cd bot && uv run python run_bot.py

bot-stop:
	-powershell -NoProfile -Command '$$ErrorActionPreference = "SilentlyContinue"; $$pids = Get-CimInstance Win32_Process | Where-Object { $$_.CommandLine -match "run_bot\.py|pereobuyka\.main|make bot-run" } | Select-Object -ExpandProperty ProcessId -Unique; foreach ($$procId in $$pids) { Stop-Process -Id $$procId -Force }; exit 0'

bot-test:
	cd bot && uv run --group dev pytest

bot-lint:
	cd bot && uv run --group dev ruff check src/ && uv run --group dev ruff format --check src/ && uv run --group dev mypy src/pereobuyka

# ── Web ──────────────────────────────────────────────────────────────────────

web-install:
	cd web && pnpm install

web-dev:
	cd web && pnpm dev

web-lint:
	cd web && pnpm lint

web-build:
	cd web && pnpm build

web-test:
	cd web && pnpm test

# ── Docker Compose (полный стек; iter-dev-01) ────────────────────────────────
# Фиксированное имя проекта: на Windows при пути с кириллицей иначе бывает «project name must not be empty».
export COMPOSE_PROJECT_NAME := pereobuyka
COMPOSE_REGISTRY := docker compose -f docker-compose.yml -f docker-compose.registry.yml

compose-up:
	docker compose up -d --build --wait

compose-down:
	docker compose down

compose-ps:
	docker compose ps

compose-logs:
	docker compose logs -f

compose-logs-backend:
	docker compose logs -f backend

compose-logs-bot:
	docker compose logs -f bot

compose-logs-web:
	docker compose logs -f web

compose-logs-postgres:
	docker compose logs -f postgres

compose-health:
	-curl.exe -sf http://127.0.0.1:8000/health

compose-seed:
	docker compose exec backend python -m pereobuyka.scripts.seed

# ── Docker Compose из GHCR (iter-dev-02) ─────────────────────────────────────

compose-registry-pull:
	$(COMPOSE_REGISTRY) pull

compose-registry-up: compose-registry-pull
	$(COMPOSE_REGISTRY) up -d --wait

compose-registry-down:
	$(COMPOSE_REGISTRY) down

# ── PostgreSQL (гибридная разработка: только БД в Docker) ───────────────────
# Для полного стека используйте compose-up; db-* — когда backend/bot/web на хосте.

db-up:
	docker compose up -d postgres --wait

db-down:
	docker compose stop postgres

# Удаляет volume `pgdata` вместе с данными; затем поднимает контейнер, миграции и seed.
db-reset:
	@echo "ВНИМАНИЕ: db-reset выполняет docker compose down -v (данные PostgreSQL будут удалены)."
	docker compose down -v
	docker compose up -d postgres --wait
	cd backend && uv run alembic upgrade head
	cd backend && uv run python -m pereobuyka.scripts.seed

db-migrate:
	cd backend && uv run alembic upgrade head

db-seed:
	cd backend && uv run python -m pereobuyka.scripts.seed

db-psql:
	docker compose exec postgres psql -U pereobuyka -d pereobuyka
