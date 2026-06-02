# task-03: summary

## Имена образов

| Сервис | Image |
|--------|-------|
| backend | `ghcr.io/zharkov-ruslan/pereobuyka-backend` |
| bot | `ghcr.io/zharkov-ruslan/pereobuyka-bot` |
| web | `ghcr.io/zharkov-ruslan/pereobuyka-web` |

Теги: `latest`, `<full-commit-sha>`.

## Команды (после успешного workflow)

```powershell
Copy-Item .env.docker.example .env.docker
# при private packages: docker login ghcr.io -u YOUR_GITHUB_USERNAME

make compose-registry-up
make compose-seed
make compose-health
# Web: http://127.0.0.1:3000
```

Конкретный SHA:

```powershell
$env:IMAGE_TAG = "<sha-from-ghcr>"
make compose-registry-up
```

## Smoke checklist

| Проверка | Команда / URL | Ожидание |
|----------|---------------|----------|
| Backend health | `make compose-health` / `:8000/health` | `{"status":"ok"}` |
| Web | http://127.0.0.1:3000 | HTTP 200 |
| Статус | `make compose-ps` | backend/web healthy |

## Документация

- [`docs/tech/docker-compose-local.md`](../../../../../tech/docker-compose-local.md) — раздел «Запуск из GHCR»

## Верификация агента

- Compose merge проверен (`docker compose config`)
- Pull/up на реальных образах — **после push workflow** (DoD пользователя)
