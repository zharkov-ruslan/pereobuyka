# Контракты HTTP API «Переобуйка»

Текстовое описание публичного REST API ядра. **Источник истины по полям и схемам** — [openapi.yaml](openapi.yaml) (OpenAPI 3.0.3). Ниже — **сводные таблицы** эндпоинтов по группам доступа, затем **детальные подразделы** с заголовками, параметрами и примерами запросов/ответов.

**См. также:** [errors.md](errors.md) · [README](README.md) · сценарии [vision.md](../../vision.md) §4 · модель [data-model.md](../data-model.md).

---

## Соглашения

| Тема | Описание | Правило |
|------|----------|---------|
| Базовый путь | Единый префикс версии для всех маршрутов API. | Префикс **`/api/v1`** |
| Формат | Кодировка и тип тел запросов и ответов. | **JSON**, UTF-8 |
| Идентификаторы | Как передаются id сущностей в теле и path. | Строки **UUID** в JSON |
| Время | Форматы даты-времени и времени суток в расписании. | `date-time` — ISO 8601; время суток в расписании — `HH:MM:SS` |
| День недели в правилах | Нумерация дня в шаблонах расписания. | `0` — понедельник … `6` — воскресенье |
| Ошибки | Структура ошибок и ссылка на перечень кодов. | Обёртка `error` — см. [errors.md](errors.md) |
| Заголовок Bearer | Способ передачи токена для защищённых маршрутов. | `Authorization: Bearer <JWT>` там, где нужна авторизация |
| Content-Type | Формат тела для запросов с JSON-телом (POST, PATCH). | `Content-Type: application/json` |

---

## Auth (без Bearer)

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| POST | `/api/v1/auth/telegram` | Вход / регистрация через Telegram (upsert пользователя), выдача JWT. | 200 / 201 |

<span id="post-auth-telegram"></span>

### POST `/api/v1/auth/telegram`

**Описание:** Вход / регистрация через Telegram (upsert пользователя), выдача JWT.

Сервер определяет факт создания по наличию записи с `telegram_id`:
- `200` — пользователь уже существовал, выполнен вход.
- `201` — пользователь создан впервые.

Тело ответа идентично в обоих случаях.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Content-Type` | `application/json` | да |

**Параметры:** —

**Запрос:** `POST /api/v1/auth/telegram` с телом:

```json
{
  "telegram_id": 123456789,
  "name": "Иван",
  "phone": "+79001234567"
}
```

**Ответ `200` (существующий пользователь) / `201` (новый пользователь):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Иван",
    "phone": "+79001234567",
    "role": "client",
    "telegram_id": 123456789,
    "registered_at": "2026-04-18T12:00:00+03:00",
    "source": "telegram"
  }
}
```

