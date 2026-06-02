# task-02: summary

## Реализовано

- [`docker-compose.registry.yml`](../../../../../../docker-compose.registry.yml)
- Makefile: `compose-registry-pull`, `compose-registry-up`, `compose-registry-down`
- Комментарии в [`.env.docker.example`](../../../../../../.env.docker.example) про `REGISTRY` / `IMAGE_TAG`

## Верификация

```powershell
$env:COMPOSE_PROJECT_NAME = "pereobuyka"
docker compose -f docker-compose.yml -f docker-compose.registry.yml config
```

Ожидание: у backend/bot/web только `image: ghcr.io/zharkov-ruslan/pereobuyka-*:latest`, без `build`.

Проверено локально (2026-06-03): merge config OK.
