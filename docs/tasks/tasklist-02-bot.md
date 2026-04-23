# Tasklist: Telegram Bot (этап 2)

## Область: bot

Клиентский Telegram-канал на `aiogram` с тонкими handlers и вызовами backend API.

**Опорные документы:** [`docs/plan.md`](../plan.md) · [`docs/tech/api/openapi.yaml`](../tech/api/openapi.yaml) · [`docs/tasks/tasklist-backend.md`](tasklist-backend.md)

---

## Легенда статусов

| Иконка | Статус | Значение |
|--------|--------|----------|
| ✅ | `done` | Сценарий реализован и проверен |

---

## Этап 2 — Bot

**Статус:** ✅ done

**Состав работ**

- [x] `/start`: проверка пользователя через `GET /api/v1/me`, fallback-регистрация через `POST /api/v1/auth/telegram`
- [x] `/services`: каталог услуг и цен
- [x] `/book`: FSM-запись через слоты и `POST /api/v1/appointments`
- [x] `/appointments`: список записей и отмена через `PATCH /api/v1/me/appointments/{appointment_id}`
- [x] `/bonus`: бонусный счёт и последние бонусные операции
- [x] `/visits`: история последних подтверждённых визитов
- [x] Обработка ошибок backend без утечки технических деталей

**Артефакты**

- [`bot/src/pereobuyka/bot/handlers/start.py`](../../bot/src/pereobuyka/bot/handlers/start.py)
- [`bot/src/pereobuyka/bot/handlers/services.py`](../../bot/src/pereobuyka/bot/handlers/services.py)
- [`bot/src/pereobuyka/bot/handlers/book.py`](../../bot/src/pereobuyka/bot/handlers/book.py)
- [`bot/src/pereobuyka/bot/handlers/appointments.py`](../../bot/src/pereobuyka/bot/handlers/appointments.py)
- [`bot/src/pereobuyka/bot/handlers/loyalty.py`](../../bot/src/pereobuyka/bot/handlers/loyalty.py)
- [`bot/src/pereobuyka/client/backend.py`](../../bot/src/pereobuyka/client/backend.py)
- [`bot/src/pereobuyka/bot/router.py`](../../bot/src/pereobuyka/bot/router.py)

**Проверка**

- `make bot-lint`