**Ответ `422`** (невалидные данные):

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": [{"field": "telegram_id", "message": "field required"}]
}
```

---

## Public (без Bearer)

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| GET | `/api/v1/services` | Каталог услуг для отображения и расчёта (опционально только активные). | 200 |
| GET | `/api/v1/slots` | Свободные окна по диапазону дат и выбранным услугам. | 200 |
| GET | `/api/v1/loyalty/rules` | Правила программы лояльности (лимит списания бонусами, начисление после визита). | 200 |

<span id="get-services"></span>

### GET `/api/v1/services`

**Описание:** Каталог услуг для отображения и расчёта (опционально только активные).

**Заголовки:** —

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `active_only` | query | bool | нет | Вернуть только активные услуги. По умолч. `true`. |

**Запрос:** `GET /api/v1/services?active_only=true`

**Ответ `200`:**

```json
{
  "items": [
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "name": "Шиномонтаж R17",
      "description": "Снятие/установка 4 колёс",
      "price": "2500.00",
      "duration_minutes": 60,
      "is_active": true
    }
  ]
}
```

<span id="get-slots"></span>

### GET `/api/v1/slots`

**Описание:** Свободные окна по диапазону дат и выбранным услугам.

**Заголовки:** —

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `date_from` | query | date | да | Начало диапазона дат (включительно). |
| `date_to` | query | date | да | Конец диапазона дат (включительно). |
| `service_ids[]` | query | UUID[] | да | Список идентификаторов услуг для расчёта длительности. |

**Запрос:**

```http
GET /api/v1/slots?date_from=2026-04-20&date_to=2026-04-22&service_ids=22222222-2222-4222-8222-222222222222&service_ids=33333333-3333-4333-8333-333333333333
```

**Ответ `200`:**

```json
{
  "items": [
    {
      "starts_at": "2026-04-20T10:00:00+03:00",
      "ends_at": "2026-04-20T11:30:00+03:00"
    }
  ]
}
```

<span id="get-loyalty-rules"></span>

### GET `/api/v1/loyalty/rules`

**Описание:** Правила программы лояльности (лимит списания бонусами, начисление после визита).

**Заголовки:** —

**Параметры:** —

**Запрос:** `GET /api/v1/loyalty/rules`

**Ответ `200`:**

```json
{
  "max_bonus_spend_percent": 30,
  "earn_percent_after_visit": 5
}
```

---

## Client (Bearer, роль client)

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| GET | `/api/v1/me` | Текущий профиль пользователя по токену. | 200 |
| POST | `/api/v1/appointments` | Создание записи на выбранное время и перечень услуг (опционально списание бонусов). | 201 |
| GET | `/api/v1/me/appointments` | Список записей клиента с фильтрами по датам и статусу и пагинацией. | 200 |
| PATCH | `/api/v1/me/appointments/{appointment_id}` | Обновление записи; для клиента — в т.ч. перевод в статус отмены. | 200 |
| GET | `/api/v1/me/visits` | История подтверждённых визитов с пагинацией. | 200 |
| GET | `/api/v1/me/bonus-account` | Текущий баланс бонусного счёта клиента. | 200 |
| GET | `/api/v1/me/bonus-transactions` | История бонусных операций с пагинацией. | 200 |

<span id="get-me"></span>

### GET `/api/v1/me`

**Описание:** Текущий профиль пользователя по токену.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:** —

**Запрос:** `GET /api/v1/me` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Иван",
  "phone": "+79001234567",
  "role": "client",
  "telegram_id": 123456789,
  "registered_at": "2026-04-18T12:00:00+03:00",
  "source": "telegram"
}
```

<span id="post-appointments"></span>

### POST `/api/v1/appointments`

**Описание:** Создание записи на выбранное время и перечень услуг (опционально списание бонусов).

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:** —

**Запрос:** `POST /api/v1/appointments` с телом:

```json
{
  "starts_at": "2026-04-20T10:00:00+03:00",
  "service_items": [
    { "service_id": "22222222-2222-4222-8222-222222222222", "quantity": 1 }
  ],
  "bonus_spend": 100
}
```

**Ответ `201`:**

```json
{
  "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "starts_at": "2026-04-20T10:00:00+03:00",
  "ends_at": "2026-04-20T11:00:00+03:00",
  "total_price": "2500.00",
  "status": "scheduled",
  "created_at": "2026-04-18T14:00:00+03:00",
  "service_items": [
    { "service_id": "22222222-2222-4222-8222-222222222222", "quantity": 1 }
  ]
}
```

**Ответ `409`** (слот уже занят):

```json
{
  "error": "slot_conflict",
  "message": "Requested time slot is not available",
  "details": {"starts_at": "2026-04-20T10:00:00+03:00"}
}
```

