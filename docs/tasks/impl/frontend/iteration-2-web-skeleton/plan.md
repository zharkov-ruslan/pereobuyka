# План iter-fe-02 — каркас web

## Цель

Создать базовый `web/` для следующих frontend-итераций: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, общий layout по ролям, MVP-вход и глобальная оболочка чат-виджета.

## Решения

- **Стек:** Next.js App Router + React + TypeScript + Tailwind CSS, пакетный менеджер `pnpm`.
- **UI:** shadcn/ui, семантические токены темы, без ручного дублирования компонентов.
- **Auth MVP:** клиентский вход через `POST /api/v1/auth/web` по `telegram_username`; JWT хранится в `localStorage` только для демо/MVP. Админский токен можно вставить вручную через форму входа для проверки админ-разделов.
- **API base URL:** публичная переменная `NEXT_PUBLIC_API_BASE_URL`; по умолчанию `http://localhost:8000`.
- **Границы логики:** frontend не считает цены, бонусы и слоты; только вызывает backend и отображает состояния.
- **Чат:** в этой итерации только глобальная плавающая оболочка/заглушка; полноценная история и отправка сообщений остаются в iter-fe-06.

## Структура

- `web/app/` — App Router, страницы входа, client/admin dashboards-заглушки, layout.
- `web/components/` — app-shell, auth form, chat widget, shadcn/ui.
- `web/lib/` — HTTP-клиент, auth storage, utils.
- `web/.env.example` — публичные настройки frontend без секретов.

## Состав работ

1. Инициализировать `web/` с Next.js, ESLint, Tailwind и pnpm.
2. Подключить shadcn/ui и базовые компоненты (`button`, `card`, `input`, `badge`, `separator`, `sheet`, `avatar`).
3. Добавить `ApiError`/`apiFetch`, типы auth и helpers для token storage.
4. Реализовать страницу входа:
   - вход клиента через `telegram_username`;
   - ручной режим Bearer token для админа/отладки;
   - выход очищает локальное состояние.
5. Реализовать общий shell:
   - навигация по ролям;
   - отображение текущего пользователя;
   - маршруты `/client` и `/admin` как стартовые заглушки;
   - плавающая кнопка и панель чат-заглушки.
6. Добавить Makefile-цели `web-install`, `web-dev`, `web-lint`, `web-build`.
7. Обновить README, `docs/vision.md`, `tasklist-frontend.md`; создать `summary.md`.

## Проверки

- `make web-lint`
- `make web-build`

