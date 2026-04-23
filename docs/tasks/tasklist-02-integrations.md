# Tasklist: Integrations для этапа 2

## Область: integrations

Интеграционный слой между Telegram-ботом и backend API для сценариев этапа 2.

**Опорные документы:** [`docs/plan.md`](../plan.md) · [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml) · [`backend/src/pereobuyka/api/v1/endpoints/client.py`](../../backend/src/pereobuyka/api/v1/endpoints/client.py)

---

## Легенда статусов

| Иконка | Статус | Значение |
|--------|--------|----------|
| ✅ | `done` | Интеграция завершена |

---

## Этап 2 — Интеграции bot ↔ backend

**Статус:** ✅ done

**Состав работ**

- [x] Подтверждена реализация backend-эндпоинтов `/api/v1/me`, `/api/v1/me/appointments`, `/api/v1/me/visits`, `/api/v1/me/bonus-account`, `/api/v1/me/bonus-transactions`
- [x] Бот использует единый `httpx.AsyncClient` и тонкий API-клиент без бизнес-логики
- [x] Регистрация пользователя в БД выполняется через `POST /api/v1/auth/telegram` при первом входе
- [x] Команды бота для записей, бонусов и визитов подключены через контрактные client-endpoints
- [x] Ошибки API транслируются пользователю в понятные fallback-сообщения

**Артефакты**

- [`backend/src/pereobuyka/api/v1/endpoints/client.py`](../../backend/src/pereobuyka/api/v1/endpoints/client.py)
- [`backend/src/pereobuyka/api/v1/endpoints/auth.py`](../../backend/src/pereobuyka/api/v1/endpoints/auth.py)
- [`bot/src/pereobuyka/client/backend.py`](../../bot/src/pereobuyka/client/backend.py)
- [`bot/src/pereobuyka/bot/handlers/start.py`](../../bot/src/pereobuyka/bot/handlers/start.py)
- [`bot/src/pereobuyka/bot/handlers/appointments.py`](../../bot/src/pereobuyka/bot/handlers/appointments.py)
- [`bot/src/pereobuyka/bot/handlers/loyalty.py`](../../bot/src/pereobuyka/bot/handlers/loyalty.py)

**Открытые вопросы вне этапа 2**

- Полноценная пользовательская авторизация вместо временной схемы `BOT_SECRET` (отдельный auth-tasklist).