**Ответ `422`** (невалидные данные):

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": [{"field": "starts_at", "message": "field required"}]
}
```

<span id="get-me-appointments"></span>

### GET `/api/v1/me/appointments`

**Описание:** Список записей клиента с фильтрами по датам и статусу и пагинацией.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `date_from` | query | date | нет | Начало диапазона дат. |
| `date_to` | query | date | нет | Конец диапазона дат. |
| `status` | query | string | нет | Фильтр по статусу (`scheduled`, `cancelled`, `completed`). |
| `limit` | query | int | нет | Кол-во записей на странице. По умолч. 20. |
| `offset` | query | int | нет | Смещение. По умолч. 0. |

**Запрос:**

```http
GET /api/v1/me/appointments?date_from=2026-04-01&date_to=2026-04-30&status=scheduled&limit=20&offset=0
Authorization: Bearer <JWT>
```

**Ответ `200`:**

```json
{
  "items": [
    {
      "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "starts_at": "2026-04-20T10:00:00+03:00",
      "ends_at": "2026-04-20T11:00:00+03:00",
      "total_price": "2500.00",
      "status": "scheduled",
      "created_at": "2026-04-18T14:00:00+03:00",
      "service_items": [
        { "service_id": "22222222-2222-4222-8222-222222222222", "quantity": 1 }
      ]
    }
  ],
  "total": 1
}
```

<span id="patch-me-appointment"></span>

### PATCH `/api/v1/me/appointments/{appointment_id}`

**Описание:** Обновление записи; для клиента — в т.ч. перевод в статус отмены.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `appointment_id` | path | UUID | да | UUID записи на обслуживание. |

**Запрос:**

```http
PATCH /api/v1/me/appointments/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb
Authorization: Bearer <JWT>
Content-Type: application/json

{"status": "cancelled"}
```

**Ответ `200`:**

```json
{
  "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "starts_at": "2026-04-20T10:00:00+03:00",
  "ends_at": "2026-04-20T11:00:00+03:00",
  "total_price": "2500.00",
  "status": "cancelled",
  "created_at": "2026-04-18T14:00:00+03:00",
  "service_items": [
    { "service_id": "22222222-2222-4222-8222-222222222222", "quantity": 1 }
  ]
}
```

<span id="get-me-visits"></span>

### GET `/api/v1/me/visits`

**Описание:** История подтверждённых визитов с пагинацией.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `limit` | query | int | нет | Кол-во записей на странице. По умолч. 20. |
| `offset` | query | int | нет | Смещение. По умолч. 0. |

**Запрос:** `GET /api/v1/me/visits?limit=20&offset=0` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "items": [
    {
      "id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      "appointment_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      "total_amount": "2500.00",
      "bonus_spent": 0,
      "bonus_earned": 125,
      "confirmed_at": "2026-04-20T12:00:00+03:00",
      "confirmed_by_user_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
      "lines": [
        { "service_id": "22222222-2222-4222-8222-222222222222", "quantity": 1 }
      ]
    }
  ],
  "total": 1
}
```

<span id="get-me-bonus-account"></span>

### GET `/api/v1/me/bonus-account`

**Описание:** Текущий баланс бонусного счёта клиента.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:** —

**Запрос:** `GET /api/v1/me/bonus-account` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "balance": 350
}
```

<span id="get-me-bonus-transactions"></span>

### GET `/api/v1/me/bonus-transactions`

**Описание:** История бонусных операций с пагинацией.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `limit` | query | int | нет | Кол-во записей на странице. По умолч. 20. |
| `offset` | query | int | нет | Смещение. По умолч. 0. |

**Запрос:** `GET /api/v1/me/bonus-transactions?limit=20&offset=0` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "items": [
    {
      "id": "ffffffff-ffff-4fff-8fff-ffffffffffff",
      "type": "earn",
      "amount": 125,
      "visit_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      "created_at": "2026-04-20T12:05:00+03:00",
      "comment": null
    }
  ],
  "total": 1
}
```

---

## Consultation (Bearer, роль client)

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| POST | `/api/v1/consultation/messages` | Отправка сообщения в LLM-консультацию; сервер подмешивает контекст (прайс, слоты, бонусы, FAQ). | 200 |

<span id="post-consultation-messages"></span>

### POST `/api/v1/consultation/messages`

**Описание:** Отправка сообщения в LLM-консультацию; сервер подмешивает контекст (прайс, слоты, бонусы, FAQ).

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:** —

**Запрос:** `POST /api/v1/consultation/messages` с телом:

```json
{
  "message": "Сколько стоит шиномонтаж R17 и есть ли окна на завтра?"
}
```

**Ответ `200`:**

```json
{
  "reply": "Шиномонтаж R17 — от 2500 ₽ по прайсу. Свободные окна на завтра можно посмотреть в записи: ...",
  "request_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
}
```

---

## Admin (Bearer, роль admin)

Во всех запросах ниже требуется заголовок `Authorization: Bearer <JWT>` (токен администратора).

