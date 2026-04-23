# Миграции БД и доступ: практическая справка

Краткое руководство для разработчиков репозитория «Переобуйка». Архитектурные решения: [ADR-001](adr/adr-001-database.md) (PostgreSQL), [ADR-003](adr/adr-003-orm.md) (SQLAlchemy 2 async, Alembic), [ADR-004](adr/adr-004-database-migrations-workflow.md) (расположение Alembic, ревизии, downgrade).

Целевая схема таблиц описана в [data-model.md](data-model.md).

---

## Предпосылки

- Установлен **uv**, проект backend: каталог `backend/`.
- Доступна база **PostgreSQL** (локально: `make db-up` из корня репозитория, см. [iter-db-04](../tasks/tasklist-database.md#iter-db-04--infra-локальный-postgresql-migrations-seed) и [backend/README.md](../../backend/README.md)).
- Переменная **`DATABASE_URL`** (или согласованный алиас в `backend` config) указывает на нужную БД.

Все команды ниже выполняются из **`backend/`** (или с префиксом `cd backend &&`):

```bash
cd backend && uv run alembic --help
```

Из корня репозитория после `make db-up` и настройки `DATABASE_URL` на PostgreSQL в `backend/.env`: `make db-migrate` (алиас к `alembic upgrade head`). Начальные данные: `make db-seed`.

---

## Где что лежит (целевая структура)

| Путь | Назначение |
|------|------------|
| `backend/alembic.ini` | Настройки Alembic (script_location, prepend_sys_path) |
| `backend/alembic/env.py` | Подключение к БД, `target_metadata`, вызов `run_migrations` |
| `backend/alembic/versions/` | Файлы ревизий `*.py` |
| `backend/src/pereobuyka/db/` | ORM-модели (`Base`, mapped classes по схеме Alembic); `DeclarativeBase` для будущего autogenerate |

**Граница слоёв:** схемы **Pydantic** — только HTTP API; таблицы и mapped classes — в репозиториях / ORM-слое, без протаскивания ORM-объектов в ответы API ([ADR-003](adr/adr-003-orm.md)).

---

## Типовые команды Alembic

После появления `alembic.ini` (из `backend/`):

| Действие | Команда |
|----------|---------|
| Текущая ревизия | `uv run alembic current` |
| История | `uv run alembic history` |
| Применить все | `uv run alembic upgrade head` |
| Откатить одну ревизию | `uv run alembic downgrade -1` |
| Новая ревизия (пустая) | `uv run alembic revision -m "описание"` |
| Новая ревизия с autogenerate | `uv run alembic revision --autogenerate -m "описание"` |

Перед коммитом ревизии с **autogenerate** всегда просматривайте сгенерированный `upgrade()` / `downgrade()` и уберите лишнее (лишние `drop` и т.д.).

---

## Autogenerate vs ручные правки

- **Autogenerate** — основной путь при изменении моделей SQLAlchemy; сравнивает `MetaData` с текущей БД.
- **Ручной SQL** в ревизии — для данных, расширений PostgreSQL, индексов, которые autogenerate не отражает; зафиксируйте причину комментарием в файле.

---

## Тесты с БД (Testcontainers)

Интеграционные тесты поднимают PostgreSQL в Docker (**Testcontainers**), накатывают миграции на выданный URL и выполняют сценарии против реальной схемы. Подробности — в [tasklist-database.md](../tasks/tasklist-database.md) (iter-db-05) и в `backend/README.md` после появления фикстур.

Требуется **запущенный Docker** на машине разработчика и в CI, если гоняются эти тесты.

---

## Что читать дальше

- [ADR-004](adr/adr-004-database-migrations-workflow.md) — политика ревизий и downgrade
- [data-model.md](data-model.md) — таблицы и связи
