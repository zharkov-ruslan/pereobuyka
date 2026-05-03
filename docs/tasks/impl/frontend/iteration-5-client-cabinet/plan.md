# План iter-fe-05 — личный кабинет клиента + визард записи

## Цель

Реализовать маршрут `/client`: приветствие клиента, переход в Telegram-бот, списки записей и визитов, визард самостоятельной записи с восстановлением черновика из `localStorage`.

## Решения

- **Источник данных:** backend API: `GET /api/v1/services`, `GET /api/v1/loyalty/rules`, `GET /api/v1/slots`, `POST /api/v1/appointments`, `GET/PATCH /api/v1/me/appointments`, `GET /api/v1/me/visits`, `GET /api/v1/me/bonus-account`, `POST /api/v1/me/visits/{visit_id}/service-rating`.
- **Auth:** использовать текущую MVP-сессию клиента из `localStorage`; backend остаётся источником проверки роли.
- **LocalStorage:** ключ `pereobuyka:web:appointment-draft:v1`, хранить только выбранные услуги, выбранный слот и бонусы к списанию; очищать после успешного `201`.
- **UI:** один App Router маршрут `/client`, без отдельной страницы визарда; loading/empty/error состояния внутри текущей shadcn-композиции (`Card`, `Badge`, `Button`, `Field`, `Input`).
- **Telegram:** ссылка берётся из `NEXT_PUBLIC_TELEGRAM_BOT_URL`; если переменная не задана, кнопка остаётся неактивной с подсказкой.

## Состав работ

1. Добавить `web/lib/client-api.ts` с типами и функциями клиентского кабинета.
2. Заменить заглушку `web/app/client/page.tsx`:
   - приветствие, бонусный баланс, CTA;
   - списки предстоящих/отменённых записей и визитов;
   - отмена scheduled-записи;
   - оценка сервиса по визиту;
   - визард: услуги → слот → подтверждение.
3. Добавить `NEXT_PUBLIC_TELEGRAM_BOT_URL` в `web/.env.example`.
4. Обновить `tasklist-frontend.md` и итоговый `summary.md`.

## Проверки

- `make web-lint`
- `make web-build`
- IDE diagnostics для изменённых frontend-файлов