### Услуги

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| GET | `/api/v1/admin/services` | Список услуг, включая неактивные; опциональный фильтр по `is_active`. | 200 |
| POST | `/api/v1/admin/services` | Создание новой услуги (цена, длительность, активность). | 201 |
| GET | `/api/v1/admin/services/{service_id}` | Получение одной услуги по id. | 200 |
| PATCH | `/api/v1/admin/services/{service_id}` | Частичное обновление полей услуги. | 200 |
| DELETE | `/api/v1/admin/services/{service_id}` | Удаление услуги. | 204 |

<span id="get-admin-services-list"></span>

#### GET `/api/v1/admin/services`

**Описание:** Список услуг, включая неактивные; опциональный фильтр по `is_active`.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `is_active` | query | bool | нет | Фильтр по активности услуги. |

**Запрос:** `GET /api/v1/admin/services` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`** (пример тела `ServiceListResponse`, совпадает по структуре с [GET `/api/v1/services`](#get-services)):

```json
{
  "items": [
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "name": "Шиномонтаж R17",
      "description": "Снятие/установка 4 колёс",
      "price": "2500.00",
      "duration_minutes": 60,
      "is_active": true
    }
  ]
}
```

<span id="post-admin-services"></span>

#### POST `/api/v1/admin/services`

**Описание:** Создание новой услуги (цена, длительность, активность).

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:** —

**Запрос:** `POST /api/v1/admin/services` с телом:

```json
{
  "name": "Шиномонтаж R17",
  "description": "Снятие/установка 4 колёс",
  "price": "2500.00",
  "duration_minutes": 60,
  "is_active": true
}
```

**Ответ `201`:**

```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "name": "Шиномонтаж R17",
  "description": "Снятие/установка 4 колёс",
  "price": "2500.00",
  "duration_minutes": 60,
  "is_active": true
}
```

<span id="get-admin-service-by-id"></span>

#### GET `/api/v1/admin/services/{service_id}`

**Описание:** Получение одной услуги по id.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `service_id` | path | UUID | да | UUID услуги. |

**Запрос:** `GET /api/v1/admin/services/22222222-2222-4222-8222-222222222222` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "name": "Шиномонтаж R17",
  "description": "Снятие/установка 4 колёс",
  "price": "2500.00",
  "duration_minutes": 60,
  "is_active": true
}
```

<span id="patch-admin-service"></span>

#### PATCH `/api/v1/admin/services/{service_id}`

**Описание:** Частичное обновление полей услуги.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `service_id` | path | UUID | да | UUID услуги. |

**Запрос:** `PATCH /api/v1/admin/services/22222222-2222-4222-8222-222222222222` с телом (пример):

```json
{
  "price": "2600.00",
  "is_active": false
}
```

**Ответ `200`:**

```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "name": "Шиномонтаж R17",
  "description": "Снятие/установка 4 колёс",
  "price": "2600.00",
  "duration_minutes": 60,
  "is_active": false
}
```

<span id="delete-admin-service"></span>

#### DELETE `/api/v1/admin/services/{service_id}`

**Описание:** Удаление услуги.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `service_id` | path | UUID | да | UUID услуги. |

**Запрос:** `DELETE /api/v1/admin/services/22222222-2222-4222-8222-222222222222` с заголовком `Authorization: Bearer <JWT>`

**Ответ `204`:** без тела.

---

### Расписание: правила (дни недели)

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| GET | `/api/v1/admin/schedule/rules` | Список правил шаблона расписания по дням недели. | 200 |
| POST | `/api/v1/admin/schedule/rules` | Добавление правила для одного дня недели (интервал, выходной). | 201 |
| GET | `/api/v1/admin/schedule/rules/{rule_id}` | Получение одного правила по id. | 200 |
| PATCH | `/api/v1/admin/schedule/rules/{rule_id}` | Изменение правила дня недели. | 200 |
| DELETE | `/api/v1/admin/schedule/rules/{rule_id}` | Удаление правила. | 204 |

<span id="get-admin-schedule-rules"></span>

#### GET `/api/v1/admin/schedule/rules`

