# iter-dev-02: summary

## Реализовано

- `.github/workflows/docker-publish.yml` — matrix build/push backend, bot, web → GHCR
- `docker-compose.registry.yml` — override `image:` без локального `build`
- Makefile: `compose-registry-pull`, `compose-registry-up`, `compose-registry-down`
- Раздел «Запуск из GHCR» в [`docs/tech/docker-compose-local.md`](../../../tech/docker-compose-local.md)
- Обновлены `devops/README.md`, `.env.docker.example`

## Имена образов

```
ghcr.io/zharkov-ruslan/pereobuyka-backend
ghcr.io/zharkov-ruslan/pereobuyka-bot
ghcr.io/zharkov-ruslan/pereobuyka-web
```

Теги: `latest` (master), полный SHA коммита.

## Отклонения

- Триггер workflow на ветке **`master`** (не `main`) — фактическая default-ветка репозитория
- Smoke pull на реальных образах не выполнен агентом: образы появятся после первого run в GitHub Actions

## Верификация (агент, 2026-06-03)

- `docker compose -f docker-compose.yml -f docker-compose.registry.yml config` — backend/bot/web используют GHCR image, без build

## DoD пользователя

1. Push в `master` или **Actions → Publish Docker images → Run workflow**
2. В GHCR — три package с тегами `latest` и SHA
3. `make compose-registry-up` → health + web smoke
4. При private packages — `docker login ghcr.io`
