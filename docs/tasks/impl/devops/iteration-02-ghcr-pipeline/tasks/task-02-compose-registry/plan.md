# task-02: Compose для registry

## Что делаем

`docker-compose.registry.yml` — override к корневому compose:

- `build: !reset null` — убрать локальную сборку
- `image: ${REGISTRY}/pereobuyka-<service>:${IMAGE_TAG}` с defaults `ghcr.io/zharkov-ruslan` и `latest`
- postgres и остальная конфигурация наследуются из `docker-compose.yml`

Makefile:

- `compose-registry-pull`, `compose-registry-up`, `compose-registry-down`
- `COMPOSE_REGISTRY` = `-f docker-compose.yml -f docker-compose.registry.yml`
