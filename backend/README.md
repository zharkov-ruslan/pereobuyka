# Переобуйка — Backend

FastAPI-сервис: бизнес-логика записи, расписания, прайса и лояльности для шиномонтажного сервиса «Переобуйка».

## Требования

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) — пакетный менеджер

## Быстрый старт

### 1. Установка зависимостей

```bash
make backend-install
```

Либо вручную из папки `backend/`:

```bash
cd backend
uv sync
```

### 2. Настройка окружения

Скопировать `.env.example` в `.env` и заполнить переменные:

```powershell
Copy-Item backend/.env.example backend/.env
```

Для локальной разработки достаточно оставить `DATABASE_URL` со значением по умолчанию (`sqlite+aiosqlite:///./dev.db`) — SQLite создастся автоматически.

Переменные окружения имеют приоритет над `.env`.

### 3. Запуск сервера

```bash
make backend-run
```

Сервер стартует на `http://localhost:8000`.

- **Health check:** `http://localhost:8000/health`
- **OpenAPI (Swagger UI):** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Остановить сервер:

```bash
make backend-stop
```

## Переменные окружения

Все переменные описаны в `backend/.env.example`.

| Переменная | Обязательна | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `DATABASE_URL` | нет | `sqlite+aiosqlite:///./dev.db` | URL подключения к БД. PostgreSQL в production, SQLite для разработки |
| `LOG_LEVEL` | нет | `INFO` | Уровень логирования: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `OPENROUTER_API_KEY` | нет | *(пусто)* | API-ключ OpenRouter — нужен только для LLM-консультации (этап 3) |
| `OPENROUTER_MODEL` | нет | `openai/gpt-4o-mini` | Идентификатор модели OpenRouter |
| `OPENROUTER_BASE_URL` | нет | `https://openrouter.ai/api/v1` | Base URL OpenRouter API |

> Не публикуй `.env` в репозиторий — он добавлен в `.gitignore`.

## Команды Make

| Команда | Описание |
|---------|----------|
| `make backend-install` | Установить зависимости (`uv sync`) |
| `make backend-run` | Запустить сервер с `--reload` на порту 8000 |
| `make backend-stop` | Остановить процесс на порту 8000 (Windows/PowerShell) |
| `make backend-test` | Запустить тесты (`pytest`) |
| `make backend-lint` | Проверить стиль кода (`ruff check` + `ruff format --check`) |

## Тесты и линтер

```bash
make backend-test   # pytest — должно быть: N passed
make backend-lint   # ruff — должно быть: All checks passed
```

## Структура пакета

```
backend/
├── src/pereobuyka/
│   ├── api/v1/          # Роутеры и Pydantic-схемы
│   ├── services/        # Бизнес-логика (слоты, записи)
│   ├── storage/         # Хранилище (in-memory; заменяется на DB в следующих итерациях)
│   ├── models/          # Доменные модели
│   ├── config.py        # Настройки из env
│   ├── main.py          # FastAPI app, lifespan, обработчики ошибок
│   └── utils.py         # Вспомогательные функции
└── tests/               # pytest-тесты API
```

## API-контракт

Полная спецификация: [`docs/tech/api/openapi.yaml`](../docs/tech/api/openapi.yaml)  
Описание контрактов: [`docs/tech/api/api-contracts.md`](../docs/tech/api/api-contracts.md)  
Модель ошибок: [`docs/tech/api/errors.md`](../docs/tech/api/errors.md)
