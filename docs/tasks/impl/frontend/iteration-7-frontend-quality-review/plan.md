# iter-fe-07 — Ревью качества frontend

## План

1. Прогнать `pnpm lint` и `pnpm build` в `web/`.
2. Сверить код с чек-листом **vercel-react-best-practices** (водопады async, бандл, мемоизация, эффекты) и **nextjs-app-router-patterns** (границы client/server, гидрация).
3. Устранить **ошибки** ESLint (в т.ч. `react-hooks/set-state-in-effect`, `react-hooks/exhaustive-deps`, `react-hooks/refs`).
4. Зафиксировать оставшиеся улучшения некритичного уровня в [`docs/backlog.md`](../../../../backlog.md).

## Файлы

- Основные правки: `web/components/admin-create-booking-sheet.tsx`, `web/app/admin/page.tsx`.
- Отчёт: этот каталог (`summary.md`).
