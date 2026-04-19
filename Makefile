.PHONY: install run backend-install backend-run backend-stop backend-test backend-lint bot-install bot-run bot-lint

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
