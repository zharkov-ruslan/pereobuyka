# iter-06 — Backend docs: итог

Соответствие чеклисту и артефактам — раздел **iter-06** в [`tasklist-backend.md`](../../../tasklist-backend.md).

## Что реализовано

### `backend/README.md` — создан
Быстрый старт backend: требования, установка (`make backend-install`), настройка `.env`, запуск (`make backend-run`), ссылки на OpenAPI (`/docs`, `/redoc`), таблица переменных окружения, таблица Make-команд, структура пакета, ссылки на контрактную документацию.

### `backend/.env.example` — обновлён
- `DATABASE_URL` переключён на SQLite по умолчанию (`sqlite+aiosqlite:///./dev.db`) — PostgreSQL вынесен в комментарий; это согласовано с дефолтом в `config.py`
- Добавлено уточнение к `OPENROUTER_API_KEY`: «необходим только для модуля консультации (этап 3)»

### `Makefile` — без изменений в рамках iter-06
Цели `backend-*` уже были актуальны. Дополнительно в репозитории есть цели `db-up` / `db-migrate` / `db-seed` и др. для PostgreSQL (см. README и database-tasklist) — в [`tasklist-backend.md`](../../../tasklist-backend.md) для iter-06 это отражено формулировкой «при необходимости migrate».

### `docs/plan.md` — без изменений
Все ссылки на tasklist уже использовали корректный путь `docs/tasks/`, не устаревший `tasklists/` (как в артефактах iter-06 в tasklist).

## Принятые решения

- В `.env.example` SQLite как дефолт ускоряет локальный старт: не нужен Docker/PostgreSQL для разработки на этапе MVP.
- README ссылается на контрактные документы относительными путями — актуально при перемещении `backend/`.

## Статус DoD

| Критерий | Выполнено |
|----------|-----------|
| README + `.env.example` согласованы с кодом | ✅ |
| `docs/plan.md` не содержит `tasklists/` в URL | ✅ (было чисто) |
| `make backend-test` и `make backend-lint` — зелёные | ✅ (не нарушены; изменения только в документации) |