**Описание:** Список правил шаблона расписания по дням недели.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `date_from` | query | date | да | Начало диапазона дат. |
| `date_to` | query | date | да | Конец диапазона дат. |

**Запрос:** `GET /api/v1/admin/schedule/rules?date_from=2026-04-01&date_to=2026-04-30` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "items": [
    {
      "id": "77777777-7777-4777-8777-777777777777",
      "weekday": 0,
      "start_time": "09:00:00",
      "end_time": "18:00:00",
      "is_day_off": false
    }
  ]
}
```

<span id="post-admin-schedule-rules"></span>

#### POST `/api/v1/admin/schedule/rules`

**Описание:** Добавление правила для одного дня недели (интервал, выходной).

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:** —

**Запрос:** `POST /api/v1/admin/schedule/rules` с телом:

```json
{
  "weekday": 0,
  "start_time": "09:00:00",
  "end_time": "18:00:00",
  "is_day_off": false
}
```

**Ответ `201`:**

```json
{
  "id": "77777777-7777-4777-8777-777777777777",
  "weekday": 0,
  "start_time": "09:00:00",
  "end_time": "18:00:00",
  "is_day_off": false
}
```

<span id="get-admin-schedule-rule-by-id"></span>

#### GET `/api/v1/admin/schedule/rules/{rule_id}`

**Описание:** Получение одного правила по id.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `rule_id` | path | UUID | да | UUID правила расписания. |

**Запрос:** `GET /api/v1/admin/schedule/rules/77777777-7777-4777-8777-777777777777` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "id": "77777777-7777-4777-8777-777777777777",
  "weekday": 0,
  "start_time": "09:00:00",
  "end_time": "18:00:00",
  "is_day_off": false
}
```

<span id="patch-admin-schedule-rule"></span>

#### PATCH `/api/v1/admin/schedule/rules/{rule_id}`

**Описание:** Изменение правила дня недели.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `rule_id` | path | UUID | да | UUID правила расписания. |

**Запрос:** `PATCH /api/v1/admin/schedule/rules/77777777-7777-4777-8777-777777777777` с телом (пример):

```json
{
  "end_time": "17:00:00",
  "is_day_off": false
}
```

**Ответ `200`:**

```json
{
  "id": "77777777-7777-4777-8777-777777777777",
  "weekday": 0,
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "is_day_off": false
}
```

<span id="delete-admin-schedule-rule"></span>

#### DELETE `/api/v1/admin/schedule/rules/{rule_id}`

**Описание:** Удаление правила.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `rule_id` | path | UUID | да | UUID правила расписания. |

**Запрос:** `DELETE /api/v1/admin/schedule/rules/77777777-7777-4777-8777-777777777777` с заголовком `Authorization: Bearer <JWT>`

**Ответ `204`:** без тела.

---

### Расписание: исключения (даты)

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| GET | `/api/v1/admin/schedule/exceptions` | Список исключений расписания на конкретные даты в диапазоне. | 200 |
| POST | `/api/v1/admin/schedule/exceptions` | Добавление исключения на дату (особые часы или выходной). | 201 |
| GET | `/api/v1/admin/schedule/exceptions/{exception_id}` | Получение одного исключения по id. | 200 |
| PATCH | `/api/v1/admin/schedule/exceptions/{exception_id}` | Изменение исключения на дату. | 200 |
| DELETE | `/api/v1/admin/schedule/exceptions/{exception_id}` | Удаление исключения. | 204 |

<span id="get-admin-schedule-exceptions"></span>

#### GET `/api/v1/admin/schedule/exceptions`

**Описание:** Список исключений расписания на конкретные даты в диапазоне.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `date_from` | query | date | нет | Начало диапазона дат. |
| `date_to` | query | date | нет | Конец диапазона дат. |

