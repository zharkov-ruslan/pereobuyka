# Локальный запуск через Docker Compose

Полный стек **postgres + backend + bot + web** одной командой. Альтернатива — гибридный режим (только БД в Docker, сервисы на хосте): см. [README.md](../../README.md) и [onboarding.md](../onboarding.md).

---

## Требования

| Инструмент | Примечание |
|------------|------------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Engine + Compose v2 |
| GNU Make | опционально; можно вызывать `docker compose` напрямую |
| Свободные порты | `5432`, `8000`, `3000` |

На **Windows** предпочитайте **`127.0.0.1`**, не `localhost`, в URL API (IPv6). Если путь к репозиторию содержит **кириллицу**, в `Makefile` задано `COMPOSE_PROJECT_NAME=pereobuyka` — используйте `make compose-*`, не голый `docker compose` без этой переменной.

---

## Быстрый старт

Из **корня** репозитория:

```powershell
Copy-Item .env.docker.example .env.docker
# Отредактируйте .env.docker: BOT_SECRET, ADMIN_API_TOKEN, при необходимости OPENROUTER_API_KEY и TELEGRAM_BOT_TOKEN
make compose-up
make compose-seed
make compose-health
```

Откройте:

- Backend health: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs
- Web: http://127.0.0.1:3000

---

## Переменные окружения

Файл **`.env.docker`** (не коммитить) — шаблон [`.env.docker.example`](../../.env.docker.example).

| Переменная | Обязательность | Назначение |
|------------|----------------|------------|
| `BOT_SECRET` | да | Общий секрет backend ↔ bot |
| `ADMIN_API_TOKEN` | да (для админки) | Bearer для `/api/v1/admin/*` |
| `TELEGRAM_BOT_TOKEN` | для бота | Без токена контейнер `bot` будет перезапускаться |
| `OPENROUTER_API_KEY` | для LLM/STT | Консультация и голос |
| `NEXT_PUBLIC_API_BASE_URL` | да | Origin backend **для браузера**; по умолчанию `http://127.0.0.1:8000` |

`DATABASE_URL` для backend задаётся в `docker-compose.yml` (хост `postgres`, не `127.0.0.1`).

---

## Команды Make

| Цель | Действие |
|------|----------|
| `make compose-up` | Сборка и подъём всего стека (`--build --wait`) |
| `make compose-down` | Остановка и удаление контейнеров |
| `make compose-ps` | Статус сервисов |
| `make compose-logs` | Логи всех сервисов (follow) |
| `make compose-logs-backend` | Логи backend |
| `make compose-logs-bot` | Логи bot |
| `make compose-logs-web` | Логи web |
| `make compose-logs-postgres` | Логи PostgreSQL |
| `make compose-health` | `curl` → `/health` |
| `make compose-seed` | Seed демо-данных в БД |
| `make compose-registry-pull` | Pull образов из GHCR (override registry) |
| `make compose-registry-up` | Pull + подъём стека без `--build` |
| `make compose-registry-down` | Остановка registry-стека |

Эквивалент без Make:

```bash
docker compose up -d --build --wait
docker compose exec backend python -m pereobuyka.scripts.seed
```

---

## Гибридная разработка (только PostgreSQL)

Если backend/bot/web запускаются на хосте через `make backend-run` и т.д.:

```bash
make db-up
make db-migrate
make db-seed
```

`make db-up` поднимает **только** сервис `postgres`, не весь стек.

---

## Структура артефактов

| Путь | Назначение |
|------|------------|
| [`devops/`](../../devops/) | Dockerfile и .dockerignore по сервисам |
| [`docker-compose.yml`](../../docker-compose.yml) | Описание полного стека |
| [`.env.docker.example`](../../.env.docker.example) | Шаблон env для compose |

Подробнее о layout: [`devops/README.md`](../../devops/README.md).

---

## Типовые проблемы

### «project name must not be empty» (Windows + кириллица в пути)

Используйте цели `make compose-*` или экспортируйте `COMPOSE_PROJECT_NAME=pereobuyka` перед `docker compose`.

