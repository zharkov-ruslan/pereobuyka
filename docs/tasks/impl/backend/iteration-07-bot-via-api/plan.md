# iter-be-07 — Bot via API: план реализации

## Цель

Рефакторинг Telegram-бота: тонкие handlers без бизнес-логики, HTTP-клиент к backend API для сценариев слотов и записи.

## Архитектура

```
bot/src/pereobuyka/
├── client/
│   ├── __init__.py
│   └── backend.py          # BackendClient (httpx)
├── bot/
│   ├── handlers/
│   │   ├── start.py        # обновлён: список команд
│   │   ├── services.py     # /services → GET /api/v1/services
│   │   └── book.py         # /book → FSM: услуга → дата → слот → запись
│   ├── router.py           # включает все handlers
│   └── __init__.py
├── config.py               # + backend_base_url, bot_secret
└── main.py                 # app_config передаётся через start_polling
```

## Аутентификация бота

Backend `deps.py` расширяется поддержкой `bot_secret`:
- Переменная `BOT_SECRET` в backend `.env`
- Если `Authorization: Bearer <BOT_SECRET>` и секрет совпадает → user UUID вычисляется через `uuid5(NS, "telegram:<id>")` из заголовка `X-Telegram-User-Id`
- Пустой `BOT_SECRET` = фича выключена (существующие тесты с `auth_override` не затрагиваются)

## Сценарии бота

### `/services`
1. `GET /api/v1/services`
2. Форматированный список услуг (название, цена, длительность)

### `/book` (FSM)
| Шаг | Состояние | Действие |
|-----|-----------|----------|
| 1 | `choosing_service` | inline-клавиатура с услугами из backend |
| 2 | `entering_date` | inline-клавиатура: сегодня / завтра / послезавтра |
| 3 | `choosing_slot` | inline-клавиатура со слотами из `GET /api/v1/slots` |
| 4 | — | `POST /api/v1/appointments` → подтверждение |

### Обработка ошибок
- Backend недоступен (`ConnectError`, `TimeoutException`) → "Сервис временно недоступен"
- 409 при бронировании → "Время занято, выберите другое"
- 422 → "Некорректный запрос"

## Изменяемые файлы

| Файл | Изменение |
|------|-----------|
| `backend/src/pereobuyka/config.py` | `+ bot_secret: str = ""` |
| `backend/src/pereobuyka/api/v1/deps.py` | Поддержка bot_secret + X-Telegram-User-Id |
| `backend/.env.example` | `+ BOT_SECRET=` |
| `bot/src/pereobuyka/config.py` | Снять конфликт, добавить поля |
| `bot/pyproject.toml` | `+ httpx` |
| `bot/src/pereobuyka/client/backend.py` | Новый файл |
| `bot/src/pereobuyka/client/__init__.py` | Новый файл |
| `bot/src/pereobuyka/bot/handlers/services.py` | Новый файл |
| `bot/src/pereobuyka/bot/handlers/book.py` | Новый файл |
| `bot/src/pereobuyka/bot/handlers/start.py` | Обновить текст |
| `bot/src/pereobuyka/bot/router.py` | Включить новые handlers |
| `bot/src/pereobuyka/main.py` | DI через start_polling kwargs |
| `bot/.env.example` | `+ BACKEND_BASE_URL`, `+ BOT_SECRET` |
| `Makefile` | `+ bot-install`, `+ bot-run`, `+ bot-lint` |

## Зависимости

- `httpx` добавляется в `bot/pyproject.toml`
- Все изменения backend обратно совместимы: существующие тесты (`auth_override`) продолжают работать без изменений

## Definition of Done

- [ ] `make backend-test`: 12 passed (регрессий нет)
- [ ] `make backend-lint`: OK
- [ ] Бот стартует: `make bot-run`
- [ ] В Telegram работают `/services`, `/book` (happy path)
- [ ] При недоступном backend — дружелюбное сообщение
