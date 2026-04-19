# iter-07 — Bot via API: итоги реализации

## Что реализовано

### Backend (расширение auth)
- `backend/src/pereobuyka/config.py` — добавлено поле `bot_secret: str = ""`
- `backend/src/pereobuyka/api/v1/deps.py` — поддержка авторизации бота через `BOT_SECRET`:
  - Если `Authorization: Bearer <BOT_SECRET>` совпадает и секрет задан — user UUID вычисляется как `uuid5(NAMESPACE_URL, "telegram:<id>")` из заголовка `X-Telegram-User-Id`
  - При пустом `BOT_SECRET` — поведение без изменений (401)
- `backend/.env.example` — добавлена переменная `BOT_SECRET=`

### HTTP-клиент (`bot/src/pereobuyka/client/`)
- `BackendClient` — инициализируется при запуске бота с общим `httpx.AsyncClient`
  - `get_services()` — GET /api/v1/services
  - `for_user(telegram_id)` → `_UserClient` — клиент для запросов с авторизацией
- `_UserClient`
  - `get_slots(date_from, date_to, service_ids)` — GET /api/v1/slots
  - `create_appointment(starts_at, service_items)` — POST /api/v1/appointments
- `BackendError`, `BackendUnavailableError` — типизированные исключения

### Handlers
- `bot/src/pereobuyka/bot/handlers/services.py` — `/services`: список услуг из backend
- `bot/src/pereobuyka/bot/handlers/book.py` — `/book`: FSM-запись
  - Состояния: `choosing_service` → `entering_date` → `choosing_slot`
  - Inline-клавиатуры на каждом шаге
  - CallbackData: `ServiceCb`, `DateCb`, `SlotCb`, `CancelCb`
  - 409 при конфликте → предложить другой слот
  - Защита от устаревших callback'ов
- `bot/src/pereobuyka/bot/handlers/start.py` — обновлён текст приветствия со списком команд

### Инфраструктура
- Проект бота вынесен в каталог `bot/` (рядом с `backend/`): `bot/pyproject.toml`, `bot/uv.lock`, `bot/.venv` при локальной установке.
- `bot/src/pereobuyka/config.py` — снят merge-конфликт; добавлены `backend_base_url`, `bot_secret`
- `bot/src/pereobuyka/main.py` — `BackendClient` инициализируется при старте, закрывается в `finally`; FSM через `MemoryStorage`
- `bot/src/pereobuyka/bot/router.py` — включает все три handler'а
- `bot/pyproject.toml` — зависимость `httpx>=0.27.0`, dev-группа `ruff`
- `Makefile` — добавлены `bot-install`, `bot-run`, `bot-lint` (`install`/`run` → алиасы на бота)
- `bot/.env.example` — `BACKEND_BASE_URL`, `BOT_SECRET`; в корне `.env.example` — указатель на шаблон бота

## Отклонения от плана

По сравнению с первоначальным планом iter-07: исходники бота лежат в `bot/src/pereobuyka/`, а не в корневом `src/` — отдельная задача по выравниванию структуры репозитория. Остальное соответствует плану.

## Принятые решения

- **Один `httpx.AsyncClient` на весь жизненный цикл бота** — более эффективно, чем создание per-request; закрывается в `finally` в `_run()`.
- **`_UserClient` как легковесная обёртка** — не копирует данные, ссылается на общий `http`; позволяет избежать хранения `telegram_user_id` в базовом клиенте.
- **`MemoryStorage` для FSM** — достаточно для MVP; при рестарте бота пользователи начинают сессию заново (ожидаемо).
- **`BOT_SECRET` без полноценного JWT** — явно помечено как временная мера до `auth-tasklist`; пустой секрет → старый поток 401 (тесты не затронуты).

## Проверка

| Проверка | Результат |
|----------|-----------|
| `make backend-test` | 15 passed |
| `make backend-lint` | All checks passed |
| `make bot-lint` | ruff в `bot/` |
| Импорты бота | OK (`cd bot && uv run python -c "import pereobuyka.main"`) |
