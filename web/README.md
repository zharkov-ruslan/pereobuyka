# Переобуйка — Web (Next.js)

Клиентский и административный интерфейс: [Next.js](https://nextjs.org) App Router, React, TypeScript, [shadcn/ui](https://ui.shadcn.com), Tailwind CSS. API — отдельный сервис в [`../backend/`](../backend/).

## Требования

- Node.js **22+**
- **pnpm** (менеджер пакетов монорепозитория)

## Быстрый старт

Из **корня** репозитория (рекомендуется):

```bash
make web-install
```

Создать `web/.env` из шаблона (Windows PowerShell):

```powershell
Copy-Item web\.env.example web\.env
```

По умолчанию [`web/.env.example`](.env.example) задаёт `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000` (на Windows предпочтительнее **127.0.0.1**, не `localhost` — см. [корневой README](../README.md)).

Запуск dev-сервера (нужен поднятый backend):

```bash
make web-dev
```

Открыть [http://localhost:3000](http://localhost:3000).

Проверки качества:

```bash
make web-lint
make web-build
```

## Тесты

Автотестов UI пока нет. Скрипт `pnpm test` (и `make web-test` из корня) — **заглушка** с кодом выхода 0, чтобы единообразно вызывать «тестовый» шаг в скриптах; реальные тесты планируются отдельно. См. [`package.json`](package.json).

## Документация проекта

- [Онбординг](../docs/onboarding.md) · [Архитектура](../docs/architecture.md)
- [Корневой README](../README.md) — полный онбординг (БД, backend, бот)
- [docs/vision.md](../docs/vision.md) — видение и границы системы
- [docs/tasks/tasklist-frontend.md](../docs/tasks/tasklist-frontend.md) — итерации фронтенда
- HTTP API: [docs/tech/api/openapi.yaml](../docs/tech/api/openapi.yaml), [api-contracts.md](../docs/tech/api/api-contracts.md)
