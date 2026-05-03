# Переобуйка

Система записи в сервис шиномонтажа: **HTTP API** (ядро), **Telegram-бот** и веб-интерфейс.

| Проект | Каталог | Описание |
|--------|---------|----------|
| Backend | [`backend/`](backend/) | FastAPI, бизнес-логика, OpenAPI — см. [backend/README.md](backend/README.md) |
| Бот | [`bot/`](bot/) | aiogram, вызовы API — см. [bot/README.md](bot/README.md) |
| Web | [`web/`](web/) | Next.js App Router, shadcn/ui, клиентский и админский интерфейс |

## Документация

- [Дорожная карта](docs/plan.md)
- [Бэклог отложенных улучшений](docs/backlog.md)
- [Tasklists по областям](docs/tasks/) (`tasklist-*.md`)

## Требования

- Python **3.12+**
- Установленный **uv**
- Node.js **22+**
- Установленный **pnpm**
- Для локальной PostgreSQL (миграции, seed): **Docker** и **GNU Make** — см. раздел «База данных» в [backend/README.md](backend/README.md) (`make db-up`, `make db-migrate`, …).

## Где взять токены и ключи

### `TELEGRAM_BOT_TOKEN`

1) Открой Telegram и найди бота `@BotFather`.
2) Выполни команду `/newbot` и следуй инструкциям (название и username бота).
3) В ответ BotFather пришлёт токен — это и есть `TELEGRAM_BOT_TOKEN`.

### `OPENROUTER_API_KEY` (LLM-консультант)

Ключ настраивается **в backend** (`backend/.env`) — backend вызывает модель консультации и function-calling.

1) Как получить ключ: [openrouter.ai](https://openrouter.ai/) → **Sign in** → **API Keys** → **Create key**.
2) Скопируйте в **`OPENROUTER_API_KEY`**.

### `SPEECH_TO_TEXT_API_KEY` (распознавание голоса в боте)

Ключ для **speech-to-text** на сервере (OpenRouter STT или прямой OpenAI — см. `SPEECH_TO_TEXT_PROVIDER` в [ADR-005](docs/tech/adr/adr-005-speech-to-text.md)). Запросы идут на `…/audio/transcriptions`.

- Укажите в **`SPEECH_TO_TEXT_API_KEY`**. Для OpenRouter STT задайте также **`SPEECH_TO_TEXT_BASE_URL`** (как **`OPENROUTER_BASE_URL`**) и при необходимости **`SPEECH_TO_TEXT_MODEL`**.
- Рекомендуется отдельный API key от **`OPENROUTER_API_KEY`** или временно **продублируйте** то же значение.

Важно: не публикуй ключи и не коммить `.env` (он добавлен в `.gitignore`).

## Быстрый старт (Windows)

### Backend (нужен для `/book`, `/bonus`, … и для `/ask`)

```bash
make backend-install
make backend-run
```

Подробности: [backend/README.md](backend/README.md).

### Web

1) Установить зависимости:

```bash
make web-install
```

2) Создать `web/.env` из шаблона:

```powershell
Copy-Item web\.env.example web\.env
```

По умолчанию API ходит на **`http://127.0.0.1:8000`** (не `localhost`: на Windows иначе часто уходит в IPv6 `::1`, а uvicorn слушает только IPv4 `127.0.0.1` — получится «не подключается»).

3) Запустить backend и web:

```bash
make backend-run
make web-dev
```

Открыть `http://localhost:3000`. Клиентский MVP-вход использует `POST /api/v1/auth/web`; для админского режима можно временно вставить Bearer token администратора из локальной демо-среды.

Проверки web:

```bash
make web-lint
make web-build
```

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

- LLM-консультация включается, когда в `backend/.env` задан **`OPENROUTER_API_KEY`**; голос в боте — ещё **`SPEECH_TO_TEXT_API_KEY`** (и база/модель STT, см. ADR-005). В боте: `/ask`.
