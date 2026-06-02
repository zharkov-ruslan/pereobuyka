# task-03: Smoke на registry

## Что делаем

- Раздел «Запуск из GHCR» в `docs/tech/docker-compose-local.md`
- Имена образов, команды pull/up, smoke (health + web)
- Типовые ошибки: login, manifest unknown, NEXT_PUBLIC_API_BASE_URL

## Ограничение

Pull из GHCR возможен только после успешного run workflow на GitHub; локально фиксируем команды и проверяем compose merge.
