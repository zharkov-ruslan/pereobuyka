# iter-06 — Backend docs: план реализации

## Цель

Задокументировать backend так, чтобы новый участник мог воспроизвести окружение без устных инструкций; исправить ссылки в `docs/plan.md` на `docs/tasks/`.

## Состав работ

1. **`backend/README.md`** — быстрый старт: требования, установка, настройка env, запуск, OpenAPI, команды Make, тесты/линтер
2. **`backend/.env.example`** — проверить полноту переменных и корректность комментариев
3. **`Makefile`** — убедиться, что команды `backend-install / backend-run / backend-test / backend-lint` актуальны; добавить при необходимости
4. **`docs/plan.md`** — проверить таблицу этапов на наличие путей вида `tasklists/` → заменить на `docs/tasks/`

## Файлы, которые будут созданы / изменены

| Файл | Действие |
|------|----------|
| `backend/README.md` | создать |
| `backend/.env.example` | проверить / обновить |
| `Makefile` | проверить / обновить |
| `docs/plan.md` | проверить / исправить ссылки |
| `docs/tasks/impl/backend/iteration-06-backend-docs/plan.md` | создать (этот файл) |
| `docs/tasks/impl/backend/iteration-06-backend-docs/summary.md` | создать после реализации |
| `docs/tasks/tasklist-backend.md` | обновить статус iter-06 |

## Критерии готовности

- `backend/README.md` существует: install → env → run → `/docs` проверяется вручную
- `backend/.env.example` покрывает все переменные из `config.py`
- Makefile содержит все команды из README
- `docs/plan.md` не содержит `tasklists/` в URL-ссылках
