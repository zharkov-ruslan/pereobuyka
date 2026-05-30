# Переобуйка — Telegram-бот

Пакет `pereobuyka`: опрос Telegram, HTTP-клиент к [backend](../backend/README.md).

## Быстрый старт

```bash
cd bot
uv sync
copy .env.example .env   # Windows: заполнить переменные
uv run python run_bot.py
```

Точка входа **`run_bot.py`** (в корневом `make bot-run` то же самое) добавляет `src/` в `PYTHONPATH` и вызывает `pereobuyka.main` — удобно без editable-install пакета. Альтернатива после настройки окружения: `uv run python -m pereobuyka.main` (если пакет установлен как модуль).

Из корня репозитория: `make bot-install`, `make bot-run`.

LLM-консультация: команда **`/ask`** (вызов `POST /api/v1/consultation/messages` на backend). Ключи OpenRouter настраиваются в `backend/.env`.

## Качество кода

Линтер и форматирование — **ruff**, статическая типизация — **mypy** (см. `pyproject.toml`, ориентир — `.agents/skills/python-code-style`).

```bash
cd bot
uv run --group dev ruff check src/ && uv run --group dev ruff format src/
uv run --group dev mypy src/pereobuyka
```

Из корня: `make bot-lint` (ruff + mypy).

Тесты:

```bash
cd bot
uv run --group dev pytest
```

Из корня: `make bot-test`.

Общее описание проекта: [README в корне](../README.md).
