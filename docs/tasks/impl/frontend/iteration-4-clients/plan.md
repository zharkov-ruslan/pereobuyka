# План iter-fe-04 — экран «Клиенты сервиса»

## Цель

Реализовать маршрут `/admin/clients`: список клиентов с KPI и карточку выбранного клиента на той же странице с записями, визитами и базовыми правками по API iter-fe-01.

## Решения

- **Источник данных:** backend API: `GET /api/v1/admin/clients`, `GET /api/v1/admin/clients/{user_id}`, `GET /api/v1/admin/users/{user_id}/appointments`, новый `GET /api/v1/admin/users/{user_id}/visits`, `GET /api/v1/admin/services`.
- **Auth:** использовать текущую MVP-сессию администратора из `localStorage`; backend остаётся источником проверки роли.
- **UI:** отдельный App Router маршрут `/admin/clients`, shadcn/ui-композиция на текущих компонентах (`Card`, `Badge`, `Button`, `Field`, `Input`), без новой таблиц/форм-библиотеки.
- **Карточка клиента:** открывается на той же странице по клику из списка; возврат кнопкой «К списку клиентов».
- **Правки:** изменение статуса/скидки/услуг записи через `PATCH /api/v1/admin/appointments/{id}`, подтверждение визита через `POST /api/v1/admin/visits`, корректировка визита через `PATCH /api/v1/admin/visits/{id}`, оценка клиента через `POST /api/v1/admin/visits/{id}/client-rating`.
- **Telegram:** показывать ссылку, если backend отдаёт `telegram_username` или `telegram_id`; для username использовать `https://t.me/...`, для id — `tg://user?id=...`.

## Состав работ

1. Расширить backend admin web API:
   - добавить `telegram_id` в строку клиента;
   - добавить `GET /api/v1/admin/users/{user_id}/visits`.
2. Расширить `web/lib/admin-api.ts` типами клиентов, услуг, визитов и функциями загрузки/мутаций.
3. Добавить `web/app/admin/clients/page.tsx`:
   - loading/empty/error;
   - список клиентов с сортировкой на клиенте;
   - карточка клиента с KPI и Telegram-ссылкой;
   - переключение «Записи» / «Визиты»;
   - формы редактирования service lines, скидки, бонусов и оценки.
4. Разблокировать пункт навигации «Клиенты».
5. Обновить API-документацию, tasklist и итоговый summary.

## Проверки

- `make web-lint`
- `make web-build`
- IDE diagnostics для изменённых frontend-файлов
