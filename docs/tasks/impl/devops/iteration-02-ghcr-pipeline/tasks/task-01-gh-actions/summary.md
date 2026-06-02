# task-01: summary

## Реализовано

- [`.github/workflows/docker-publish.yml`](../../../../../../.github/workflows/docker-publish.yml)
- Matrix job `build-and-push` для backend, bot, web
- Образы: `ghcr.io/${{ github.repository_owner }}/pereobuyka-<service>`
- Теги: `latest` (только master), полный SHA (`type=sha,format=long`)
- Buildx + GHA cache (`cache-from` / `cache-to type=gha`)
- Web собирается с `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`

## Ревью (github-actions-templates)

| Проверка | Статус |
|----------|--------|
| Pin версий actions (@v4, @v3, @v5, @v6) | ✅ |
| `permissions: packages: write` | ✅ |
| Login через `GITHUB_TOKEN`, не hardcoded secrets | ✅ |
| Matrix для нескольких образов | ✅ |
| `fail-fast: false` — один сервис не блокирует остальные | ✅ |

## Верификация

- Workflow YAML добавлен локально; полная проверка — после push в `master` или ручного `workflow_dispatch` в GitHub Actions.