### Web не достучится до API

`NEXT_PUBLIC_API_BASE_URL` должен указывать на **хост** с проброшенным портом backend (`http://127.0.0.1:8000`), не на `http://backend:8000` — это имя только внутри Docker-сети.

### Backend unhealthy / миграции

Проверьте `make compose-logs-backend`. Entrypoint выполняет `alembic upgrade head` перед uvicorn. Убедитесь, что postgres healthy: `make compose-logs-postgres`.

### Bot в restart loop

Заполните `TELEGRAM_BOT_TOKEN` в `.env.docker` и совпадающий `BOT_SECRET` с backend.

### Порт занят

Остановите локальные `make backend-run` / `web-dev` или измените mapping портов в `docker-compose.yml`.

---

## Дальше

- Публикация образов в GHCR — см. раздел [Запуск из GHCR](#запуск-из-ghcr) ниже и [`tasklist-devops.md`](../tasks/tasklist-devops.md)
- Дорожная карта — [`plan.md`](../plan.md), этап 6

---

## Запуск из GHCR

Образы **backend**, **bot**, **web** публикуются workflow [`.github/workflows/docker-publish.yml`](../../.github/workflows/docker-publish.yml) в GitHub Container Registry при push в `master` или вручную через **Actions → Publish Docker images → Run workflow**.

### Имена образов

| Сервис | Image |
|--------|-------|
| backend | `ghcr.io/zharkov-ruslan/pereobuyka-backend` |
| bot | `ghcr.io/zharkov-ruslan/pereobuyka-bot` |
| web | `ghcr.io/zharkov-ruslan/pereobuyka-web` |

Теги: `latest` (ветка master) и полный SHA коммита (например `abc123def456...`).

### Prerequisites

1. Успешный run workflow в GitHub Actions (образы появились в **Packages** репозитория).
2. Файл `.env.docker` (как для локальной сборки).
3. Если packages **private** — авторизация в GHCR:

```powershell
# Personal Access Token (classic) с read:packages
docker login ghcr.io -u YOUR_GITHUB_USERNAME
```

Для публичных packages login не обязателен.

### Подъём стека без локальной сборки

Override [`docker-compose.registry.yml`](../../docker-compose.registry.yml) подменяет `build:` на `image:`.

```powershell
make compose-registry-up
make compose-seed
make compose-health
```

Эквивалент без Make:

```powershell
$env:COMPOSE_PROJECT_NAME = "pereobuyka"
docker compose -f docker-compose.yml -f docker-compose.registry.yml pull
docker compose -f docker-compose.yml -f docker-compose.registry.yml up -d --wait
docker compose exec backend python -m pereobuyka.scripts.seed
curl.exe -sf http://127.0.0.1:8000/health
```

Конкретный тег вместо `latest`:

```powershell
$env:IMAGE_TAG = "abc123def456789..."   # SHA из GitHub Actions / GHCR
make compose-registry-up
```

Или в `.env.docker`:

```
REGISTRY=ghcr.io/zharkov-ruslan
IMAGE_TAG=latest
```

### Smoke после pull

| Проверка | Ожидание |
|----------|----------|
| `make compose-ps` | postgres, backend, web **healthy**; bot running (при заданном `TELEGRAM_BOT_TOKEN`) |
| http://127.0.0.1:8000/health | `{"status":"ok"}` |
| http://127.0.0.1:3000 | страница web, 200 |

Остановка: `make compose-registry-down` (или `make compose-down` — тот же project name).

### Типовые проблемы (registry)

**pull access denied** — выполните `docker login ghcr.io` или сделайте package public в настройках GHCR.

**manifest unknown** — workflow ещё не отработал или указан неверный `IMAGE_TAG`; проверьте теги в GHCR.

**Web без API** — `NEXT_PUBLIC_API_BASE_URL` зашит при сборке образа (`http://127.0.0.1:8000`); для другого origin нужна пересборка web с другим build-arg.
