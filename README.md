# Переобуйка

Telegram-бот-консультант для записи в сервис шиномонтажа.

## Требования
- Python **3.12+**
- Установленный **uv**

## Где взять токены и ключи

### `TELEGRAM_BOT_TOKEN`
1) Открой Telegram и найди бота `@BotFather`.
2) Выполни команду `/newbot` и следуй инструкциям (название и username бота).
3) В ответ BotFather пришлёт токен — это и есть `TELEGRAM_BOT_TOKEN`.

### `OPENROUTER_API_KEY`
1) Как попасть в кабинет OpenRouter:
   - Открой `https://openrouter.ai/`
   - Нажми **Sign in / Log in**
   - Войди через доступный способ (Google/GitHub/Email)
2) В кабинете открой раздел **API Keys**.
3) Нажми **Create key** (или аналогичную кнопку).
4) Скопируй ключ — это и есть `OPENROUTER_API_KEY`.

Важно: не публикуй ключи и не коммить `.env` (он добавлен в `.gitignore`).

## Быстрый старт (Windows)

1) Установить зависимости (создаст `.venv` в корне):

```bash
make install
```

2) Создать локальный файл `.env` (можно скопировать из `.env.example`):

```powershell
Copy-Item .env.example .env
```

Заполнить значения в `.env`.

Также можно задавать переменные окружения напрямую (они имеют приоритет над `.env`).

- **обязательные**
  - `TELEGRAM_BOT_TOKEN`
  - `OPENROUTER_API_KEY`
  - `OPENROUTER_MODEL`
- **опциональные**
  - `OPENROUTER_BASE_URL` (по умолчанию `https://openrouter.ai/api/v1`)
  - `LOG_LEVEL` (по умолчанию `INFO`)

Пример для PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:OPENROUTER_API_KEY="..."
$env:OPENROUTER_MODEL="openai/gpt-4o-mini"
```

3) Запустить бота:

```bash
make run
```

## Примечания
- На Этапе 0 LLM-консультации ещё не используются, но ключи OpenRouter уже валидируются на старте согласно техвидению.

