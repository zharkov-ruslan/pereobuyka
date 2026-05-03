# Итог iter-fe-02 — каркас web

## Реализовано

- Создан `web/` на Next.js App Router, React, TypeScript, Tailwind CSS v4, shadcn/ui, `pnpm`.
- Подключены базовые shadcn/ui компоненты: `button`, `card`, `input`, `badge`, `separator`, `sheet`, `avatar`, `field`.
- Добавлен общий shell приложения:
  - локальная MVP-сессия в `localStorage` с префиксом `pereobuyka:web:*`;
  - вход клиента через `POST /api/v1/auth/web`;
  - ручной Bearer token для локальной проверки роли администратора;
  - роль-зависимая навигация;
  - выход с очисткой локальной сессии.
- Добавлены стартовые маршруты `/`, `/client`, `/admin` и глобальная плавающая оболочка чат-виджета.
- Добавлен единый HTTP-клиент `apiFetch` с `NEXT_PUBLIC_API_BASE_URL` и базовой обработкой ошибок.
- Добавлен `web/.env.example`.

## Документы и автоматизация

- В `Makefile` добавлены цели `web-install`, `web-dev`, `web-lint`, `web-build`.
- В `README.md` добавлен быстрый старт для web.
- В `docs/vision.md` закрыт open question по frontend-стеку.
- `docs/tasks/tasklist-frontend.md` обновлён по статусу итерации.

## Отклонения и допущения

- Полноценный защищённый вход администратора не реализовывался: для MVP оставлен ручной Bearer token, потому что backend-контракт итерации 1 фиксирует отдельный клиентский `POST /auth/web`.
- Чат пока без отправки сообщений и истории: это сознательная заглушка до iter-fe-06.
- Серверная защита web-роутов не добавлялась; текущий shell скрывает чужие разделы на клиенте. Защита данных остаётся на backend API.

## Проверки

- `pnpm lint` — зелёный.
- `pnpm build` — зелёный.
- IDE diagnostics для `web/` — без ошибок.

