# iter-dev-02: сборка образов в GHCR

## Цель

GitHub Actions публикует образы backend, bot, web в GHCR; локально стек поднимается без `build`.

## Решения

- Workflow `.github/workflows/docker-publish.yml` — matrix из трёх сервисов, `docker/build-push-action`, GHA cache
- Имена: `ghcr.io/<owner>/pereobuyka-<service>`, теги `latest` + SHA коммита
- Триггеры: push `master`, `workflow_dispatch`
- Override `docker-compose.registry.yml` с `build: !reset null` и переменными `REGISTRY`, `IMAGE_TAG`
- Make: `compose-registry-pull`, `compose-registry-up`, `compose-registry-down`
- Документация — раздел «Запуск из GHCR» в `docs/tech/docker-compose-local.md`

## Задачи

1. gh-actions — workflow публикации
2. compose-registry — override compose + Makefile
3. registry-smoke — команды pull/run и имена образов в summary