**Запрос:** `GET /api/v1/admin/schedule/exceptions?date_from=2026-05-01&date_to=2026-05-31` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "items": [
    {
      "id": "88888888-8888-4888-8888-888888888888",
      "date": "2026-05-09",
      "start_time": "10:00:00",
      "end_time": "14:00:00",
      "is_day_off": true
    }
  ]
}
```

<span id="post-admin-schedule-exceptions"></span>

#### POST `/api/v1/admin/schedule/exceptions`

**Описание:** Добавление исключения на дату (особые часы или выходной).

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:** —

**Запрос:** `POST /api/v1/admin/schedule/exceptions` с телом:

```json
{
  "date": "2026-05-09",
  "start_time": "10:00:00",
  "end_time": "14:00:00",
  "is_day_off": true
}
```

**Ответ `201`:**

```json
{
  "id": "88888888-8888-4888-8888-888888888888",
  "date": "2026-05-09",
  "start_time": "10:00:00",
  "end_time": "14:00:00",
  "is_day_off": true
}
```

<span id="get-admin-schedule-exception-by-id"></span>

#### GET `/api/v1/admin/schedule/exceptions/{exception_id}`

**Описание:** Получение одного исключения по id.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `exception_id` | path | UUID | да | UUID исключения расписания. |

**Запрос:** `GET /api/v1/admin/schedule/exceptions/88888888-8888-4888-8888-888888888888` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "id": "88888888-8888-4888-8888-888888888888",
  "date": "2026-05-09",
  "start_time": "10:00:00",
  "end_time": "14:00:00",
  "is_day_off": true
}
```

<span id="patch-admin-schedule-exception"></span>

#### PATCH `/api/v1/admin/schedule/exceptions/{exception_id}`

**Описание:** Изменение исключения на дату.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `exception_id` | path | UUID | да | UUID исключения расписания. |

**Запрос:** `PATCH /api/v1/admin/schedule/exceptions/88888888-8888-4888-8888-888888888888` с телом (пример):

```json
{
  "is_day_off": false,
  "start_time": "09:00:00",
  "end_time": "18:00:00"
}
```

**Ответ `200`:**

```json
{
  "id": "88888888-8888-4888-8888-888888888888",
  "date": "2026-05-09",
  "start_time": "09:00:00",
  "end_time": "18:00:00",
  "is_day_off": false
}
```

<span id="delete-admin-schedule-exception"></span>

#### DELETE `/api/v1/admin/schedule/exceptions/{exception_id}`

**Описание:** Удаление исключения.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `exception_id` | path | UUID | да | UUID исключения расписания. |

**Запрос:** `DELETE /api/v1/admin/schedule/exceptions/88888888-8888-4888-8888-888888888888` с заголовком `Authorization: Bearer <JWT>`

**Ответ `204`:** без тела.

---

### Записи и визиты

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| GET | `/api/v1/admin/appointments` | Журнал записей с фильтрами и вложенным объектом пользователя; пагинация. | 200 |
| POST | `/api/v1/admin/visits` | Подтверждение визита: фактические услуги, сумма, списание бонусов; начисление бонусов считает сервер. | 201 |

<span id="get-admin-appointments"></span>

#### GET `/api/v1/admin/appointments`

**Описание:** Журнал записей с фильтрами и вложенным объектом пользователя; пагинация.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `date_from` | query | date | нет | Начало диапазона дат. |
| `date_to` | query | date | нет | Конец диапазона дат. |
| `status` | query | string | нет | Фильтр по статусу (`scheduled`, `cancelled`, `completed`). |
| `user_id` | query | UUID | нет | Фильтр по UUID клиента. |
| `limit` | query | int | нет | Кол-во записей на странице. По умолч. 20. |
| `offset` | query | int | нет | Смещение. По умолч. 0. |

**Запрос:**

```http
GET /api/v1/admin/appointments?date_from=2026-04-01&date_to=2026-04-30&status=scheduled&user_id=550e8400-e29b-41d4-a716-446655440001&limit=20&offset=0
Authorization: Bearer <JWT>
```

**Ответ `200`:**

```json
{
  "items": [
    {
      "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "starts_at": "2026-04-20T10:00:00+03:00",
      "ends_at": "2026-04-20T11:00:00+03:00",
      "total_price": "2500.00",
      "status": "scheduled",
      "created_at": "2026-04-18T14:00:00+03:00",
      "service_items": [
        { "service_id": "22222222-2222-4222-8222-222222222222", "quantity": 1 }
      ],
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Иван",
        "phone": "+79001234567",
        "role": "client",
        "telegram_id": 123456789,
        "registered_at": "2026-04-18T12:00:00+03:00",
        "source": "telegram"
      }
    }
  ],
  "total": 1
}
```

