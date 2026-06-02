# task-01: Workflow GH Actions

## Что делаем

Файл `.github/workflows/docker-publish.yml`:

- matrix: backend, bot, web (context + dockerfile из iter-dev-01)
- `docker/login-action` → GHCR через `GITHUB_TOKEN`
- `docker/metadata-action` — теги `latest` (master) и `sha`
- `docker/build-push-action` — push, GHA cache
- web: build-arg `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
- permissions: `packages: write`

## Триггеры

- `push` → `master` (фактическая default-ветка репозитория)
- `workflow_dispatch`
