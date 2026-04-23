# Переобуйка

Система записи в сервис шиномонтажа: **HTTP API** (ядро) и **Telegram-бот** (клиент).

| Проект | Каталог | Описание |
|--------|---------|----------|
| Backend | [`backend/`](backend/) | FastAPI, бизнес-логика, OpenAPI — см. [backend/README.md](backend/README.md) |
| Бот | [`bot/`](bot/) | aiogram, вызовы API — см. [bot/README.md](bot/README.md) |

## Требования

- Python **3.12+**
- Установленный **uv**
- Для локальной PostgreSQL (миграции, seed): **Docker** и **GNU Make** — см. раздел «База данных» в [backend/README.md](backend/README.md) (`make db-up`, `make db-migrate`, …).

## Где взять токены и ключи

### `TELEGRAM_BOT_TOKEN`

1) Открой Telegram и найди бота `@BotFather`.
2) Выполни команду `/newbot` и следуй инструкциям (название и username бота).
3) В ответ BotFather пришлёт токен — это и есть `TELEGRAM_BOT_TOKEN`.

### `OPENROUTER_API_KEY` (для LLM-консультанта)

Ключ OpenRouter настраивается **в backend** (`backend/.env`, переменная `OPENROUTER_API_KEY`) — именно backend вызывает модель и выполняет function-calling к данным сервиса.

1) Как попасть в кабинет OpenRouter:
   - Открой `https://openrouter.ai/`
   - Нажми **Sign in / Log in**
   - Войди через доступный способ (Google/GitHub/Email)
2) В кабинете открой раздел **API Keys**.
3) Нажми **Create key** (или аналогичную кнопку).
4) Скопируй ключ — это и есть `OPENROUTER_API_KEY`.

Важно: не публикуй ключи и не коммить `.env` (он добавлен в `.gitignore`).

## Быстрый старт (Windows)

### Backend (нужен для `/book`, `/bonus`, … и для `/ask`)

```bash
make backend-install
make backend-run
```

Подробности: [backend/README.md](backend/README.md).

### Бот

1) Установить зависимости (создаст `bot/.venv`):

```bash
make bot-install
```

2) Создать `bot/.env` из шаблона:

```powershell
Copy-Item bot\.env.example bot\.env
```

Заполнить значения в `bot/.env` (обязательные: `TELEGRAM_BOT_TOKEN`; для API — `BACKEND_BASE_URL`, `BOT_SECRET` в паре с backend).

3) Запустить бота:

```bash
make bot-run
```

Эквивалент из каталога `bot/`: `uv sync`, затем `uv run python run_bot.py` (см. `Makefile`).

Тесты бота:

```bash
make bot-test
```

- **обязательные** (для старта бота): `TELEGRAM_BOT_TOKEN`
- **опциональные**: `LOG_LEVEL`, `BACKEND_BASE_URL`, `BOT_SECRET`

Пример для PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
```

## Примечания

- LLM-консультация включается, когда в `backend/.env` задан `OPENROUTER_API_KEY` и доступен backend; в боте это команда `/ask <вопрос>`.
