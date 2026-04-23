.PHONY: install run backend-install backend-run backend-stop backend-test backend-lint bot-install bot-run bot-lint
.PHONY: db-up db-down db-reset db-migrate db-seed db-psql

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
	cd bot && uv run python -m pereobuyka.main

bot-lint:
	cd bot && uv run --group dev ruff check src/ && uv run --group dev ruff format --check src/ && uv run --group dev mypy src/pereobuyka

# ── Локальная PostgreSQL (iter-db-04; см. backend/README.md) ───────────────
# Фиксированное имя проекта: на Windows при пути с кириллицей иначе бывает «project name must not be empty».
export COMPOSE_PROJECT_NAME := pereobuyka

db-up:
	docker compose up -d --wait

db-down:
	docker compose down

# Удаляет volume `pgdata` вместе с данными; затем поднимает контейнер, миграции и seed.
db-reset:
	@echo "ВНИМАНИЕ: db-reset выполняет docker compose down -v (данные PostgreSQL будут удалены)."
	docker compose down -v
	docker compose up -d --wait
	cd backend && uv run alembic upgrade head
	cd backend && uv run python -m pereobuyka.scripts.seed

db-migrate:
	cd backend && uv run alembic upgrade head

db-seed:
	cd backend && uv run python -m pereobuyka.scripts.seed

db-psql:
	docker compose exec postgres psql -U pereobuyka -d pereobuyka
