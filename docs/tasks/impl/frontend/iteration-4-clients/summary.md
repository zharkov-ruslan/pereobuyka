# Итог iter-fe-04 — экран «Клиенты сервиса»

## Реализовано

- Добавлен маршрут `/admin/clients`:
  - таблица клиентов с визитами, суммой, бонусами и рейтингом;
  - карточка клиента на той же странице;
  - ссылка «К списку клиентов»;
  - Telegram-ссылка по `telegram_username` или `telegram_id`;
  - вкладки «Записи» и «Визиты».
- В карточке клиента доступны правки:
  - услуги и скидка записи через `PATCH /api/v1/admin/appointments/{appointment_id}`;
  - отмена записи;
  - подтверждение визита через `POST /api/v1/admin/visits`;
  - услуги, сумма и бонусы визита через `PATCH /api/v1/admin/visits/{visit_id}`;
  - оценка клиента через `POST /api/v1/admin/visits/{visit_id}/client-rating`.
- Разблокирован пункт навигации «Клиенты».
- Расширен backend admin web API:
  - `AdminClientRow.telegram_id`;
  - `GET /api/v1/admin/users/{user_id}/visits`.
- Обновлены `api-contracts.md` и `openapi.yaml` под новый endpoint и поле клиента.

## Решения и ограничения

- UI использует текущую MVP-сессию из `localStorage`; контроль роли остаётся на backend.
- Таблица сделана нативной HTML-таблицей в текущей shadcn-композиции без установки новых компонентов.
- Пересчёт итогов записи и валидация пересечений слотов остаются на backend.

## Проверки

- `pnpm lint` — зелёный.
- `pnpm build` — зелёный.
- `make backend-lint` — зелёный.
- `make backend-test` — зелёный, 25 tests passed.
- IDE diagnostics для изменённых файлов — без ошибок на момент проверки.
