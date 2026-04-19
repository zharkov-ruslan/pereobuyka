# Переобуйка — Telegram-бот

Пакет `pereobuyka`: опрос Telegram, HTTP-клиент к [backend](../backend/README.md).

## Быстрый старт

```bash
cd bot
uv sync
copy .env.example .env   # Windows: заполнить переменные
uv run python -m pereobuyka.main
```

Из корня репозитория: `make bot-install`, `make bot-run`.

## Качество кода

Линтер и форматирование — **ruff**, статическая типизация — **mypy** (см. `pyproject.toml`, ориентир — `.agents/skills/python-code-style`).

```bash
cd bot
uv run --group dev ruff check src/ && uv run --group dev ruff format src/
uv run --group dev mypy src/pereobuyka
```

Из корня: `make bot-lint` (ruff + mypy).

Общее описание проекта: [README в корне](../README.md).