<span id="post-admin-visits"></span>

#### POST `/api/v1/admin/visits`

**Описание:** Подтверждение визита: фактические услуги, сумма, списание бонусов; начисление бонусов считает сервер.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:** —

**Запрос:** `POST /api/v1/admin/visits` с телом:

```json
{
  "appointment_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "lines": [
    { "service_id": "22222222-2222-4222-8222-222222222222", "quantity": 1 }
  ],
  "total_amount": "2500.00",
  "bonus_spent": 0
}
```

**Ответ `201`:**

```json
{
  "id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
  "appointment_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "total_amount": "2500.00",
  "bonus_spent": 0,
  "bonus_earned": 125,
  "confirmed_at": "2026-04-20T12:00:00+03:00",
  "confirmed_by_user_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  "lines": [
    { "service_id": "22222222-2222-4222-8222-222222222222", "quantity": 1 }
  ]
}
```

---

### Бонусы (клиент в path)

| Метод | Путь | Описание | Успех |
|-------|------|----------|-------|
| GET | `/api/v1/admin/users/{user_id}/bonus-account` | Просмотр бонусного счёта выбранного клиента. | 200 |
| POST | `/api/v1/admin/users/{user_id}/bonus-transactions` | Ручная корректировка баланса (тип `adjust`, комментарий для аудита). | 201 |

<span id="get-admin-user-bonus-account"></span>

#### GET `/api/v1/admin/users/{user_id}/bonus-account`

**Описание:** Просмотр бонусного счёта выбранного клиента.

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `user_id` | path | UUID | да | UUID клиента. |

**Запрос:** `GET /api/v1/admin/users/550e8400-e29b-41d4-a716-446655440001/bonus-account` с заголовком `Authorization: Bearer <JWT>`

**Ответ `200`:**

```json
{
  "id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "balance": 350
}
```

<span id="post-admin-user-bonus-transactions"></span>

#### POST `/api/v1/admin/users/{user_id}/bonus-transactions`

**Описание:** Ручная корректировка баланса (тип `adjust`, комментарий для аудита).

**Заголовки:**

| Заголовок | Значение | Обязательный |
|---|---|---|
| `Authorization` | `Bearer <JWT>` | да |
| `Content-Type` | `application/json` | да |

**Параметры:**

| Параметр | Расположение | Тип | Обязательный | Описание |
|---|---|---|---|---|
| `user_id` | path | UUID | да | UUID клиента. |

**Запрос:** `POST /api/v1/admin/users/550e8400-e29b-41d4-a716-446655440001/bonus-transactions` с телом:

```json
{
  "amount": 50,
  "comment": "Жест доброй воли"
}
```

**Ответ `201`:**

```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "type": "adjust",
  "amount": 50,
  "visit_id": null,
  "created_at": "2026-04-18T16:00:00+03:00",
  "comment": "Жест доброй воли"
}
```

---

## Что намеренно вне публичного API

Уведомления в Telegram после событий описаны в [integrations.md](../integrations.md) как канал доставки, не как отдельные REST-ресурсы.

---

## Сводка: количество методов API

Подсчёт по **сводным таблицам** эндпоинтов в этом документе (одна строка таблицы = одна уникальная пара «HTTP-метод + путь»).

| Раздел документа | Количество методов |
|------------------|-------------------:|
| Auth (без Bearer) | 1 |
| Public (без Bearer) | 3 |
| Client (Bearer, клиент) | 7 |
| Consultation (Bearer, клиент) | 1 |
| Admin — услуги | 5 |
| Admin — расписание: правила (`schedule/rules`) | 5 |
| Admin — расписание: исключения (`schedule/exceptions`) | 5 |
| Admin — журнал записей и подтверждение визитов | 2 |
| Admin — бонусный счёт и корректировки | 2 |
| **Итого** | **31** |

По HTTP-глаголам (по тем же строкам таблиц): **GET** — 16, **POST** — 8, **PATCH** — 4, **DELETE** — 3.
